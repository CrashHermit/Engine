class Generator:

    def generate_3d_fbm(self, xs: np.ndarray, ys: np.ndarray, zs: np.ndarray, octaves: int, frequency: float, lacunarity: float, persistence: float) -> np.ndarray:

        elevations = np.zeros(len(xs), dtype=np.double)

        amplitude: float = 1.0
