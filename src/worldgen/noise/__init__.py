from collections.abc import Callable

import numpy as np

NoiseFn = Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]
