import numpy as np

from src.worldgen.noise import NoiseFn


def warp(
    noise_fn: NoiseFn,
    xs: np.ndarray,
    ys: np.ndarray,
    zs: np.ndarray,
    warp_strength: float,
    warp_noise: NoiseFn,
) -> np.ndarray:
    pass
