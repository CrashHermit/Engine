"""Terrain field specs: elevation, plates, routing, landmasses, vulcanism."""

from src.core.model.environment.field_spec import (
    DTYPE_BOOL,
    DTYPE_F8,
    DTYPE_I1,
    DTYPE_I4,
    FieldSpec,
)

TERRAIN_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("elevation", DTYPE_F8, lo=-1.0, hi=1.0, doc="Normalized height in [-1,1]; 0 = sea level"),
    FieldSpec("is_land", DTYPE_BOOL, doc="True when elevation is at or above sea level"),
    FieldSpec("plate_id", DTYPE_I4, doc="Which plate owns the cell"),
    FieldSpec("uplift", DTYPE_F8, doc="Tectonic push-up rate"),
    FieldSpec("z_route", DTYPE_F8, doc="Water-routing elevation (separate from terrain)"),
    FieldSpec("receiver", DTYPE_I4, doc="Downstream cell id; -1 = base level"),
    FieldSpec("drainage", DTYPE_F8, doc="Upstream area (river size)"),
    FieldSpec("slope", DTYPE_F8, doc="Steepest descent"),
    FieldSpec("coast_distance", DTYPE_F8, doc="Hops from coast"),
    FieldSpec("landmass_id", DTYPE_I4, doc="Connected land component id"),
    FieldSpec("landmass_class", DTYPE_I1, doc="0 = ocean, 1 = island, 2 = landmass, 3 = major"),
    FieldSpec("volcanism", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] present-day volcanic activity"),
    FieldSpec("is_volcano", DTYPE_BOOL, doc="Cell is a discrete volcano summit"),
    FieldSpec("volcano_id", DTYPE_I4, doc="Volcano object id; -1 = none"),
)
