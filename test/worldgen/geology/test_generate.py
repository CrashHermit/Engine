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
        first.geology.magma_intensity, second.geology.magma_intensity
    )
    np.testing.assert_array_equal(first.geology.plate_ids, second.geology.plate_ids)
    assert not np.array_equal(
        first.geology.magma_intensity, other.geology.magma_intensity
    )
    assert len(np.unique(first.geology.plate_ids)) == config.geology.plate_count
    assert np.all(first.geology.plate_ids >= 0)
    assert np.all(first.geology.plate_ids < config.geology.plate_count)


def test_geology_velocity_fields_are_tangent_and_boundaries_are_exact() -> None:
    world = generate_world(WorldgenConfig(seed=123, subdivision_frequency=3))
    mesh = world.mesh
    geology = world.geology

    magma_dot = np.sum(geology.magma_velocity * mesh.vertices, axis=1)
    plate_dot = np.sum(geology.plate_velocity * mesh.vertices, axis=1)
    assert np.allclose(magma_dot, 0.0)
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
