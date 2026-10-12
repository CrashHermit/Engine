import numpy as np


def grouped_mean(values: np.ndarray, group_ids: np.ndarray) -> np.ndarray:
    n_groups: int = int(group_ids.max()) + 1
    sums_shape: tuple[int, ...] = (n_groups,) + values.shape[1:]
    sums = np.zeros(sums_shape, dtype=values.dtype)
    np.add.at(sums, group_ids, values)
    counts = np.bincount(group_ids, minlength=n_groups)

    broadcast_shape: tuple[int, ...] = (n_groups,) + (1,) * (values.ndim - 1)

    reshape = sums / counts.reshape(broadcast_shape)

    return reshape
