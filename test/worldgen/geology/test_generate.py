import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world


def test_world_generation_is_seeded_and_complete() -> None:
    config = WorldgenConfig(seed=123, subdivision_frequency=3)
    first = generate_world(config)
    second = generate_world(config)
    other = generate_world(WorldgenConfig(seed=124, subdivision_frequency=3))

    np.testing.assert_array_equal(first.mesh.vertices, second.mesh.vertices)
    np.testing.assert_array_equal(first.mesh.faces, second.mesh.faces)
    np.testing.assert_array_equal(
        first.geology.hotspots.potential, second.geology.hotspots.potential
    )
    np.testing.assert_array_equal(first.geology.plate_ids, second.geology.plate_ids)
    assert not np.array_equal(
        first.geology.hotspots.potential, other.geology.hotspots.potential
    )
    assert len(np.unique(first.geology.plate_ids)) == config.geology.plates.plate_count
    assert np.all(first.geology.plate_ids >= 0)
    assert np.all(first.geology.plate_ids < config.geology.plates.plate_count)
    assert not first.geology.hotspots.potential.flags.writeable


def test_default_priority_flood_regions_are_connected_and_seed_owned():
    config = WorldgenConfig(seed=123, subdivision_frequency=3)
    world = generate_world(config)
    geology = world.geology
    plate_count = config.geology.plates.plate_count
    np.testing.assert_array_equal(
        geology.plate_ids[geology.seed_indices], np.arange(plate_count)
    )

    neighbors = [[] for _ in range(len(world.mesh.vertices))]
    for left, right in world.mesh.edges:
        neighbors[int(left)].append(int(right))
        neighbors[int(right)].append(int(left))
    for plate in range(plate_count):
        cells = np.flatnonzero(geology.plate_ids == plate)
        visited = {int(cells[0])}
        stack = [int(cells[0])]
        while stack:
            current = stack.pop()
            for neighbor in neighbors[current]:
                if geology.plate_ids[neighbor] == plate and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        assert visited == set(cells)


def test_plate_velocity_is_tangent_and_boundaries_are_exact() -> None:
    world = generate_world(WorldgenConfig(seed=123, subdivision_frequency=3))
    mesh = world.mesh
    geology = world.geology

    plate_dot = np.sum(geology.plate_velocity * mesh.vertices, axis=1)
    assert np.allclose(plate_dot, 0.0)
    expected_boundaries = np.flatnonzero(
        geology.plate_ids[mesh.edges[:, 0]] != geology.plate_ids[mesh.edges[:, 1]]
    )
    np.testing.assert_array_equal(geology.boundary_edge_indices, expected_boundaries)


def test_generation_does_not_change_global_numpy_random_state() -> None:
    np.random.seed(77)
    before = np.random.get_state()
    generate_world(WorldgenConfig(seed=123, subdivision_frequency=3))
    after = np.random.get_state()

    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
