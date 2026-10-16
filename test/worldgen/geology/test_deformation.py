import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.geology.boundary_sections import (
    generate_boundary_sections,
    section_plate_boundaries,
)
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.topology import edge_face_indices
from src.worldgen.geology.model import CrustResult


def _section_fixture():
    vertices = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.2],
            [0.1, 0.0, 1.0],
            [-1.0, 0.1, 0.0],
            [0.0, -1.0, 0.3],
            [0.0, 0.0, -1.0],
        ]
    )
    vertices /= np.linalg.norm(vertices, axis=1, keepdims=True)
    return Mesh(
        vertices,
        np.array(
            [
                [0, 1, 2],
                [0, 2, 3],
                [0, 3, 4],
                [0, 4, 1],
                [5, 2, 1],
                [5, 3, 2],
                [5, 4, 3],
                [5, 1, 4],
            ]
        ),
    )


def _crust(mesh, continental, density_by_cell):
    return CrustResult(
        region_ids=np.arange(len(mesh.vertices)),
        seed_indices=np.empty(0, dtype=np.int64),
        continental_regions=np.asarray(continental),
        continental_mask=np.asarray(continental),
        shaping_field=np.zeros(len(mesh.vertices)),
        effective_density=np.asarray(density_by_cell, dtype=float),
        density_anomaly=np.zeros(len(mesh.vertices)),
        region_effective_density=np.asarray(density_by_cell, dtype=float),
    )


def _edge_id(mesh, a, b):
    return int(np.flatnonzero(np.all(mesh.edges == np.sort([a, b]), axis=1))[0])


def test_sections_use_dual_edge_length_weighting_and_ordered_plate_sides():
    mesh = _section_fixture()
    # Two edges of face [0, 1, 2] form one dual-connected section.
    edges = np.array([_edge_id(mesh, 0, 1), _edge_id(mesh, 0, 2)])
    plates = np.array([9, 2, 2, 20, 21, 22])
    continental = np.array([False, True, True, False, False, False])
    density = np.array([8.0, 1.0, 5.0, 3.0, 4.0, 6.0])
    result = generate_boundary_sections(
        mesh, plates, _crust(mesh, continental, density), edges
    )
    assert result.plate_pairs.tolist() == [[2, 9]]
    assert result.continental_sides.tolist() == [[True, False]]
    assert result.subducting_plate_ids.tolist() == [9]
    incidence = edge_face_indices(mesh)
    lengths = np.array(
        [
            np.arccos(np.clip(np.dot(*mesh.dual_vertices[incidence[e]]), -1, 1))
            for e in edges
        ]
    )
    expected_low = np.average([1.0, 5.0], weights=lengths)
    expected_high = np.average([8.0, 8.0], weights=lengths)
    assert not np.isclose(lengths[0], lengths[1])
    np.testing.assert_allclose(
        result.side_effective_density[0], [expected_low, expected_high]
    )


def test_sections_ignore_motion_and_join_edges_with_same_plate_pair_and_crust():
    mesh = _section_fixture()
    edges = np.array([_edge_id(mesh, 0, 1), _edge_id(mesh, 0, 2)])
    convergence = np.array([1.0, 0.0])
    divergence = np.array([0.0, 1.0])
    assert not np.array_equal(convergence, divergence)

    plates = np.array([0, 1, 1, 2, 3, 4])
    continental = np.zeros(6, dtype=bool)
    section_ids, pairs, sides = section_plate_boundaries(
        mesh, plates, continental, edges
    )
    assert section_ids.tolist() == [0, 0]
    assert pairs.tolist() == [[0, 1]]
    assert sides.tolist() == [[False, False]]

    # The caller retains raw motion separately; section generation has no
    # motion input and therefore cannot split this coherent dual-connected pair.
    crust = _crust(mesh, continental, [10, 1, 100, 3, 4, 5])
    result = generate_boundary_sections(mesh, plates, crust, edges)
    assert result.edge_section_ids.tolist() == [0, 0]
    assert result.subducting_plate_ids.tolist() == [1]


