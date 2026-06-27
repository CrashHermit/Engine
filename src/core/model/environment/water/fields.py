"""Water field specs: discharge, rivers, flow, lakes."""

from src.core.model.environment.field_spec import (
    DTYPE_BOOL,
    DTYPE_F8,
    DTYPE_I4,
    FieldSpec,
)

WATER_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("discharge", DTYPE_F8, doc="Rain-weighted water flow volume"),
    FieldSpec("is_river", DTYPE_BOOL, doc="Cell carries a river"),
    FieldSpec("river_id", DTYPE_I4, doc="River object id; -1 = none"),
    FieldSpec("flow_u", DTYPE_F8, doc="Unit flow direction x"),
    FieldSpec("flow_v", DTYPE_F8, doc="Unit flow direction y"),
    FieldSpec("flow_speed", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] stylized flow speed"),
    FieldSpec("is_lake", DTYPE_BOOL, doc="Cell is under lake water"),
    FieldSpec("lake_id", DTYPE_I4, doc="Lake object id; -1 = none"),
)
