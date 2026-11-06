"""Refit the original Stage 2 models and check their streaming predictions."""

import argparse
import json
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from stage2 import build_features, load_recording, partitions, select_model
from streaming_lag import CHANNELS, LAGS, StreamingLagRidge


TOLERANCE_PPM = 1e-8


def verify(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=TOLERANCE_PPM, rtol=0)
    return float(np.max(np.abs(actual - expected)))


def replay(config, archive, saved_dir, out):
    if config['sample_interval_seconds'] != 1 or tuple(config['lag_seconds']['lags_10s']) != LAGS:
        raise ValueError('The streaming model expects the Stage 2 lags at one reading per second')
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for member, gases in config['recordings'].items():
        t, x, y, _ = load_recording(archive, member)
        features = build_features(x, 'lags_10s', config)
        for split in config['splits']:
            idx = partitions(t, split, config)
            test = idx['test']
            batch = np.empty_like(y[test])
            weights = np.empty((len(LAGS), CHANNELS, len(gases)))
            intercept = np.empty(len(gases))
            alphas = []
            for j in range(len(gases)):
                scaler, model, alpha, _ = select_model(features, y[:, j], idx['train'],
                                                       idx['validation'], config['alphas'])
                batch[:, j] = model.predict(scaler.transform(features[test]))
                coefficients = model.coef_ / scaler.scale_
                weights[:, :, j] = coefficients.reshape(len(LAGS), CHANNELS)
                intercept[j] = model.intercept_ - scaler.mean_ @ coefficients
                alphas.append(alpha)

            name = f'{Path(member).stem}_fold{split["fold"]}'
            model_path = out / f'{name}_streaming.npz'
            np.savez_compressed(model_path, weights=weights, intercept=intercept, targets=np.array(gases))
            model = StreamingLagRidge.load(model_path)
            # Prime the buffer with the same preceding inputs the batch model saw.
            for reading in x[test[0] - LAGS[-1]:test[0]]:
                model.update(reading)
            streamed = np.stack([model.update(x[i]) for i in test])
            with np.load(saved_dir / f'{name}.npz', allow_pickle=False) as saved:
                np.testing.assert_array_equal(t[test], saved['time'])
                np.testing.assert_array_equal(y[test], saved['target'])
                row = dict(period=name, readings=len(test), targets=gases, alpha=alphas,
                           refit_vs_saved_max_ppm=verify(batch, saved['lags_10s']),
                           stream_vs_refit_max_ppm=verify(streamed, batch),
                           stream_vs_saved_max_ppm=verify(streamed, saved['lags_10s']))
            results.append(row)
            print(f'{name}: {len(test):,} readings, max streaming difference '
                  f'{row["stream_vs_saved_max_ppm"]:.3g} ppm', flush=True)

    report = dict(passed=True, tolerance_ppm=TOLERANCE_PPM, periods=results,
                  total_readings=sum(row['readings'] for row in results),
                  total_estimates=sum(row['readings'] * len(row['targets']) for row in results),
                  max_stream_vs_saved_ppm=max(row['stream_vs_saved_max_ppm'] for row in results))
    (out / 'replay_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('stage2_config.json'))
    parser.add_argument('--zip', type=Path, default=Path('data/uci322.zip'))
    parser.add_argument('--saved', type=Path, default=Path('results/stage2'))
    parser.add_argument('--out', type=Path, required=True, help='New directory for models and replay results')
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        replay(json.loads(args.config.read_text()), args.zip, args.saved, args.out)


if __name__ == '__main__':
    main()
