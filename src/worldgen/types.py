import numpy as np
from numpy.typing import NDArray

# Broad aliases — numpy operations return platform-dependent dtypes
# (intp on 64-bit, float32 on some reductions). Concrete aliases are
# kept for boundary cases where we *explicitly* cast.
type FloatArray = NDArray[np.floating]
type IntArray = NDArray[np.integer]
# Backward-compatible: widened to accept any integer/float dtype so numpy
# operations (bincount, cumsum, argpartition, flatnonzero…) satisfy the
# annotation without casts.  Explicit-cast boundaries use the concrete
# aliases below.
type Int32Array = NDArray[np.integer]   # widened from np.int32
type Float64Array = NDArray[np.floating]  # widened from np.float64
type IntPArray = NDArray[np.intp]     # explicit intp boundary
type BoolArray = NDArray[np.bool_]
type Int8Array = NDArray[np.int8]
