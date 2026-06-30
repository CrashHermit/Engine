import numpy as np

from src.worldgen.scalar import ScalarFn


def warp(
    noise_fn: ScalarFn,
    xs: np.ndarray,
    ys: np.ndarray,
    zs: np.ndarray,
    warp_strength: float,
    warp_noise: ScalarFn,
) -> np.ndarray:
    pass
