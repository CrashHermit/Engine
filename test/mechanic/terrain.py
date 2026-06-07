"""Elevation enum coverage."""

from __future__ import annotations

from src.core.model.terrain import ELEVATION, Elevation


def test_elevation_descriptions_cover_all_members() -> None:
    assert set(ELEVATION) == set(Elevation)
