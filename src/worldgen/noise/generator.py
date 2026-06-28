import numpy as np
import opensimplex as osn
from numba import njit, prange


class NoiseGenerator:
    """A procedural noise generator for seamless, tileable 2D torus maps."""

    def __init__(self, seed: int) -> None:
        """Initializes the noise generator with a specific seed.

        Args:
            seed (int): The seed value used to initialize the OpenSimplex
                permutation table. Ensures determinism across runs.
        """
        osn.seed(seed)

    def generate_torus_2d_hex(
        self,
        h: int,
        w: int,
        radius: float = 1.0,
        offset: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        octaves: int = 4,
        lacunarity: float = 2.0,
        persistence: float = 0.5,
    ) -> np.ndarray:
        """Generates a seamless, tileable 2D torus noise map using Fractal Brownian Motion (FBM).

        This maps a 2D grid onto a 4D Clifford torus (two independent circles, one for
        the X-axis and one for the Y-axis) to achieve seamless wrapping along both axes
        simultaneously without seams or stretching.

        Args:
            y (int): The height of the output noise map in pixels/grid units.
            x (int): The width of the output noise map in pixels/grid units.
            radius (float, optional): The base radius of the wrapping circles in
                4D space. Larger values scale the noise coordinates up, resulting in
                more detailed/higher frequency base features. Defaults to 1.0.
            offset (tuple[float, float, float, float], optional): A 4D offset used
                to shift the sampling window to a different region of the noise field.
                Useful for generating different aligned layers (e.g., elevation vs
                moisture). Defaults to (0.0, 0.0, 0.0, 0.0).
            octaves (int, optional): The number of noise detail layers to stack.
                A value of 1 generates a single-pass noise map. Defaults to 4.
            lacunarity (float, optional): The multiplier applied to the frequency
                of the coordinates with each successive octave (e.g., 2.0 doubles
                the frequency). Defaults to 2.0.
            persistence (float, optional): The multiplier applied to the amplitude
                of each successive octave (e.g., 0.5 halves the intensity/weight
                of the detail). Defaults to 0.5.

        Returns:
            np.ndarray: A 2D NumPy float array of shape (y, x) containing the
                generated seamless torus noise normalized to the range [0.0, 1.0].
        """
        # Precompute the base angular vectors
        angle_q = (np.arange(w) / w) * 2.0 * np.pi
        angle_r = (np.arange(h) / h) * 2.0 * np.pi

        noise = self._generate_torus_hex_fbm(
            angle_r,
            angle_q,
            radius,
            offset[0],
            offset[1],
            offset[2],
            offset[3],
            octaves,
            lacunarity,
            persistence,
        )

        noise_min, noise_max = noise.min(), noise.max()

        if noise_max - noise_min > 1e-6:
            return (noise - noise_min) / (noise_max - noise_min)
        else:
            return noise

    @staticmethod
    @njit(parallel=True, cache=True)
    def _generate_torus_hex_fbm(
        angle_r: np.ndarray,
        angle_q: np.ndarray,
        base_radius: float,
        ox: float,
        oy: float,
        oz: float,
        ow: float,
        octaves: int,
        lacunarity: float,
        persistence: float,
    ) -> np.ndarray:
        """Computes 4D torus coordinates element-wise using Numba optimization.

        Args:
            angle_y (np.ndarray): Precomputed angular values for the Y-axis.
            angle_x (np.ndarray): Precomputed angular values for the X-axis.
            base_radius (float): The base radius of the wrapping circles.
            ox (float): Offset for the X-axis first dimension.
            oy (float): Offset for the X-axis second dimension.
            oz (float): Offset for the Y-axis first dimension.
            ow (float): Offset for the Y-axis second dimension.
            octaves (int): The number of FBM octaves to process.
            lacunarity (float): The FBM lacunarity multiplier.
            persistence (float): The FBM persistence multiplier.

        Returns:
            np.ndarray: A 2D NumPy array of shape (len(angle_y), len(angle_x))
                containing raw noise values scaled between [-1.0, 1.0].
        """
        nr = angle_r.size
        nq = angle_q.size
        out = np.zeros((nr, nq), dtype=np.double)

        max_dim = max(nq, nr)
        radius_q = base_radius * (nq / max_dim)
        radius_r = base_radius * (nr / max_dim)

        # Precompute octave frequency and amplitude scales
        freqs = np.zeros(octaves, dtype=np.double)
        amps = np.zeros(octaves, dtype=np.double)
        total_amp = 0.0

        for i in range(octaves):
            freqs[i] = np.power(lacunarity, i)
            amps[i] = np.power(persistence, i)
            total_amp += amps[i]

        for ir in prange(nr):
            ar = angle_r[ir]
            for iq in range(nq):
                aq = angle_r[iq]

                value = 0.0
                for i in range(octaves):
                    freq = freqs[i]
                    amp = amps[i]

                    # Apply a unique spatial shift per octave to prevent
                    # artifacts where the center points of different octaves align.
                    shift = i * 1123.456

                    # Scale coordinates by frequency.
                    # Note: Periodic wrapping is still preserved because ax and ay
                    # remain bounded strictly between 0 and 2*pi.
                    cx = np.cos(aq) * (radius_q * freq) + (ox + shift) * freq
                    cy = np.sin(aq) * (radius_q * freq) + (oy + shift) * freq
                    cz = np.cos(ar) * (radius_r * freq) + (oz + shift) * freq
                    cw = np.sin(aq) * (radius_r * freq) + (ow + shift) * freq

                    value += amp * osn.noise4(cx, cy, cz, cw)

                # Normalize the sum of octaves so the result is scaled between [-1, 1]
                out[ir, radius_q] = value / total_amp

        return out
