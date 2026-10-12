"""Power-curve and sigmoidal remapping utilities."""

import numpy as np
from scipy.special import expit


def power_curve(values: np.ndarray, exponent: float) -> np.ndarray:
    """Apply a power curve to remap values.

    Args:
        values: Input values in ``[0.0, 1.0]``, shape ``(n,)``.
        exponent: Power to raise values to.

    Returns:
        Transformed values, shape ``(n,)``.
    """
    min_val: float = float(values.min())
    max_val: float = float(values.max())

    if min_val < 0.0 or max_val > 1.0:
        raise ValueError("power_curve expects values in [0.0, 1.0]")

    return np.power(values, exponent)


def s_curve(values: np.ndarray, steepness: float) -> np.ndarray:
    """Apply a sigmoidal S-curve to remap values.

    Args:
        values: Input values in ``[0.0, 1.0]``, shape ``(n,)``.
        steepness: Steepness of the S-curve transition.

    Returns:
        Transformed values, shape ``(n,)``.
    """
    return expit((values - 0.5) * steepness)
