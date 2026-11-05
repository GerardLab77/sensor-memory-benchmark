"""Frozen chronological robustness evaluation; run `python stage2.py --download`."""
import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import subprocess
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits, threadpool_info

SOURCE = 'https://archive.ics.uci.edu/static/public/322/gas+sensor+array+under+dynamic+gas+mixtures.zip'


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def causal_indices(times, grid):
    indices = np.searchsorted(times, grid, side='right') - 1
    if np.any(indices < 0):
        raise ValueError('Grid precedes observations')
    return indices


def load_recording(archive, member, dt=1, chunk_size=100000):
    """Validate/hash the entire member and sample it with bounded memory.

    Carry the last raw row between chunks so interpolation is strictly backward.
    Grid timestamps are relative to the first raw timestamp, never row numbers.
    """
    digest = hashlib.sha256()
    sampled, grids, ages = [], [], []
    previous = None
    origin = None
    next_index = 0
    count = 0
    max_gap = 0.0
    with zipfile.ZipFile(archive) as z, z.open(member) as stream:
        header_bytes = stream.readline()
        digest.update(header_bytes)
        header = header_bytes.decode().strip()
        while True:
            lines = []
            for _ in range(chunk_size):
                line = stream.readline()
                if not line:
                    break
                digest.update(line)
                lines.append(line)
            if not lines:
                break
            raw = np.loadtxt(io.BytesIO(b''.join(lines)), ndmin=2)
            if raw.shape != (len(lines), 19) or not np.isfinite(raw).all():
                raise ValueError('Expected exactly 19 finite values on every raw row')
            if origin is None:
                origin = float(raw[0, 0])
            count += len(raw)
            if previous is not None:
                raw = np.vstack([previous, raw])
            differences = np.diff(raw[:, 0])
            if np.any(differences <= 0):
                raise ValueError('Raw timestamps must be strictly increasing')
            if len(differences):
                max_gap = max(max_gap, float(differences.max()))
            last_index = int(np.floor((raw[-1, 0] - origin) / dt))
            elapsed_grid = np.arange(next_index, last_index + 1) * dt
            grid = origin + elapsed_grid
            idx = causal_indices(raw[:, 0], grid)
            sampled.append(raw[idx])
            grids.append(elapsed_grid)
            ages.append(grid - raw[idx, 0])
            next_index = last_index + 1
            previous = raw[-1:]
    if not sampled:
        raise ValueError('Empty recording')
    values, elapsed, age = np.vstack(sampled), np.concatenate(grids), np.concatenate(ages)
    metadata = dict(member=member, member_sha256=digest.hexdigest(), header=header,
                    raw_rows=count, raw_first_timestamp_seconds=origin,
                    raw_last_timestamp_seconds=float(previous[0, 0]),
                    grid_rows=len(elapsed), grid_last_elapsed_seconds=float(elapsed[-1]),
                    max_raw_gap_seconds=max_gap, max_source_age_seconds=float(age.max()),
                    source_age_quantiles_seconds=np.quantile(age, [0, .5, .95, 1]).tolist(),
                    grid_points_source_older_than_one_interval=int(np.sum(age > dt)))
    return elapsed, values[:, 3:], values[:, 1:3], metadata


def build_features(x, name, config):
    dt = config['sample_interval_seconds']
    if name == 'current':
        return x.copy()
    if name == 'summary':
        parts = [x, np.vstack([np.zeros_like(x[:1]), np.diff(x, axis=0)])]
        for tau in config['summary_tau_seconds']:
            weight = -np.expm1(-dt / tau)
            state = x[0].copy()
            output = np.empty_like(x)
            for i, row in enumerate(x):
                state += weight * (row - state)
                output[i] = state
            parts.append(output)
        return np.column_stack(parts)
    lags = config['lag_seconds'][name]
    if any(lag / dt != int(lag / dt) for lag in lags):
        raise ValueError('Lags must be integer multiples of the interval')
    return np.column_stack([x[np.maximum(np.arange(len(x)) - int(lag / dt), 0)] for lag in lags])


def partitions(t, split, config):
    indices = {}
    for part in ('train', 'validation', 'test'):
        start, end = split[part]
        idx = np.flatnonzero((t >= start) & (t < end))
        if len(idx) != (end - start) / config['sample_interval_seconds']:
            raise ValueError(f'Recording does not cover {part}: {start}, {end}')
        indices[part] = idx
    if split['train'][0] < config['warmup_seconds']:
        raise ValueError('Insufficient warm-up')
    for first, second in [('train', 'validation'), ('validation', 'test')]:
        if split[second][0] - split[first][1] < config['gap_seconds']:
            raise ValueError('Insufficient split gap')
    return indices


