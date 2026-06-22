from dataclasses import dataclass, field, fields
from typing import Self

import numpy as np

from src.worldgen.types import BoolArray, Float64Array, Int32Array, Int8Array


@dataclass
class MeshFields:
    elevation: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Normalized height in [-1, 1]; 0 = sea level
    is_land: BoolArray | None = field(
        default=None, metadata={"dtype": bool}
    )  # True when elevation is at or above sea level
    plate_id: Int32Array | None = field(
        default=None, metadata={"dtype": np.int32}
    )  # Which plate owns the cell
    uplift: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Tectonic push-up rate
    z_route: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Water-routing elevation (separate from terrain)
    receiver: Int32Array | None = field(
        default=None, metadata={"dtype": np.int32}
    )  # Downstream cell id; -1 = base level
    drainage: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Upstream area (river size)
    slope: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Steepest descent
    coast_distance: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Hops from coast
    landmass_id: Int32Array | None = field(
        default=None, metadata={"dtype": np.int32}
    )  # Connected land component id
    landmass_class: Int8Array | None = field(
        default=None, metadata={"dtype": np.int8}
    )  # 0 = ocean, 1 = island, 2 = landmass, 3 = major
    insolation: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # [0,1] authored energy field; 1 = sunband (mesh-side intermediate)
    temperature: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # [0,1] warmth; 1 = sunband
    precipitation: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # [0,1] rainfall
    wind_u: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # unit wind direction x
    wind_v: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # unit wind direction y
    wind_magnitude: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # [0,1] wind speed

    @classmethod
    def allocate(cls, n: int) -> Self:
        """Create zeroed per-cell field arrays of length n."""
        return cls(
            **{
                f.name: np.zeros(n, dtype=f.metadata["dtype"])
                for f in fields(class_or_instance=cls)
            }
        )


@dataclass
class GridFields:
    elevation: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Normalized height in [-1, 1]; 0 = sea level
    is_land: BoolArray | None = field(
        default=None, metadata={"dtype": bool}
    )  # True when elevation is at or above sea level
    plate_id: Int32Array | None = field(
        default=None, metadata={"dtype": np.int32}
    )  # Which plate owns the cell
    uplift: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Tectonic push-up rate
    z_route: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Water-routing elevation (separate from terrain)
    receiver: Int32Array | None = field(
        default=None, metadata={"dtype": np.int32}
    )  # Downstream cell id; -1 = base level
    drainage: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Upstream area (river size)
    slope: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Steepest descent
    coast_distance: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # Hops from coast
    landmass_id: Int32Array | None = field(
        default=None, metadata={"dtype": np.int32}
    )  # Connected land component id
    landmass_class: Int8Array | None = field(
        default=None, metadata={"dtype": np.int8}
    )  # 0 = ocean, 1 = island, 2 = landmass, 3 = major
    temperature: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # [0,1] warmth; 1 = sunband
    precipitation: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # [0,1] rainfall
    wind_u: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # unit wind direction x
    wind_v: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # unit wind direction y
    wind_magnitude: Float64Array | None = field(
        default=None, metadata={"dtype": np.float64}
    )  # [0,1] wind speed

    @classmethod
    def allocate(cls, n: int) -> Self:
        """Create zeroed per-tile field arrays of length n."""
        return cls(
            **{
                f.name: np.zeros(n, dtype=f.metadata["dtype"])
                for f in fields(class_or_instance=cls)
            }
        )
