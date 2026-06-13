"""Plate personality invariants: uplift mapping, drift unit length, determinism."""

from __future__ import annotations

import numpy as np

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.terrain.plate_personalities import (
    PlateProperties,
    assign_plate_personalities,
    fill_uplift_from_plates,
)
from src.worldgen.types import Float64Array, Int32Array

N_PLATES: int = 12
SEED: int = 42


def test_uplift_matches_plate_lookup() -> None:
    """Every cell's uplift equals its plate's base uplift."""
    props: PlateProperties = assign_plate_personalities(
        n_plates=N_PLATES,
        seed=SEED,
        config=PlatesConfig(continental_fraction=0.5),
    )
    plate_id: Int32Array = np.array([0, 0, 1, 2, 2, 2], dtype=np.int32)
    uplift: Float64Array = fill_uplift_from_plates(
        plate_id=plate_id,
        base_uplift=props.base_uplift,
    )

    cell: int
    plate: int
    for cell, plate in enumerate(plate_id):
        assert uplift[cell] == props.base_uplift[plate]


def test_drift_vectors_are_unit_length() -> None:
    """Drift is a direction only — each row must have norm 1."""
    props: PlateProperties = assign_plate_personalities(
        n_plates=N_PLATES,
        seed=SEED,
        config=PlatesConfig(),
    )
    norms: Float64Array = np.linalg.norm(props.drift, axis=1)
    np.testing.assert_allclose(actual=norms, desired=1.0, rtol=1e-12)


def test_same_seed_is_deterministic() -> None:
    """Personality rolls are a pure function of seed and config."""
    cfg: PlatesConfig = PlatesConfig(continental_fraction=0.45)
    a: PlateProperties = assign_plate_personalities(
        n_plates=N_PLATES,
        seed=SEED,
        config=cfg,
    )
    b: PlateProperties = assign_plate_personalities(
        n_plates=N_PLATES,
        seed=SEED,
        config=cfg,
    )
    assert np.array_equal(a1=a.is_continental, a2=b.is_continental)
    assert np.array_equal(a1=a.drift, a2=b.drift)
    assert np.array_equal(a1=a.base_uplift, a2=b.base_uplift)
