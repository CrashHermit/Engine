from collections.abc import Callable

import numpy as np

ScalarFn = Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]

from src.core.field.scalar.noise import fbm

# TODO: implement voronoi and domain_warp as core scalar field modules
# from src.worldgen.scalar.voronoi import generate_graph_voronoi
# from src.worldgen.scalar.domain_warp import warp
