"""Ecology field specs: savagery and the soft biome distribution."""

from src.core.model.environment.ecology.biome import BiomeEnum
from src.core.model.environment.field_spec import DTYPE_F8, FieldSpec

# Soft biome membership is a dense (n, n_biomes) matrix; the trailing dim is the
# BiomeEnum cardinality so the schema follows the biome taxonomy automatically.
N_BIOMES: int = len(BiomeEnum)

ECOLOGY_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("savagery", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] danger/wildness from geography"),
    FieldSpec(
        "biome_weights", DTYPE_F8, extra_dims=(N_BIOMES,), lo=0.0, hi=1.0,
        doc="(n, n_biomes) soft biome distribution",
    ),
)
