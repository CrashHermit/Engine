from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geology.config import PlateConfig
from src.worldgen.geology.plates import (
    calculate_plate_velocity,
    generate_plate_rotation,
)


def test_plate_rotations_follow_region_centers_with_seeded_tangent_motion():
    mesh = Mesh(*generate_icosphere(2))
    labels = np.arange(len(mesh.vertices)) % 4
    config = PlateConfig(min_angular_speed=0.05, max_angular_speed=0.20)
    seed = 827
    rotations = generate_plate_rotation(
        mesh, labels, config, rng=np.random.default_rng(seed)
    )
    repeated = generate_plate_rotation(
        mesh, labels, config, rng=np.random.default_rng(seed)
    )
    np.testing.assert_array_equal(rotations, repeated)
    expected_rng = np.random.default_rng(seed)
    centers = []
    for plate in range(4):
        center = mesh.vertices[labels == plate].mean(axis=0)
        center /= np.linalg.norm(center)
        direction = expected_rng.normal(size=3)
        tangent = direction - np.dot(direction, center) * center
        tangent /= np.linalg.norm(tangent)
        speed = expected_rng.uniform(0.05, 0.20)
        centers.append(center)
        np.testing.assert_allclose(
            rotations[plate], np.cross(center, tangent * speed), atol=1e-15
        )
    assert all(0.05 <= np.linalg.norm(rotation) <= 0.20 for rotation in rotations)
    np.testing.assert_allclose(
        [np.dot(rotation, center) for rotation, center in zip(rotations, centers)],
        0.0,
        atol=1e-15,
    )


def test_single_cell_region_gets_valid_motion_and_velocity():
    mesh = Mesh(*generate_icosphere(1))
    labels = np.arange(len(mesh.vertices), dtype=np.int64)
    rotation = generate_plate_rotation(
        mesh, labels, PlateConfig(), rng=np.random.default_rng(18)
    )
    velocity = calculate_plate_velocity(mesh, rotation, labels)
    assert rotation.shape == (len(mesh.vertices), 3)
    assert np.isfinite(rotation).all()
    assert np.isfinite(velocity).all()
    assert np.all(np.linalg.norm(rotation, axis=1) >= 0.05 - 1e-15)
    assert np.all(np.linalg.norm(rotation, axis=1) <= 0.20 + 1e-15)


def test_motion_scale_changes_boundary_motion_without_changing_regions():
    config = WorldgenConfig(seed=2026, subdivision_frequency=5)
    first = generate_world(config)
    scaled = generate_world(
        replace(
            config,
            geology=replace(
                config.geology, plates=replace(config.geology.plates, motion_scale=2.0)
            ),
        )
    )
    np.testing.assert_array_equal(first.geology.plate_ids, scaled.geology.plate_ids)
    np.testing.assert_array_equal(
        first.geology.crust.region_ids, scaled.geology.crust.region_ids
    )
    for name in (
        "plate_rotation",
        "plate_velocity",
        "boundary_convergence",
        "boundary_divergence",
        "boundary_shear",
    ):
        np.testing.assert_allclose(
            getattr(scaled.geology, name), 2 * getattr(first.geology, name)
        )
    np.testing.assert_allclose(
        scaled.elevation.tectonic_relief,
        2 * first.elevation.tectonic_relief,
    )
