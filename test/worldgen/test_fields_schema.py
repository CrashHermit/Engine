"""Drift guard: the worldgen Fields container must mirror FIELD_SCHEMA exactly.

If these fail, the schema (core/model) and its numpy realization (worldgen) have
drifted — add the field in both places, in the same order.
"""

import numpy as np

from src.core.model.environment.field_schema import FIELD_SCHEMA, PRODUCT_FIELDS
from src.worldgen.fields import _DTYPE_MAP, Fields


def test_container_matches_schema_order() -> None:
    """Declared attribute names/order match the schema's exactly."""
    schema_names: tuple[str, ...] = tuple(spec.name for spec in FIELD_SCHEMA)
    assert Fields.field_names() == schema_names


def test_allocate_honors_dtype_and_shape() -> None:
    """allocate(n) produces arrays at each spec's dtype and trailing shape."""
    n: int = 8
    fields: Fields = Fields.allocate(n=n)
    for spec in FIELD_SCHEMA:
        arr = getattr(fields, spec.name)
        assert arr.shape == (n, *spec.extra_dims), f"{spec.name} shape"
        assert arr.dtype == np.dtype(_DTYPE_MAP[spec.dtype]), f"{spec.name} dtype"


def test_product_subset_is_schema_minus_intermediates() -> None:
    """PRODUCT_FIELDS is exactly the ships_to_product subset; insolation is excluded."""
    product_names = {spec.name for spec in PRODUCT_FIELDS}
    assert "insolation" not in product_names
    assert product_names == {spec.name for spec in FIELD_SCHEMA if spec.ships_to_product}
