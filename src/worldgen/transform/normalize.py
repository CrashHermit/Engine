import numpy as np


def interpolate_noise_array(noise_array: np.ndarray, domain: tuple) -> np.ndarray:
    min: float = noise_array.min()
    max: float = noise_array.max()

    if min == max:
        transformed_noise_array: np.ndarray = np.full_like(noise_array, domain[0])
        return transformed_noise_array

    transformed_noise_array: np.ndarray = np.interp(noise_array, (min, max), domain)
    return transformed_noise_array
