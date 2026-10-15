from dataclasses import replace

import numpy as np

from src.worldgen.config import PlanetConfig, WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.terrain.config import TerrainConfig
from src.worldgen.terrain.generate import (
    _base_elevation,
    _edge_lengths_percent,
    generate_terrain,
)


def test_smooth_coastal_profile_saturates_at_expected_heights() -> None:
    config = TerrainConfig()
    distances = np.array(
        [
            config.shelf_width_percent + config.inland_width_percent,
            config.shelf_width_percent,
            0.0,
            -(config.shelf_width_percent + config.slope_width_percent),
            -(2 * config.shelf_width_percent + config.slope_width_percent),
        ]
    )
    np.testing.assert_allclose(
        _base_elevation(distances, config, 100.0),
        [
            config.interior_height_percent,
            0.0,
            -config.shelf_depth_percent,
            -config.basin_depth_percent,
            -config.basin_depth_percent,
        ],
    )


def test_margin_distances_have_class_signs_and_start_half_edge_lengths() -> None:
    vertices, faces = generate_icosphere(nu=2)
    mesh = Mesh(vertices, faces)
    mask = np.zeros(len(vertices), dtype=bool)
    mask[0] = True
    terrain = generate_terrain(mesh, mask, TerrainConfig(), PlanetConfig().radius_m)
    lengths = _edge_lengths_percent(mesh)

    assert np.all(terrain.margin_distance[mask] > 0)
    assert np.all(terrain.margin_distance[~mask] < 0)
    for edge_index in terrain.coast_edge_indices:
        left, right = mesh.edges[edge_index]
        expected = lengths[edge_index] / 2
        assert terrain.margin_distance[left] <= expected
        assert terrain.margin_distance[right] <= expected
    assert not terrain.margin_distance.flags.writeable
    assert not terrain.base_elevation.flags.writeable
    assert not terrain.land_mask.flags.writeable
    assert not terrain.coast_edge_indices.flags.writeable


def test_world_terrain_is_deterministic_and_uses_crust_mask() -> None:
    config = WorldgenConfig(seed=123, subdivision_frequency=3)
    first, second = generate_world(config), generate_world(config)

    np.testing.assert_array_equal(
        first.terrain.margin_distance, second.terrain.margin_distance
    )
    np.testing.assert_array_equal(
        first.terrain.base_elevation, second.terrain.base_elevation
    )
    np.testing.assert_array_equal(
        first.terrain.coast_edge_indices,
        np.flatnonzero(
            first.geology.crust.continental_mask[first.mesh.edges[:, 0]]
            != first.geology.crust.continental_mask[first.mesh.edges[:, 1]]
        ),
    )
    np.testing.assert_array_equal(
        first.geology.crust.continental_mask,
        second.geology.crust.continental_mask,
    )


def test_radius_scales_elevation_without_changing_geography() -> None:
    config = WorldgenConfig(seed=2026, subdivision_frequency=5)
    first = generate_world(config)
    larger = generate_world(
        replace(config, planet=PlanetConfig(radius_m=config.planet.radius_m * 2.0))
    )

    np.testing.assert_array_equal(first.mesh.vertices, larger.mesh.vertices)
    np.testing.assert_array_equal(first.geology.plate_ids, larger.geology.plate_ids)
    np.testing.assert_array_equal(
        first.geology.crust.region_ids, larger.geology.crust.region_ids
    )
    np.testing.assert_array_equal(
        first.terrain.margin_distance, larger.terrain.margin_distance
    )
    np.testing.assert_array_equal(first.terrain.land_mask, larger.terrain.land_mask)
    np.testing.assert_allclose(
        larger.terrain.base_elevation, first.terrain.base_elevation * 2.0
    )
