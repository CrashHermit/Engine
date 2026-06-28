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

    def generate_torus_2d_surface(
        self,
        y: int,
        x: int,
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
        angle_x = (np.arange(x) / x) * 2.0 * np.pi
        angle_y = (np.arange(y) / y) * 2.0 * np.pi
        
        noise = self._generate_torus_grid_fbm(
            angle_y, angle_x, radius,
            offset[0], offset[1], offset[2], offset[3],
            octaves, lacunarity, persistence
        )
        
        # Normalize final noise back to [0.0, 1.0]
        return (noise + 1.0) / 2.0

    @staticmethod
    @njit(parallel=True, cache=True)
    def _generate_torus_grid_fbm(
        angle_y: np.ndarray,
        angle_x: np.ndarray,
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
        ny = angle_y.size
        nx = angle_x.size
        out = np.zeros((ny, nx), dtype=np.double)
        
        # Precompute octave frequency and amplitude scales
        freqs = np.zeros(octaves, dtype=np.double)
        amps = np.zeros(octaves, dtype=np.double)
        total_amp = 0.0
        
        for i in range(octaves):
            freqs[i] = lacunarity ** i
            amps[i] = persistence ** i
            total_amp += amps[i]
            
        for iy in prange(ny):
            ay = angle_y[iy]
            for ix in range(nx):
                ax = angle_x[ix]
                
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
                    cx = np.cos(ax) * (base_radius * freq) + (ox + shift) * freq
                    cy = np.sin(ax) * (base_radius * freq) + (oy + shift) * freq
                    cz = np.cos(ay) * (base_radius * freq) + (oz + shift) * freq
                    cw = np.sin(ay) * (base_radius * freq) + (ow + shift) * freq
                    
                    value += amp * osn.noise4(cx, cy, cz, cw)
                    
                # Normalize the sum of octaves so the result is scaled between [-1, 1]
                out[iy, ix] = value / total_amp
                
        return out
