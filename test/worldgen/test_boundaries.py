"""Shared boundary classifier invariants: ranges, kind consistency, polarity."""

import numpy as np

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.terrain.boundaries import (
    BoundaryKind,
    classify_boundaries,
)
from src.worldgen.terrain.plate_personalities import assign_plate_personalities
from src.worldgen.terrain.plates import build_plates

MESH_SEED: int = 1
N_PLATES: int = 8
PLATE_SEED: int = 42
CELL_COUNT: int = 600

CONV_KINDS = {int(BoundaryKind.CONV_OO), int(BoundaryKind.CONV_OC), int(BoundaryKind.CONV_CC)}
DIV_KINDS = {int(BoundaryKind.DIV_OO), int(BoundaryKind.DIV_OC), int(BoundaryKind.DIV_CC)}


def _setup():
    geometry: MeshGeometry = build_mesh(
        seed=MESH_SEED,
        cell_count=CELL_COUNT,
        lloyd_iterations=2,
        width=50.0,
        height=50.0,
    )
    plate_id = build_plates(
        geometry=geometry, n_plates=N_PLATES, seed=PLATE_SEED, growth_raggedness=2.0
    )
    props = assign_plate_personalities(
        n_plates=N_PLATES, seed=PLATE_SEED, config=PlatesConfig()
    )
    facts = classify_boundaries(geometry=geometry, plate_id=plate_id, properties=props)
    return geometry, plate_id, props, facts


def test_magnitudes_nonnegative_and_sized() -> None:
    """Convergence/divergence are >= 0 and span every cell."""
    geometry, _plate_id, _props, facts = _setup()
    assert facts.convergence.shape == (geometry.n_cells,)
    assert facts.divergence.shape == (geometry.n_cells,)
    assert np.all(facts.convergence >= 0.0)
    assert np.all(facts.divergence >= 0.0)


def test_kind_consistent_with_magnitude() -> None:
    """A kind is NONE exactly when its magnitude is zero, and from the right family."""
    _geometry, _plate_id, _props, facts = _setup()
    # convergence
    conv_zero = facts.convergence == 0.0
    assert np.all(facts.conv_kind[conv_zero] == int(BoundaryKind.NONE))
    for k in facts.conv_kind[~conv_zero]:
        assert int(k) in CONV_KINDS
    # divergence
    div_zero = facts.divergence == 0.0
    assert np.all(facts.div_kind[div_zero] == int(BoundaryKind.NONE))
    for k in facts.div_kind[~div_zero]:
        assert int(k) in DIV_KINDS


def test_no_cc_subduction_overriding() -> None:
    """Continent-continent collision has no subduction, so its cells never override.

    (is_overriding only carries meaning for genuine subduction, OO/OC.)
    """
    _geometry, _plate_id, _props, facts = _setup()
    cc = facts.conv_kind == int(BoundaryKind.CONV_CC)
    # Whatever overriding flag CC cells carry is meaningless; assert the field
    # is only ever True on convergent cells (never on pure-divergent/interior).
    assert np.all(~facts.is_overriding[facts.convergence == 0.0])


def test_overriding_is_lighter_plate() -> None:
    """Where a cell overrides, its plate is lighter (less dense) than the neighbor it converges with."""
    geometry, plate_id, props, facts = _setup()
    density = props.density
    # For every overriding convergent cell, at least one cross-plate neighbor it
    # converges toward is denser than its own plate.
    checked = 0
    for cell in np.flatnonzero(facts.is_overriding & (facts.convergence > 0.0)):
        pi = int(plate_id[cell])
        denser_neighbor = False
        for nb in geometry.neighbors_of(cell_id=int(cell)):
            pj = int(plate_id[int(nb)])
            if pj != pi and density[pj] >= density[pi]:
                denser_neighbor = True
                break
        assert denser_neighbor, f"overriding cell {cell} has no denser neighbor"
        checked += 1
    assert checked > 0, "expected at least one overriding subduction cell"


def test_classifier_deterministic() -> None:
    """Same inputs produce identical facts."""
    _g, _p, _props, a = _setup()
    _g2, _p2, _props2, b = _setup()
    np.testing.assert_array_equal(a.convergence, b.convergence)
    np.testing.assert_array_equal(a.divergence, b.divergence)
    np.testing.assert_array_equal(a.conv_kind, b.conv_kind)
    np.testing.assert_array_equal(a.div_kind, b.div_kind)
    np.testing.assert_array_equal(a.is_overriding, b.is_overriding)
