import numpy as np
from numpy.typing import NDArray

# --- Concrete storage/contract aliases ---
# These match the FIELD_SCHEMA dtypes exactly and type the Fields container and
# every field a stage reads/writes.  The product honours these dtypes (the bake
# coerces to them), so they are an honest contract, not an aspiration.
type Float64Array = NDArray[np.float64]
type Int32Array = NDArray[np.int32]
type Int8Array = NDArray[np.int8]
type BoolArray = NDArray[np.bool_]

# --- Broad internal aliases ---
# numpy widens dtypes in reductions and mixed ops (intp on 64-bit, float64 from
# integer division, ...).  Use these for algorithm intermediates where fighting
# numpy's widening adds only casts; coerce back to a concrete alias when writing
# a result into a Fields slot.
type FloatArray = NDArray[np.floating]
type IntArray = NDArray[np.integer]
type IntPArray = NDArray[np.intp]
