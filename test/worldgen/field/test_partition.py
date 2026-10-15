import numpy as np

from src.worldgen.field.partition import priority_flood_regions, weighted_regions
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.mesh import Mesh


from src.worldgen.field.cost import field_traversal_cost


def test_field_traversal_cost_uses_field_levels_as_endpoint_multipliers() -> None:
    vertices = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [-1.0, 0.0, 0.0]]
    )
    mesh = Mesh(vertices, np.array([[0, 1, 2], [1, 3, 2]]))
    distance = np.arctan2(
        np.linalg.norm(
            np.cross(mesh.vertices[mesh.edges[:, 0]], mesh.vertices[mesh.edges[:, 1]]),
            axis=1,
        ),
        np.sum(
            mesh.vertices[mesh.edges[:, 0]] * mesh.vertices[mesh.edges[:, 1]], axis=1
        ),
    )

    equal = field_traversal_cost(mesh, np.full(4, 0.5), irregularity_strength=2.0)
    zero = field_traversal_cost(mesh, np.zeros(4), irregularity_strength=10.0)
    maximum = field_traversal_cost(mesh, np.ones(4), irregularity_strength=10.0)

    np.testing.assert_allclose(equal, distance * 2.0)
    np.testing.assert_allclose(zero, distance)
    np.testing.assert_allclose(maximum, distance * 11.0)


def test_weighted_regions_relaxes_late_cheaper_path() -> None:
    vertices = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [-1.0, 0.0, 0.0]]
    )
    faces = np.array([[0, 1, 2], [1, 3, 2]])
    mesh = Mesh(vertices, faces)
    costs = np.array([100.0, 10.0, 100.0, 1.0, 1.0])

    regions = weighted_regions(mesh, np.array([0, 1], dtype=np.int64), costs)

    assert regions.tolist() == [0, 1, 1, 1]


def test_weighted_regions_uses_lower_plate_id_for_equal_costs() -> None:
    vertices = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    mesh = Mesh(vertices, np.array([[0, 1, 2]]))

    regions = weighted_regions(
        mesh,
        np.array([0, 1], dtype=np.int64),
        np.ones(len(mesh.edges), dtype=np.float64),
    )

    assert regions.tolist() == [0, 1, 0]


def test_priority_flood_competes_on_barriers_not_accumulated_cost() -> None:
    vertices = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, -1.0, 0.0],
        ]
    )
    mesh = Mesh(vertices, np.array([[0, 2, 3], [1, 3, 4], [2, 3, 4]]))
    priorities = np.array([[0, 0, 4, 100, 4], [0, 0, 100, 6, 7]], dtype=float)

    owners = priority_flood_regions(mesh, np.array([0, 1]), priorities)

    # Region 0 reaches cell 4 through two priority-4 cells before region 1 at 7.
    assert owners.tolist() == [0, 1, 0, 1, 0]


def test_priority_flood_protects_seeds_and_breaks_ties_by_region() -> None:
    vertices = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    mesh = Mesh(vertices, np.array([[0, 1, 2]]))

    owners = priority_flood_regions(mesh, np.array([0, 1]), np.zeros((2, 3)))

    assert owners.tolist() == [0, 1, 0]


def test_priority_flood_assigns_every_cell_through_its_own_region() -> None:
    mesh = Mesh(*generate_icosphere(3))
    seeds = np.array([0, 20, 40, 60])
    priorities = np.random.default_rng(42).normal(size=(len(seeds), len(mesh.vertices)))

    owners = priority_flood_regions(mesh, seeds, priorities)

    assert np.all((owners >= 0) & (owners < len(seeds)))
    for region, seed in enumerate(seeds):
        visited = {int(seed)}
        frontier = [int(seed)]
        while frontier:
            for neighbor in mesh.neighbors(frontier.pop()):
                neighbor = int(neighbor)
                if owners[neighbor] == region and neighbor not in visited:
                    visited.add(neighbor)
                    frontier.append(neighbor)
        assert visited == set(np.flatnonzero(owners == region))
