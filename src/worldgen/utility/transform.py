import numpy as np
from scipy.special import expit


def interpolate_noise_array(noise_array: np.ndarray, range: tuple) -> np.ndarray:
    min = noise_array.min()
    max = noise_array.max()

    if min == max:
        transformed_noise_array: np.ndarray = np.full_like(noise_array, range[0])
        return transformed_noise_array

    transformed_noise_array: np.ndarray = np.interp(noise_array, (min, max), range)
    return transformed_noise_array

def power_curve_noise_array(noise_array: np.ndarray, expontent: float) -> np.ndarray:
    min = noise_array.min()
    max = noise_array.max()

    if min < 0.0 or max > 1.0:
        raise ValueError("power_curve_noise_array expects values in [0.0, 1.0]")

    transformed_noise_array: np.ndarray = np.power(noise_array, expontent)
    return transformed_noise_array

def s_curve_noise_array(noise_array: np.ndarray, steepness: float) -> np.ndarray:
    transformed_noise_array: np.ndarray = expit((noise_array - 0.5) * steepness)
    return transformed_noise_array
