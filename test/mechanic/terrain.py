"""Salinity defaults for water forms."""

from __future__ import annotations

from src.core.model.terrain import Salinity, WaterForm, resolve_salinity


def test_resolve_salinity_uses_explicit_override() -> None:
    assert (
        resolve_salinity(WaterForm.OCEAN, Salinity.FRESH) == Salinity.FRESH
    )


def test_resolve_salinity_falls_back_to_form_default() -> None:
    assert resolve_salinity(WaterForm.SEA, None) == Salinity.SALT
    assert resolve_salinity(WaterForm.RIVER, None) == Salinity.FRESH
