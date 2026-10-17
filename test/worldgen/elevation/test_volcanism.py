from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation.generate import generate_elevation
from src.worldgen.elevation.volcanism import volcanic_relief
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.model import HotspotResult
from src.worldgen.field.noise import noise_multiplier


def _hotspots(seeds, plates, widths, heights, cell_count):
    potential = np.zeros(cell_count, dtype=np.float64)
    potential.setflags(write=False)
    return HotspotResult(
        potential=potential,
        seed_indices=np.asarray(seeds, dtype=np.int64),
        plate_ids=np.asarray(plates, dtype=np.int64),
        widths_percent=np.asarray(widths, dtype=np.float64),
        heights_percent=np.asarray(heights, dtype=np.float64),
    )


def _mesh():
    vertices, faces = generate_icosphere(nu=6)
    return Mesh(vertices, faces)


def test_volcanic_shield_peaks_at_seed_falls_off_and_has_compact_support():
    mesh = _mesh()
    seed = 0
    plates = np.zeros(len(mesh.vertices), dtype=np.int64)
    result = volcanic_relief(
        mesh, plates, _hotspots([seed], [0], [15.0], [0.08], len(mesh.vertices)), 1.0
    )

    assert result[seed] == 0.0008
    distances = np.arccos(np.clip(mesh.vertices @ mesh.vertices[seed], -1.0, 1.0))
    distance_percent = distances * (100.0 / (2.0 * np.pi))
    supported = np.flatnonzero((distance_percent > 0.0) & (result > 0.0))
    assert len(supported) > 0
    ordered = supported[np.argsort(distance_percent[supported])]
    rounding = 8.0 * np.finfo(np.float64).eps * result[seed]
    assert np.all(np.diff(result[ordered]) <= rounding)
    assert np.all(result[distance_percent >= 15.0] == 0.0)


def test_volcanic_shields_overlap_by_max_not_sum_and_scale_with_radius():
    mesh = _mesh()
    plates = np.zeros(len(mesh.vertices), dtype=np.int64)
    single = volcanic_relief(
        mesh, plates, _hotspots([0], [0], [20.0], [0.08], len(mesh.vertices)), 2.0
    )
    overlapping = volcanic_relief(
        mesh,
        plates,
        _hotspots([0, 0], [0, 0], [20.0, 20.0], [0.08, 0.04], len(mesh.vertices)),
        2.0,
    )
    doubled_radius = volcanic_relief(
        mesh, plates, _hotspots([0], [0], [20.0], [0.08], len(mesh.vertices)), 4.0
    )

    np.testing.assert_array_equal(overlapping, single)
    np.testing.assert_array_equal(doubled_radius, single * 2.0)


def test_volcanic_shield_does_not_cross_assigned_plate_boundary():
    mesh = _mesh()
    seed = 0
    distances = np.arccos(np.clip(mesh.vertices @ mesh.vertices[seed], -1.0, 1.0))
    other_plate_vertex = int(np.flatnonzero((distances > 0.0) & (distances < 0.4))[0])
    plates = np.zeros(len(mesh.vertices), dtype=np.int64)
    plates[other_plate_vertex] = 1
    result = volcanic_relief(
        mesh, plates, _hotspots([seed], [0], [20.0], [0.08], len(mesh.vertices)), 1.0
    )

    assert result[seed] > 0.0
    assert result[other_plate_vertex] == 0.0


def test_emergent_and_submerged_hotspots_are_classified_from_final_height():
    from src.worldgen.generate import generate_world

    world = generate_world(WorldgenConfig(seed=71, subdivision_frequency=3))
    background = world.elevation.base_elevation + world.elevation.tectonic_relief
    submerged = np.flatnonzero(background < -0.1)
    emergent_seed = int(submerged[np.argmax(background[submerged])])
    submerged_seed = int(submerged[np.argmin(background[submerged])])
    streams = np.random.SeedSequence(71).spawn(12)

    def signed_seed(sequence):
        value = int(sequence.generate_state(1, dtype=np.uint64)[0])
        return value if value < 2**63 else value - 2**64

    noise_seeds = tuple(signed_seed(stream) for stream in streams[5:8])
    arc_noise_seed = signed_seed(streams[10])
    radius = world.radius_m
    heights = np.array(
        [
            (-background[emergent_seed] + 1.0) * 100.0 / radius,
            (-background[submerged_seed] * 0.5) * 100.0 / radius,
        ]
    )
    hotspots = _hotspots(
        [emergent_seed, submerged_seed],
        [
            world.geology.plate_ids[emergent_seed],
            world.geology.plate_ids[submerged_seed],
        ],
        [1.0, 1.0],
        heights,
        len(world.mesh.vertices),
    )
    terrain = generate_elevation(
        world.mesh,
        WorldgenConfig(seed=71, subdivision_frequency=3).elevation,
        radius,
        crust=world.geology.crust,
        plate_ids=world.geology.plate_ids,
        boundary_edge_indices=world.geology.boundary_edge_indices,
        boundary_sections=world.geology.boundary_sections,
        boundary_convergence=world.geology.boundary_convergence,
        boundary_divergence=world.geology.boundary_divergence,
        boundary_shear=world.geology.boundary_shear,
        noise_seeds=noise_seeds,
        arc_variation=noise_multiplier(
            world.mesh.vertices, seed=arc_noise_seed, frequency=6.0, strength=0.6
        ),
        volcano_sites=world.geology.volcanism.sites,
        hotspots=hotspots,
    )

    assert terrain.elevation[emergent_seed] > 0.0
    assert terrain.land_mask[emergent_seed]
    assert terrain.elevation[submerged_seed] < 0.0
    assert not terrain.land_mask[submerged_seed]
    np.testing.assert_array_equal(terrain.land_mask, terrain.elevation >= 0.0)


def test_extinct_historical_volcanoes_keep_relief_without_current_activity():
    from src.worldgen.generate import generate_world
    from src.worldgen.geology.model import VolcanoSource, VolcanoState

    config = WorldgenConfig(seed=2026, subdivision_frequency=20)
    volcanic_config = replace(
        config.geology.volcanism,
        supplied_site_count=0,
        historical_extinct_site_count=4,
    )
    world = generate_world(
        replace(config, geology=replace(config.geology, volcanism=volcanic_config))
    )
    sites = world.geology.volcanism.sites
    assert np.all(sites.source_types == VolcanoSource.HISTORICAL)
    assert np.all(sites.states == VolcanoState.EXTINCT)
    np.testing.assert_array_equal(
        world.geology.volcanism.activity, np.zeros(len(world.mesh.vertices))
    )
    expected_peaks = sites.heights_percent * world.radius_m / 100.0
    assert np.all(world.elevation.volcanic_relief[sites.cell_indices] >= expected_peaks)
    assert np.all(expected_peaks > 0.0)
