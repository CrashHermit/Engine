"""Grouped array aggregation helpers."""

import numpy as np


def grouped_mean(values: np.ndarray, group_ids: np.ndarray) -> np.ndarray:
    """Return the mean value for each contiguous group ID."""
    group_count = int(group_ids.max()) + 1
    sums = np.zeros((group_count,) + values.shape[1:], dtype=values.dtype)
    np.add.at(sums, group_ids, values)
    counts = np.bincount(group_ids, minlength=group_count)
    return sums / counts.reshape((group_count,) + (1,) * (values.ndim - 1))
