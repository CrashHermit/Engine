"""Hydrology enum coverage."""

from __future__ import annotations

from src.core.model.terrain import HYDROLOGY, Hydrology


def test_hydrology_descriptions_cover_all_members() -> None:
    assert set(HYDROLOGY) == set(Hydrology)
