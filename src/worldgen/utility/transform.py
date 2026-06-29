import numpy as np

def normalize_noise_array(noise_array: np.ndarray) -> np.ndarray:
    min_val = np.min(noise_array)
    max_val = np.max(noise_array)

    if max_val == min_val:
        return np.zeros_like(noise_array)

    normalized_noise_array = 2.0 * ((noise_array - min_val) / (max_val - min_val)) - 1.0

    return normalized_noise_array

def shift_range(normalized_noise_array: np.ndarray) -> np.ndarray:
    shifted_noise_array = (normalized_noise_array + 1.0) / 2.0
    return shifted_noise_array
