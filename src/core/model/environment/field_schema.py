"""``FIELD_SCHEMA`` — the authoritative, cross-system contract for world fields.

The ordered concatenation of the per-domain field groups.  This single registry
is the source of truth for:

* **worldgen** — allocates and bakes its numpy ``Fields`` container from it;
* **persistence** (future round) — derives the column schema from it;
* **gameplay / simulation** (future) — reads field metadata (dtype, range) from it.

It is pure-stdlib (no numpy): dtypes are string tokens (see ``field_spec``).
"""

from src.core.model.environment.climate.fields import CLIMATE_FIELDS
from src.core.model.environment.ecology.fields import ECOLOGY_FIELDS
from src.core.model.environment.field_spec import FieldSpec
from src.core.model.environment.magic.fields import MAGIC_FIELDS
from src.core.model.environment.regions.fields import REGION_FIELDS
from src.core.model.environment.terrain.fields import TERRAIN_FIELDS
from src.core.model.environment.water.fields import WATER_FIELDS

# Ordered by domain.  The worldgen Fields dataclass mirrors this exact order; a
# drift-guard test keeps the two aligned.
FIELD_SCHEMA: tuple[FieldSpec, ...] = (
    *TERRAIN_FIELDS,
    *CLIMATE_FIELDS,
    *WATER_FIELDS,
    *ECOLOGY_FIELDS,
    *MAGIC_FIELDS,
    *REGION_FIELDS,
)

# Name → spec, for quick lookup by the container, bake, and consumers.
FIELD_BY_NAME: dict[str, FieldSpec] = {spec.name: spec for spec in FIELD_SCHEMA}

# The product subset: only these fields are baked onto the grid product.
PRODUCT_FIELDS: tuple[FieldSpec, ...] = tuple(
    spec for spec in FIELD_SCHEMA if spec.ships_to_product
)
