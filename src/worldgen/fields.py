"""The worldgen ``Fields`` container — one numpy struct-of-arrays for all fields.

A single declaration, used for **both** the mesh-resolution scratch instance the
pipeline mutates and the grid-resolution product instance the bake produces (the
"one type, two instances" model).  Storage, dtype, shape, and product visibility
are governed by ``FIELD_SCHEMA`` in ``core/model`` — this container is its numpy
realization.  Arrays are eagerly allocated (never ``None``), so stages read fields
directly without the old per-field narrowing ritual.

To add a field: add a ``FieldSpec`` to the relevant domain group in
``core/model/.../<domain>/fields.py`` **and** a typed attribute here, in the same
order.  ``test_fields_schema`` fails loudly if the two drift apart.
"""

from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from typing import Self

import numpy as np

from src.core.model.environment.field_schema import FIELD_SCHEMA
from src.core.model.environment.field_spec import (
    DTYPE_BOOL,
    DTYPE_F8,
    DTYPE_I1,
    DTYPE_I4,
)
from src.worldgen.types import BoolArray, Float64Array, Int8Array, Int32Array

# dtype token -> concrete numpy dtype.  The schema is numpy-free; the mapping
# lives here, in the producer.
_DTYPE_MAP: dict[str, type] = {
    DTYPE_F8: np.float64,
    DTYPE_I4: np.int32,
    DTYPE_I1: np.int8,
    DTYPE_BOOL: np.bool_,
}


@dataclass
class Fields:
    """All per-cell (mesh) / per-tile (grid) world arrays, declared once.

    Field order mirrors ``FIELD_SCHEMA`` exactly (terrain → climate → water →
    ecology → magic → regions).  Scalar fields are shape ``(n,)``; the two dense
    fields are ``magic_channels`` ``(n, 3)`` and ``biome_weights`` ``(n, n_biomes)``.
    """

    # --- terrain ---
    elevation: Float64Array  # Normalized height in [-1,1]; 0 = sea level
    is_land: BoolArray  # True when elevation is at or above sea level
    plate_id: Int32Array  # Which plate owns the cell
    uplift: Float64Array  # Tectonic push-up rate
    z_route: Float64Array  # Water-routing elevation (separate from terrain)
    z_filled: Float64Array  # Physical spill surface (depression fill, no routing bias)
    receiver: Int32Array  # Downstream cell id; -1 = base level
    drainage: Float64Array  # Upstream area (river size)
    slope: Float64Array  # Steepest descent
    coast_distance: Float64Array  # Hops from coast
    landmass_id: Int32Array  # Connected land component id
    landmass_class: Int8Array  # 0 = ocean, 1 = island, 2 = landmass, 3 = major
    volcanism: Float64Array  # [0,1] present-day volcanic activity
    is_volcano: BoolArray  # Cell is a discrete volcano summit
    volcano_id: Int32Array  # Volcano object id; -1 = none

    # --- climate ---
    latitude: Float64Array  # [-1,1] signed latitude; 0 = equator
    insolation: Float64Array  # [0,1] authored energy field (mesh-side intermediate)
    temperature: Float64Array  # [0,1] warmth; 1 = equator
    sst: Float64Array  # [0,1] sea-surface temperature
    precipitation: Float64Array  # [0,1] rainfall
    wind_u: Float64Array  # Unit wind direction x
    wind_v: Float64Array  # Unit wind direction y
    wind_magnitude: Float64Array  # [0,1] wind speed
    convergence: Float64Array  # [-1,1] signed vertical motion; drives rain belts

    # --- water ---
    discharge: Float64Array  # Rain-weighted water flow volume
    is_river: BoolArray  # Cell carries a river
    river_id: Int32Array  # River object id; -1 = none
    flow_u: Float64Array  # Unit flow direction x
    flow_v: Float64Array  # Unit flow direction y
    flow_speed: Float64Array  # [0,1] stylized flow speed
    is_lake: BoolArray  # Cell is under lake water
    lake_id: Int32Array  # Lake object id; -1 = none

    # --- ecology ---
    savagery: Float64Array  # [0,1] danger/wildness from geography
    biome_weights: Float64Array  # (n, n_biomes) soft biome distribution

    # --- magic ---
    magic_strength: Float64Array  # [0,1] vein intensity (accumulated mana flow)
    magic_flow_u: Float64Array  # Unit mana-current direction x
    magic_flow_v: Float64Array  # Unit mana-current direction y
    magic_flow_speed: Float64Array  # [0,1] stylized mana-current speed
    is_vein: BoolArray  # Cell carries a leyline vein
    vein_id: Int32Array  # Vein object id; -1 = none
    is_nexus: BoolArray  # Cell is a nexus pole
    nexus_id: Int32Array  # Nexus object id; -1 = none
    magic_channels: Float64Array  # (n, 3) corpus/mens/anima composition

    # --- regions ---
    region_id: Int32Array  # Named geographic region id; -1 = unassigned
    biome_region_id: Int32Array  # Biome-region id; -1 = none (ocean/lake)

    @classmethod
    def allocate(cls, n: int) -> Self:
        """Create eagerly-zeroed arrays of length ``n`` for every schema field."""
        return cls(
            **{
                spec.name: np.zeros(
                    shape=(n, *spec.extra_dims), dtype=_DTYPE_MAP[spec.dtype]
                )
                for spec in FIELD_SCHEMA
            }
        )

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        """Declared attribute names, in order (for the schema drift-guard test)."""
        return tuple(f.name for f in dataclass_fields(cls))