def test_polarity_rules_cover_continental_oceanic_and_density_tie_cases():
    mesh = _section_fixture()
    edge = np.array([_edge_id(mesh, 0, 1)])
    plates = np.array([8, 3, 1, 4, 5, 6])

    continental_oceanic = generate_boundary_sections(
        mesh,
        plates,
        _crust(mesh, [True, False, False, False, False, False], np.ones(6)),
        edge,
    )
    assert continental_oceanic.subducting_plate_ids.tolist() == [3]

    continental_collision = generate_boundary_sections(
        mesh,
        plates,
        _crust(mesh, [True, True, False, False, False, False], np.ones(6)),
        edge,
    )
    assert continental_collision.subducting_plate_ids.tolist() == [-1]

    oceanic_oceanic = generate_boundary_sections(
        mesh,
        plates,
        _crust(mesh, np.zeros(6, bool), [1, 1, 1, 1, 1, 1]),
        edge,
    )
    # Equal effective densities choose the lower plate ID, independent of
    # the edge's vertex order.
    assert oceanic_oceanic.plate_pairs.tolist() == [[3, 8]]
    denser_right = generate_boundary_sections(
        mesh,
        plates,
        _crust(mesh, np.zeros(6, bool), [10, 1, 1, 1, 1, 1]),
        edge,
    )
    assert denser_right.subducting_plate_ids.tolist() == [8]


def test_empty_sections_and_complete_dual_loop_are_readonly():
    mesh = _section_fixture()
    empty = generate_boundary_sections(
        mesh,
        np.zeros(6, dtype=int),
        _crust(mesh, np.zeros(6, bool), np.ones(6)),
        np.empty(0, dtype=int),
    )
    assert empty.plate_pairs.shape == (0, 2)
    assert empty.continental_sides.shape == (0, 2)
    assert empty.side_effective_density.shape == (0, 2)
    assert empty.subducting_plate_ids.shape == (0,)
    assert empty.edge_section_ids.shape == (0,)
    assert all(
        not array.flags.writeable
        for array in (
            empty.edge_section_ids,
            empty.plate_pairs,
            empty.continental_sides,
            empty.side_effective_density,
            empty.subducting_plate_ids,
        )
    )

    # A one-versus-rest plate partition makes the boundary a complete dual loop.
    loop_plates = np.array([0, 1, 1, 1, 1, 1])
    ring = np.array([_edge_id(mesh, 0, n) for n in [1, 2, 3, 4]])
    components = generate_boundary_sections(
        mesh,
        loop_plates,
        _crust(mesh, np.zeros(6, bool), np.ones(6)),
        ring,
    )
    assert components.edge_section_ids.tolist() == [0, 0, 0, 0]
    assert all(
        not array.flags.writeable
        for array in (
            components.edge_section_ids,
            components.plate_pairs,
            components.continental_sides,
            components.side_effective_density,
            components.subducting_plate_ids,
        )
    )


def test_generated_boundary_sections_have_consistent_order_and_polarity() -> None:
    world = generate_world(WorldgenConfig(seed=2026, subdivision_frequency=5))
    geology = world.geology
    sections = geology.boundary_sections

    assert np.all(sections.plate_pairs[:, 0] < sections.plate_pairs[:, 1])
    assert np.all(sections.edge_section_ids >= 0)
    for section in range(len(sections.plate_pairs)):
        edges = geology.boundary_edge_indices[sections.edge_section_ids == section]
        assert len(edges) > 0
        pair = sections.plate_pairs[section]
        sides = sections.continental_sides[section]
        subducting = sections.subducting_plate_ids[section]
        if sides.all():
            assert subducting == -1
        elif sides[0] != sides[1]:
            assert subducting == pair[np.flatnonzero(~sides)[0]]
        elif (
            sections.side_effective_density[section, 0]
            > sections.side_effective_density[section, 1]
        ):
            assert subducting == pair[0]
        elif (
            sections.side_effective_density[section, 1]
            > sections.side_effective_density[section, 0]
        ):
            assert subducting == pair[1]
        else:
            assert subducting == pair[0]
