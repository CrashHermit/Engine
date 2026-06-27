"""Climate field specs: latitude/insolation drivers, temperature, wind, convergence."""

from src.core.model.environment.field_spec import DTYPE_F8, FieldSpec

CLIMATE_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("latitude", DTYPE_F8, lo=-1.0, hi=1.0, doc="[-1,1] signed latitude; 0 = equator, +/-1 = poles"),
    FieldSpec(
        "insolation", DTYPE_F8, lo=0.0, hi=1.0, ships_to_product=False,
        doc="[0,1] authored energy field; 1 = equator (mesh-side intermediate)",
    ),
    FieldSpec("temperature", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] warmth; 1 = equator"),
    FieldSpec("sst", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] sea-surface temperature"),
    FieldSpec("precipitation", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] rainfall"),
    FieldSpec("wind_u", DTYPE_F8, doc="Unit wind direction x"),
    FieldSpec("wind_v", DTYPE_F8, doc="Unit wind direction y"),
    FieldSpec("wind_magnitude", DTYPE_F8, lo=0.0, hi=1.0, doc="[0,1] wind speed"),
    FieldSpec("convergence", DTYPE_F8, lo=-1.0, hi=1.0, doc="[-1,1] signed vertical motion; drives rain belts"),
)