def select_model(features, target, train, validation, alphas):
    """No test arguments: only training can fit state, only validation selects alpha."""
    scaler = StandardScaler().fit(features[train])
    xtrain, xval = scaler.transform(features[train]), scaler.transform(features[validation])
    best = None
    candidates = []
    for alpha in alphas:
        model = Ridge(alpha=alpha, solver='cholesky').fit(xtrain, target[train])
        score = float(np.mean(np.abs(target[validation] - model.predict(xval))))
        candidates.append({'alpha': alpha, 'validation_mae_ppm': score})
        if best is None or score < best[0]:
            best = score, alpha, model
    return scaler, best[2], best[1], candidates


def paired_change(error, baseline):
    delta = float(error - baseline)
    return delta, (100 * delta / baseline if baseline != 0 else None), ('defined' if baseline != 0 else 'zero_baseline')


def distribution(y):
    return dict(n=len(y), min=float(y.min()), max=float(y.max()), mean=float(y.mean()),
                std=float(y.std()), q05=float(np.quantile(y, .05)),
                median=float(np.median(y)), q95=float(np.quantile(y, .95)),
                unique_values=len(np.unique(y)))


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plots(out, results, config):
    names = ['summary', *config['lag_seconds']]
    for metric in ('mae', 'rmse'):
        fig, axes = plt.subplots(2, 2, figsize=(11, 6), layout='constrained')
        for row, (member, gases) in enumerate(config['recordings'].items()):
            for col, gas in enumerate(gases):
                ax = axes[row, col]
                for fold, marker in zip((1, 2, 3), ('o', 's', '^')):
                    subset = {r['model']: r for r in results if r['recording'] == member and r['gas'] == gas and r['fold'] == fold}
                    changes = [subset[name][f'{metric}_percent_change'] for name in names]
                    ax.plot(np.arange(4), [np.nan if v is None else v for v in changes], marker=marker, label=f'Fold {fold}', lw=1)
                ax.axhline(0, color='black', lw=.8)
                ax.set_xticks(np.arange(4), ['Summary', '10 s lags', '30 s lags', '120 s lags'])
                ax.set_title(f'{member.removesuffix(".txt")} / {gas}')
                ax.set_ylabel(f'{metric.upper()} change vs current (%)')
                ax.legend(fontsize=8)
        fig.suptitle('Negative = lower error; folds are dependent chronological periods')
        fig.savefig(out / f'comparison_{metric}.png', dpi=150)
        plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 6), layout='constrained')
    for row, (member, gases) in enumerate(config['recordings'].items()):
        data = np.load(out / f'{Path(member).stem}_fold{config["prediction_plot"]["fold"]}.npz')
        keep = data['time'] < data['time'][0] + config['prediction_plot']['first_seconds']
        for col, gas in enumerate(gases):
            ax = axes[row, col]
            for name in ['target', 'current', 'summary', *config['lag_seconds']]:
                ax.plot(data['time'][keep] / 60, data[name][keep, col], label=name,
                        lw=1.3 if name == 'target' else .8, alpha=1 if name == 'target' else .75)
            ax.set_title(f'{Path(member).stem} / {gas}')
            ax.set_ylabel('Concentration set point (ppm)')
            ax.set_xlabel('Elapsed minutes')
    axes[0, 0].legend(fontsize=7, ncol=2)
    fig.suptitle('Predetermined view: first 600 seconds of fold 2 test')
    fig.savefig(out / 'predictions.png', dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, default=Path('data/uci322.zip'))
    parser.add_argument('--config', type=Path, default=Path('stage2_config.json'))
    parser.add_argument('--out', type=Path, default=Path('results/stage2'))
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output exists; choose a new --out to preserve completed runs')
    if not args.zip.exists():
        if not args.download:
            parser.error('Missing archive; use --download')
        args.zip.parent.mkdir(parents=True, exist_ok=True)
        partial = args.zip.with_suffix('.zip.partial')
        urllib.request.urlretrieve(SOURCE, partial)
        with zipfile.ZipFile(partial) as archive:
            if archive.testzip() is not None:
                raise ValueError('Corrupt download')
        partial.replace(args.zip)
    config = json.loads(args.config.read_text())
    args.out.mkdir(parents=True)
    write_json(args.out / 'config.json', config)
    environment = dict(python=sys.version, platform=platform.platform(),
                       packages={d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
                       git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                       git_status=subprocess.check_output(['git', 'status', '--porcelain'], text=True),
                       source_sha256=sha256(__file__), config_sha256=sha256(args.config),
                       archive_sha256=sha256(args.zip), source_url=SOURCE,
                       started_utc=datetime.now(timezone.utc).isoformat(), command=sys.argv,
                       thread_limit=1)
    write_json(args.out / 'environment.json', environment)
    # Check coverage/variation of both recordings before any model fitting.
    loaded, checks, summaries, boundaries = {}, {}, [], []
    for member, gases in config['recordings'].items():
        print(f'Loading and validating {member}', flush=True)
        t, x, y, metadata = load_recording(args.zip, member, config['sample_interval_seconds'])
        loaded[member] = t, x, y
        checks[member] = metadata
        previous_test_end = -np.inf
        for split in config['splits']:
            idx = partitions(t, split, config)
            if split['test'][0] < previous_test_end:
                raise ValueError('Overlapping test periods')
            previous_test_end = split['test'][1]
            for part, indices in idx.items():
                boundaries.append(dict(recording=member, fold=split['fold'], partition=part,
                                       start_elapsed_seconds=split[part][0], end_exclusive_elapsed_seconds=split[part][1],
                                       first_elapsed_seconds=float(t[indices[0]]), last_elapsed_seconds=float(t[indices[-1]]),
                                       first_raw_clock_seconds=float(t[indices[0]] + metadata['raw_first_timestamp_seconds']),
                                       last_raw_clock_seconds=float(t[indices[-1]] + metadata['raw_first_timestamp_seconds']), n=len(indices)))
                for j, gas in enumerate(gases):
                    stats = distribution(y[indices, j])
                    if stats['unique_values'] < 2:
                        raise ValueError(f'Constant target in {member}/{part}/{gas}')
                    summaries.append(dict(recording=member, fold=split['fold'], partition=part, gas=gas, **stats))
        print(json.dumps(metadata), flush=True)
    write_json(args.out / 'data_checks.json', checks)
    write_csv(args.out / 'distributions.csv', summaries)
    write_csv(args.out / 'split_boundaries.csv', boundaries)
    records, selection = [], []
    with threadpool_limits(limits=1):
        environment['threadpools'] = threadpool_info()
        for member, gases in config['recordings'].items():
            t, x, y = loaded[member]
            feature_sets = {name: build_features(x, name, config) for name in ['current', 'summary', *config['lag_seconds']]}
            for split in config['splits']:
                idx = partitions(t, split, config)
                test = idx['test']
                predictions = dict(time=t[test], target=y[test])
                baseline = {}
                for name, features in feature_sets.items():
                    pred = np.empty_like(y[test])
                    for j, gas in enumerate(gases):
                        scaler, model, alpha, candidates = select_model(features, y[:, j], idx['train'], idx['validation'], config['alphas'])
                        pred[:, j] = model.predict(scaler.transform(features[test]))
                        selection.append(dict(recording=member, fold=split['fold'], model=name, gas=gas, selected_alpha=alpha, candidates=candidates))
                        error = pred[:, j] - y[test, j]
                        record = dict(recording=member, fold=split['fold'], gas=gas, model=name,
                                      features=features.shape[1], alpha=alpha, n_test=len(test),
                                      mae_ppm=float(np.mean(np.abs(error))), rmse_ppm=float(np.sqrt(np.mean(error ** 2))))
                        if name == 'current':
                            baseline[gas] = record.copy()
                        for metric in ('mae', 'rmse'):
                            base = baseline[gas][f'{metric}_ppm']
                            delta, percent, status = paired_change(record[f'{metric}_ppm'], base)
                            record.update({f'current_{metric}_ppm': base, f'{metric}_delta_ppm': delta,
                                           f'{metric}_percent_change': percent, f'{metric}_percent_status': status})
                        records.append(record)
                    predictions[name] = pred
                np.savez_compressed(args.out / f'{Path(member).stem}_fold{split["fold"]}.npz', **predictions)
                print(f'Completed {member} fold {split["fold"]}', flush=True)
    write_csv(args.out / 'metrics.csv', records)
    write_json(args.out / 'metrics.json', records)
    write_json(args.out / 'validation_selection.json', selection)
    plots(args.out, records, config)
    environment['completed_utc'] = datetime.now(timezone.utc).isoformat()
    write_json(args.out / 'environment.json', environment)
    print(f'Completed: {args.out}', flush=True)


if __name__ == '__main__':
    main()
