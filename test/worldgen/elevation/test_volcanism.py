from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation.volcanism import VolcanicField
from src.worldgen.geometry import Mesh, generate_icosphere
from src.worldgen.geometry.boundary import BoundaryNetwork, SphericalRegions
from src.worldgen.geology.model import (
    HotspotResult,
    VolcanoSites,
    VolcanoSource,
    VolcanoState,
)


def _hotspots(seeds, plates, widths, heights, cell_count):
    return HotspotResult(
        potential=np.zeros(cell_count),
        seed_indices=np.asarray(seeds, dtype=np.int64),
        plate_ids=np.asarray(plates, dtype=np.int64),
        widths_percent=np.asarray(widths, dtype=np.float64),
        heights_percent=np.asarray(heights, dtype=np.float64),
    )


def _empty_sites():
    return VolcanoSites(
        cell_indices=np.empty(0, dtype=np.int64),
        source_types=np.empty(0, dtype=np.int8),
        states=np.empty(0, dtype=np.int8),
        supply_strength=np.empty(0),
        eruption_intensity=np.empty(0),
        widths_percent=np.empty(0),
        heights_percent=np.empty(0),
    )


def _mesh():
    return Mesh(*generate_icosphere(6))


def _field(mesh, plates, seeds, widths, heights):
    hotspots = _hotspots(seeds, plates[seeds], widths, heights, len(mesh.vertices))
    return VolcanicField(mesh, plates, hotspots, _empty_sites(), SphericalRegions(mesh))


def test_volcanic_shield_peaks_at_seed_falls_off_and_has_compact_support():
    mesh = _mesh()
    plates = np.zeros(len(mesh.vertices), dtype=np.int64)
    result = _field(mesh, plates, [0], [15.0], [0.08]).sample(mesh.vertices, 1.0)
    assert result[0] == 0.0008
    distance = np.arccos(np.clip(mesh.vertices @ mesh.vertices[0], -1.0, 1.0))
    distance *= 100.0 / (2.0 * np.pi)
    supported = np.flatnonzero((distance > 0.0) & (result > 0.0))
    ordered = supported[np.argsort(distance[supported])]
    assert np.all(np.diff(result[ordered]) <= 8.0 * np.finfo(float).eps * result[0])
    assert np.all(result[distance >= 15.0] == 0.0)


def test_volcanic_shields_overlap_by_max_not_sum_and_scale_with_radius():
    mesh = _mesh()
    plates = np.zeros(len(mesh.vertices), dtype=np.int64)
    field = _field(mesh, plates, [0], [20.0], [0.08])
    single = field.sample(mesh.vertices, 2.0)
    overlapping = _field(mesh, plates, [0, 0], [20.0, 20.0], [0.08, 0.04])
    np.testing.assert_array_equal(overlapping.sample(mesh.vertices, 2.0), single)
    np.testing.assert_array_equal(field.sample(mesh.vertices, 4.0), single * 2.0)


def test_plate_confined_shield_approaches_zero_continuously_at_boundary():
    mesh = _mesh()
    plates = (mesh.vertices[:, 0] >= 0.0).astype(np.int64)
    boundary = BoundaryNetwork(mesh, plates)
    distances = boundary.nearest(mesh.vertices)[0]
    seed = int(np.argmin(distances))
    field = _field(mesh, plates, [seed], [20.0], [0.08])
    _, _, closest = boundary.nearest(mesh.vertices[seed : seed + 1])
    q = closest[0]
    toward = mesh.vertices[seed] - q * np.dot(q, mesh.vertices[seed])
    toward /= np.linalg.norm(toward)
    points = np.array([q + toward * 1e-7, q - toward * 1e-7])
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    values = field.sample(points, 1.0)
    assert np.min(values) == 0.0
    assert np.max(values) < 0.0008 * 1e-6
    assert field.sample(mesh.vertices[seed : seed + 1], 1.0)[0] == 0.0008


def test_emergent_and_submerged_hotspots_are_classified_from_final_height():
    from src.worldgen.generate import generate_world

    world = generate_world(WorldgenConfig(seed=71, subdivision_frequency=3))
    background = world.elevation.base_elevation + world.elevation.tectonic_relief
    submerged = np.flatnonzero(background < -0.1)
    emergent = int(submerged[np.argmax(background[submerged])])
    deep = int(submerged[np.argmin(background[submerged])])
    heights = np.array(
        [
            (-background[emergent] + 1.0) * 100.0 / world.radius_m,
            (-background[deep] * 0.5) * 100.0 / world.radius_m,
        ]
    )
    volcanic = _field(
        world.mesh, world.geology.plate_ids, [emergent, deep], [1.0, 1.0], heights
    )
    field = replace(world.elevation_field, volcanoes=volcanic)
    terrain = field.sample(world.mesh.vertices)
    assert terrain.elevation[emergent] > 0.0
    assert terrain.land_mask[emergent]
    assert terrain.elevation[deep] < 0.0
    assert not terrain.land_mask[deep]
    np.testing.assert_array_equal(terrain.land_mask, terrain.elevation >= 0.0)


def test_extinct_historical_volcanoes_keep_relief_without_current_activity():
    from src.worldgen.generate import generate_world

    config = WorldgenConfig(seed=2026, subdivision_frequency=20)
    volcanic_config = replace(
        config.geology.volcanism, supplied_site_count=0, historical_extinct_site_count=4
    )
    world = generate_world(
        replace(config, geology=replace(config.geology, volcanism=volcanic_config))
    )
    sites = world.geology.volcanism.sites
    assert np.all(sites.source_types == VolcanoSource.HISTORICAL)
    assert np.all(sites.states == VolcanoState.EXTINCT)
    assert np.all(world.geology.volcanism.activity == 0.0)
    expected = sites.heights_percent * world.radius_m / 100.0
    np.testing.assert_allclose(
        world.elevation.volcanic_relief[sites.cell_indices], expected
    )
    assert np.all(expected > 0.0)
