"""Magic field specs: vein strength, mana-current flow, veins, nexuses, channels."""

from src.core.model.environment.field_spec import (
    DTYPE_BOOL,
    DTYPE_F8,
    DTYPE_I4,
    FieldSpec,
)

MAGIC_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("magic_strength", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] vein intensity (accumulated mana flow)"),
    FieldSpec("magic_flow_u", DTYPE_F8, doc="Unit mana-current direction x"),
    FieldSpec("magic_flow_v", DTYPE_F8, doc="Unit mana-current direction y"),
    FieldSpec("magic_flow_speed", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] stylized mana-current speed"),
    FieldSpec("is_vein", DTYPE_BOOL, doc="Cell carries a leyline vein"),
    FieldSpec("vein_id", DTYPE_I4, doc="Vein object id; -1 = none"),
    FieldSpec("is_nexus", DTYPE_BOOL, doc="Cell is a nexus pole"),
    FieldSpec("nexus_id", DTYPE_I4, doc="Nexus object id; -1 = none"),
    FieldSpec(
        "magic_channels", DTYPE_F8, extra_dims=(3,), lo=0.0, hi=1.0,
        doc="(n, 3) corpus/mens/anima composition",
    ),
)
