"""Controls for leakage, timestamp alignment, state and reporting semantics."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np

from stage2 import (build_features, causal_indices, load_recording, paired_change,
                    partitions, select_model)

CONFIG = json.loads(Path(__file__).with_name('stage2_config.json').read_text())


class Stage2Controls(unittest.TestCase):
    def test_causal_resampling_and_chunk_boundaries(self):
        times = np.array([.1, .3, 1.09, 1.11, 2.2, 4.2])
        rows = np.column_stack([times, np.arange(6)[:, None] + np.arange(18)[None, :]])
        content = 'header\n' + '\n'.join(' '.join(map(str, row)) for row in rows) + '\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.zip'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('test.txt', content)
            for size in (1, 2, 4, 100):
                t, x, y, checks = load_recording(path, 'test.txt', chunk_size=size)
                np.testing.assert_array_equal(t, [0, 1, 2, 3, 4])
                np.testing.assert_array_equal(y[:, 0], [0, 2, 3, 4, 4])
                np.testing.assert_array_equal(x[:, 0], y[:, 0] + 2)
                self.assertEqual(checks['member_sha256'], hashlib.sha256(content.encode()).hexdigest())
                self.assertEqual(checks['raw_rows'], 6)
                self.assertAlmostEqual(checks['max_raw_gap_seconds'], 2)
        with self.assertRaises(ValueError):
            causal_indices([1, 2], [0])

    def test_reject_invalid_unsampled_rows(self):
        for bad in ('0.2 ' + 'nan ' * 18, '0.1 ' + '1 ' * 18, '0.2 1 2'):
            text = 'header\n' + '0.1 ' + '1 ' * 18 + '\n' + bad + '\n'
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'bad.zip'
                with zipfile.ZipFile(path, 'w') as z:
                    z.writestr('bad.txt', text)
                with self.assertRaises(ValueError):
                    load_recording(path, 'bad.txt', chunk_size=1)

    def test_future_perturbation_and_sparse_lag_alignment(self):
        x = np.arange(800., dtype=float)[:, None]
        changed = x.copy()
        changed[650:] = -9999
        for name in ('current', 'summary', *CONFIG['lag_seconds']):
            original = build_features(x, name, CONFIG)
            np.testing.assert_array_equal(original[:650], build_features(changed, name, CONFIG)[:650])
            if name in CONFIG['lag_seconds']:
                np.testing.assert_array_equal(original[600], 600 - np.array(CONFIG['lag_seconds'][name]))

    def test_ewma_seconds_and_continuous_boundary_state(self):
        x = np.ones((700, 1))
        x[0] = 0
        summary = build_features(x, 'summary', CONFIG)
        for j, tau in enumerate(CONFIG['summary_tau_seconds']):
            self.assertAlmostEqual(summary[600, j + 2], 1 - np.exp(-600 / tau))
        # A partition must slice the stream, not reinitialize the summaries at 600.
        self.assertNotEqual(summary[600, -1], build_features(x[600:], 'summary', CONFIG)[0, -1])

    def test_fixed_split_coverage_gaps_and_test_nonoverlap(self):
        t = np.arange(42000.)
        tests = []
        for split in CONFIG['splits']:
            parts = partitions(t, split, CONFIG)
            self.assertEqual(len(parts['test']), 6000)
            self.assertEqual(parts['train'][0], 600)
            self.assertEqual(parts['validation'][0] - parts['train'][-1], 601)
            self.assertEqual(parts['test'][0] - parts['validation'][-1], 601)
            tests.extend(parts['test'])
        self.assertEqual(len(tests), len(set(tests)))
        with self.assertRaises(ValueError):
            partitions(np.arange(40000), CONFIG['splits'][-1], CONFIG)

    def test_train_only_scaling_and_validation_only_selection(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=(100, 4))
        y = x[:, 0] * 3 + rng.normal(size=100)
        tr, va = np.arange(60), np.arange(60, 80)
        first = select_model(x, y, tr, va, CONFIG['alphas'])
        np.testing.assert_allclose(first[0].mean_, x[tr].mean(axis=0))
        for candidate in first[3]:
            self.assertTrue(np.isfinite(candidate['validation_mae_ppm']))
        self.assertEqual(first[2], min(first[3], key=lambda r: r['validation_mae_ppm'])['alpha'])
        changed_x, changed_y = x.copy(), y.copy()
        changed_x[80:] += 1e6
        changed_y[80:] -= 1e6
        second = select_model(changed_x, changed_y, tr, va, CONFIG['alphas'])
        self.assertEqual(first[2:], second[2:])
        np.testing.assert_array_equal(first[1].coef_, second[1].coef_)
        np.testing.assert_array_equal(first[0].mean_, second[0].mean_)

    def test_percent_zero_baseline_and_sign(self):
        self.assertEqual(paired_change(8, 10), (-2, -20, 'defined'))
        self.assertEqual(paired_change(0, 0), (0, None, 'zero_baseline'))
        self.assertEqual(paired_change(2, 0), (2, None, 'zero_baseline'))


if __name__ == '__main__':
    unittest.main()
