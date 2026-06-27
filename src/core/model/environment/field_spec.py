"""The per-field contract for a generated world's tile/cell arrays.

``FieldSpec`` is the single, numpy-free description of one world field: its name,
storage dtype (as a string token so this module — and ``core/model`` as a whole —
takes no numpy dependency), trailing shape, documented value range, and whether it
ships in the persisted product.

The producer (``src/worldgen``) instantiates these into numpy arrays; future
consumers (persistence schema, gameplay/sim) read the same specs as the
authoritative contract.  See ``field_schema.py`` for the assembled ``FIELD_SCHEMA``.
"""

from dataclasses import dataclass

# Storage dtype tokens.  Kept as strings so core/model stays numpy-free; the
# worldgen Fields container maps these to concrete numpy dtypes.
DTYPE_F8: str = "f8"  # float64
DTYPE_I4: str = "i4"  # int32
DTYPE_I1: str = "i1"  # int8
DTYPE_BOOL: str = "bool"  # bool_

VALID_DTYPES: frozenset[str] = frozenset({DTYPE_F8, DTYPE_I4, DTYPE_I1, DTYPE_BOOL})


@dataclass(frozen=True)
class FieldSpec:
    """One world field's name, storage, shape, range, and product visibility."""

    name: str  #: Attribute name on the Fields container and persisted column.
    dtype: str  #: Storage dtype token (see ``DTYPE_*``).
    extra_dims: tuple[int, ...] = ()  #: Trailing dims: () scalar, (3,) channels, (N,) biomes.
    lo: float | None = None  #: Documented lower bound (contract-checked); None = unbounded.
    hi: float | None = None  #: Documented upper bound (contract-checked); None = unbounded.
    ships_to_product: bool = True  #: False = mesh-side intermediate, never baked to the grid product.
    doc: str = ""  #: One-line meaning.

    def __post_init__(self) -> None:
        if self.dtype not in VALID_DTYPES:
            msg: str = f"FieldSpec {self.name!r}: unknown dtype token {self.dtype!r}"
            raise ValueError(msg)
