import unittest

import numpy as np

from streaming_lag import StreamingLagRidge


class StreamingLagTests(unittest.TestCase):
    def test_startup_and_wrap(self):
        weights = np.zeros((5, 16, 2))
        weights[:, 0, 0] = [1, 2, 4, 8, 16]
        weights[-1, 1, 1] = 1
        model = StreamingLagRidge(weights, [0, 1])
        for i in range(25):
            reading = np.zeros(16)
            reading[:2] = [i, 3 * i]
            expected = [i + 2 * max(i-1, 0) + 4 * max(i-2, 0) + 8 * max(i-5, 0) + 16 * max(i-10, 0),
                        1 + 3 * max(i-10, 0)]
            np.testing.assert_array_equal(model.update(reading), expected)

    def test_invalid_reading_does_not_advance_history(self):
        weights = np.zeros((5, 16, 2))
        weights[1, 0, 0] = 1
        model = StreamingLagRidge(weights, [0, 0])
        model.update(np.ones(16))
        with self.assertRaises(ValueError):
            model.update(np.full(16, np.nan))
        np.testing.assert_array_equal(model.update(np.full(16, 2)), [1, 0])
