from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import Ridge
from sklearn.utils.validation import check_array, check_is_fitted


class TrainingRangeClipper(TransformerMixin, BaseEstimator):
    """Clip each feature to the finite range observed while fitting.

    Readability targets lie in [0, 1]. A linear model should therefore not make
    unbounded extrapolations merely because a new snippet is longer or denser
    than every training example. Training rows are unchanged by this transform.
    """

    def fit(self, x, y=None):
        values = check_array(x, dtype=float, ensure_all_finite=True)
        self.feature_min_ = np.min(values, axis=0)
        self.feature_max_ = np.max(values, axis=0)
        self.n_features_in_ = values.shape[1]
        return self

    def transform(self, x):
        check_is_fitted(self, ("feature_min_", "feature_max_"))
        values = check_array(x, dtype=float, ensure_all_finite=True)
        return np.clip(values, self.feature_min_, self.feature_max_)


class BoundedRidge(Ridge):
    """Ridge whose readability predictions respect the target's [0, 1] scale."""

    def predict(self, x):
        return np.clip(super().predict(x), 0.0, 1.0)
