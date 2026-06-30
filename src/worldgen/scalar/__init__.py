from collections.abc import Callable

import numpy as np

ScalarFn = Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]

from src.worldgen.scalar.noise import fbm
from src.worldgen.scalar.voronoi import generate_graph_voronoi
from src.worldgen.scalar.domain_warp import warp
