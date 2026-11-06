"""Streaming inference for the Stage 2 model with ten seconds of history."""

import numpy as np


LAGS = (0, 1, 2, 5, 10)
CHANNELS = 16


class StreamingLagRidge:
    """Predict both gas levels from one 16-channel reading per second.

    Weights have shape (5 lags, 16 channels, 2 targets) and include the
    training-time scaling. Each instance represents one continuous stream.
    As in the batch model, missing history at startup repeats the first reading.
    """

    def __init__(self, weights, intercept):
        self._weights = np.array(weights, dtype=np.float64, copy=True)
        self._intercept = np.array(intercept, dtype=np.float64, copy=True)
        if self._weights.shape != (len(LAGS), CHANNELS, 2) or self._intercept.shape != (2,):
            raise ValueError('Expected weights of shape (5, 16, 2) and two intercepts')
        if not np.isfinite(self._weights).all() or not np.isfinite(self._intercept).all():
            raise ValueError('Model parameters must be finite')
        self._history = np.empty((LAGS[-1] + 1, CHANNELS), dtype=np.float64)
        self._latest = None

    @classmethod
    def load(cls, path):
        """Load a model exported by replay_streaming.py."""
        with np.load(path, allow_pickle=False) as model:
            return cls(model['weights'], model['intercept'])

    def update(self, reading):
        """Consume the next equally spaced reading and return two ppm estimates."""
        reading = np.asarray(reading, dtype=np.float64)
        if reading.shape != (CHANNELS,) or not np.isfinite(reading).all():
            raise ValueError('Expected one finite reading with 16 channels')

        if self._latest is None:
            self._history[:] = reading
            self._latest = 0
        else:
            self._latest = (self._latest + 1) % len(self._history)
            self._history[self._latest] = reading

        prediction = self._intercept.copy()
        for lag, weights in zip(LAGS, self._weights):
            position = (self._latest - lag) % len(self._history)
            prediction += self._history[position] @ weights
        return prediction
