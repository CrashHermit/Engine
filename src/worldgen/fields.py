from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field, fields

from src.worldgen.types import BoolArray, Float64Array


@dataclass
class MeshFields:
    elevation: Float64Array | None = field(default=None, metadata={"dtype": np.float64})
    is_land: BoolArray | None = field(default=None, metadata={"dtype": bool})

    @classmethod
    def allocate(cls, n: int) -> MeshFields:
        """Create zeroed per-cell field arrays of length n."""
        return cls(**{
            f.name: np.zeros(n, dtype=f.metadata["dtype"])
            for f in fields(class_or_instance=cls)
        })
