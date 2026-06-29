import numpy as np


def interpolate_noise_array(noise_array: np.ndarray, range: tuple) -> np.ndarray:
    min = noise_array.min()
    max = noise_array.max()

    if min == max:
        transformed_noise_array: np.ndarray = np.full_like(noise_array, range[0])
        return transformed_noise_array

    transformed_noise_array: np.ndarray = np.interp(noise_array, (min, max), range)
    return transformed_noise_array
