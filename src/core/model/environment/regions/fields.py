"""Region field specs: the named-region socket and the biome-region overlay."""

from src.core.model.environment.field_spec import DTYPE_I4, FieldSpec

REGION_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("region_id", DTYPE_I4, doc="Named geographic region id; -1 = unassigned"),
    FieldSpec("biome_region_id", DTYPE_I4, doc="Biome-region id (forest/plains/...); -1 = none (ocean/lake)"),
)
