"""Build desktop C++ inference and compare it with the saved Python models."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
from threadpoolctl import threadpool_limits

# Picked these limits before running the comparison. Errors are in ppm.
DOUBLE_ATOL = 1e-8
FLOAT_ATOL = 0.01
MAE_RELATIVE_LIMIT = 0.001  # 0.1% change in each gas/period MAE.
ORDERED_FLOAT_ATOL = 1e-6
ROOT = Path(__file__).resolve().parent


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(command, **kwargs):
    return subprocess.run([str(x) for x in command], check=True, **kwargs)


def ordered_float_reference(features, weights, bias):
    """Independent batch features, with the same float32 operation order as C++."""
    inputs = features.astype(np.float32)
    coefficients = weights.astype(np.float32)
    result = np.broadcast_to(bias.astype(np.float32), (len(inputs), 2)).copy()
    for column in range(inputs.shape[1]):
        result += inputs[:, column, None] * coefficients[column]
    return result


def build(compiler, out):
    flags = ["-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
             "-ffp-contract=off", "-fno-fast-math"]
    extension = ".exe" if os.name == "nt" else ""
    executables, commands = {}, []
    for precision in ("float32", "float64"):
        defines = ["-DSENSOR_DOUBLE"] if precision == "float64" else []
        for source, label in (("test_sensor_model.cpp", "test"), ("replay.cpp", "replay")):
            target = out / (label + "_" + precision + extension)
            command = [*compiler, *flags, *defines, ROOT / "cpp" / source, "-o", target]
            commands.append([str(x) for x in command])
            run(command)
            if label == "test":
                run([target])
            else:
                executables[precision] = target
        print(f"Built and passed C++ state tests: {precision}", flush=True)
    return executables, commands


def check(args):
    # Lazy import so --help and argument checks don't initialise plotting.
    from stage2 import build_features, load_recording, partitions, select_model

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    config = json.loads(args.config.read_text())
    if config["sample_interval_seconds"] != 1 or config["lag_seconds"]["lags_10s"] != [0, 1, 2, 5, 10]:
        raise ValueError("C++ implementation expects the Stage 2 1 Hz lag configuration")
    version = run([*args.compiler, "--version"], capture_output=True, text=True).stdout
    executables, commands = build(args.compiler, out)
    report = dict(
        passed=False, python=sys.version, numpy=np.__version__, platform=platform.platform(),
        compiler_version=version, build_commands=commands,
        git_head=run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        git_status=run(["git", "-C", ROOT, "status", "--porcelain"], capture_output=True, text=True).stdout,
        sources={name: digest(ROOT / name) for name in
                 ("check_cpp.py", "cpp/sensor_model.hpp", "cpp/replay.cpp",
                  "cpp/test_sensor_model.cpp", "stage2.py")},
        config_sha256=digest(args.config), archive_sha256=digest(args.zip),
        tolerances=dict(double_atol_ppm=DOUBLE_ATOL, float_atol_ppm=FLOAT_ATOL,
                        mae_relative_change_limit=MAE_RELATIVE_LIMIT,
                        ordered_float_atol_ppm=ORDERED_FLOAT_ATOL),
        cpp_state_tests="passed for float32 and float64: startup, wraparound, reset, invalid readings",
        models=[], failures=[],
    )
    for member, gases in config["recordings"].items():
        print(f"Reading {member}", flush=True)
        time, x, y, _ = load_recording(args.zip, member)
        for name in ("current", "lags_10s"):
            features = build_features(x, name, config)
            for split in config["splits"]:
                indices = partitions(time, split, config)
                test = indices["test"]
                # Give the buffer ten readings before we start scoring.
                readings = x[test[0] - 10:test[-1] + 1]
                local_features = build_features(readings, name, config)
                weights = np.empty((features.shape[1], 2))
                bias = np.empty(2)
                batch = np.empty_like(y[test])
                alphas = []
                for gas in range(2):
                    scaler, model, alpha, _ = select_model(
                        features, y[:, gas], indices["train"], indices["validation"], config["alphas"])
                    weights[:, gas] = model.coef_ / scaler.scale_
                    bias[gas] = model.intercept_ - scaler.mean_ @ weights[:, gas]
                    batch[:, gas] = model.predict(scaler.transform(features[test]))
                    alphas.append(alpha)
                period = f"{Path(member).stem}_fold{split['fold']}"
                saved_path = args.saved / (period + ".npz")
                with np.load(saved_path, allow_pickle=False) as saved:
                    np.testing.assert_array_equal(time[test], saved["time"])
                    np.testing.assert_array_equal(y[test], saved["target"])
                    expected = saved[name].copy()
                np.testing.assert_allclose(batch, expected, atol=DOUBLE_ATOL, rtol=0)
                folder = out / f"{period}_{name}"
                folder.mkdir()
                np.savetxt(folder / "model.txt", np.r_[weights.ravel(), bias], fmt="%.17g")
                np.savetxt(folder / "inputs.txt", readings, fmt="%.17g",
                           header=str(len(readings)), comments="")
                np.savez_compressed(folder / "parameters.npz", weights=weights, bias=bias,
                                    targets=np.array(gases))
                predictions = {}
                for precision, executable in executables.items():
                    prediction_file = folder / (precision + ".txt")
                    run([executable, name, folder / "model.txt", folder / "inputs.txt", prediction_file])
                    values = np.loadtxt(prediction_file, ndmin=2)
                    if values.shape != (len(readings), 2) or not np.isfinite(values).all():
                        raise ValueError("Invalid C++ output")
                    predictions[precision] = values
                ordered = ordered_float_reference(local_features, weights, bias)
                folded = local_features @ weights + bias
                double_max = float(np.max(np.abs(predictions["float64"][10:] - expected)))
                startup_double_max = float(np.max(np.abs(predictions["float64"] - folded)))
                ordered_max = float(np.max(np.abs(predictions["float32"] - ordered)))
                row = dict(period=period, model=name, targets=gases, alpha=alphas,
                           test_updates=len(test), priming_updates=10,
                           saved_predictions_sha256=digest(saved_path),
                           refit_vs_saved_max_ppm=float(np.max(np.abs(batch - expected))),
                           double_vs_saved_max_ppm=double_max,
                           double_vs_folded_all_updates_max_ppm=startup_double_max,
                           float_vs_ordered_python_all_updates_max_ppm=ordered_max,
                           gas_metrics=[])
                if max(double_max, startup_double_max) > DOUBLE_ATOL:
                    report["failures"].append(f"{period}/{name}: double mismatch")
                if ordered_max > ORDERED_FLOAT_ATOL:
                    report["failures"].append(f"{period}/{name}: float operation-order mismatch")
                for gas, label in enumerate(gases):
                    cpp = predictions["float32"][10:, gas]
                    original_error = expected[:, gas] - y[test, gas]
                    cpp_error = cpp - y[test, gas]
                    python_mae = float(np.mean(np.abs(original_error)))
                    cpp_mae = float(np.mean(np.abs(cpp_error)))
                    mae_delta = cpp_mae - python_mae
                    relative_change = abs(mae_delta) / python_mae if python_mae else None
                    maximum = float(np.max(np.abs(cpp - expected[:, gas])))
                    mae_passed = (abs(mae_delta) <= python_mae * MAE_RELATIVE_LIMIT
                                  if python_mae else cpp_mae == 0)
                    row["gas_metrics"].append(dict(
                        gas=label, float_vs_saved_max_ppm=maximum,
                        python_mae_ppm=python_mae, cpp_mae_ppm=cpp_mae,
                        mae_delta_ppm=mae_delta, absolute_relative_mae_change=relative_change,
                        python_rmse_ppm=float(np.sqrt(np.mean(original_error ** 2))),
                        cpp_rmse_ppm=float(np.sqrt(np.mean(cpp_error ** 2))),
                        passed=maximum <= FLOAT_ATOL and mae_passed))
                    if not row["gas_metrics"][-1]["passed"]:
                        report["failures"].append(f"{period}/{name}/{label}: float accuracy limit")
                np.savez_compressed(folder / "comparison.npz", time=time[test], target=y[test],
                                    python=expected, cpp_float32=predictions["float32"][10:],
                                    cpp_float64=predictions["float64"][10:])
                report["models"].append(row)
                print(f"{period}/{name}: max float error "
                      f"{max(g['float_vs_saved_max_ppm'] for g in row['gas_metrics']):.6g} ppm", flush=True)
    report["total_test_updates"] = sum(r["test_updates"] for r in report["models"])
    report["total_test_estimates"] = report["total_test_updates"] * 2
    report["passed"] = not report["failures"]
    (out / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise RuntimeError(f"Comparison failed: see {out / 'report.json'}")
    print(f"PASS: {report['total_test_estimates']:,} estimates per precision; {out / 'report.json'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", nargs="+", default=["c++"],
                        help="GCC/Clang driver, or path/to/zig c++")
    parser.add_argument("--out", type=Path, required=True, help="New directory for builds and comparisons")
    parser.add_argument("--zip", type=Path, default=ROOT / "data/uci322.zip")
    parser.add_argument("--config", type=Path, default=ROOT / "stage2_config.json")
    parser.add_argument("--saved", type=Path, default=ROOT / "results/stage2")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a new directory")
    with threadpool_limits(limits=1):
        check(args)


if __name__ == "__main__":
    main()
