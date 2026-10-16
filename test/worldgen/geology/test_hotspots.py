from dataclasses import replace

import numpy as np

from src.worldgen.field.distance import multi_source_distances
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.config import (
    CrustConfig,
    GeologyConfig,
    HotspotConfig,
    PlateConfig,
)
from src.worldgen.geology.generate import generate_geology
from src.worldgen.geology.hotspots import generate_hotspots
from src.worldgen.utilities.sampling import poisson_disk_sample


def _mesh():
    vertices, faces = generate_icosphere(nu=8)
    return Mesh(vertices, faces)


def _hotspots(mesh, config, plate_ids, boundary_edges, seed=91):
    return generate_hotspots(
        mesh,
        config,
        plate_ids,
        boundary_edges,
        rng=np.random.default_rng(seed),
        potential_noise_seed=seed,
    )


def test_weighted_poisson_placement_prioritizes_a_deterministically_weighted_candidate():
    positions = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    # Candidate 4 is far from all others; its overwhelming synthetic weight makes
    # its exponential-race priority deterministic without a statistical threshold.
    weights = np.array([1e-300, 1e-300, 1e-300, 1e-300, 1e300])

    selected = poisson_disk_sample(
        positions,
        1,
        0.0,
        rng=np.random.default_rng(7),
        weights=weights,
    )

    np.testing.assert_array_equal(selected, [4])


def test_hotspot_generation_is_reproducible_spaced_clear_of_boundaries_and_bounded():
    mesh = _mesh()
    plate_ids = np.zeros(len(mesh.vertices), dtype=np.int64)
    plate_ids[len(mesh.vertices) // 2 :] = 1
    boundary_edges = np.flatnonzero(
        plate_ids[mesh.edges[:, 0]] != plate_ids[mesh.edges[:, 1]]
    )
    config = HotspotConfig(
        count=5,
        min_seed_distance=0.18,
        boundary_clearance_percent=0.7,
        min_width_percent=0.4,
        max_width_percent=0.9,
        min_height_percent=0.02,
        max_height_percent=0.08,
    )
    first = _hotspots(mesh, config, plate_ids, boundary_edges)
    repeated = _hotspots(mesh, config, plate_ids, boundary_edges)
    for name in (
        "potential",
        "seed_indices",
        "plate_ids",
        "widths_percent",
        "heights_percent",
    ):
        values = getattr(first, name)
        np.testing.assert_array_equal(values, getattr(repeated, name))
        assert not values.flags.writeable

    assert len(first.seed_indices) == config.count
    np.testing.assert_array_equal(first.plate_ids, plate_ids[first.seed_indices])
    positions = mesh.vertices[first.seed_indices]
    if len(positions) > 1:
        distances = np.linalg.norm(positions[:, None] - positions[None, :], axis=2)
        distances[np.diag_indices_from(distances)] = np.inf
        assert np.all(distances >= config.min_seed_distance)

    lengths = mesh.edge_lengths_percent
    sources = mesh.edges[boundary_edges].reshape(-1)
    source_distances = np.repeat(lengths[boundary_edges] * 0.5, 2)
    clearance = multi_source_distances(
        mesh, sources, source_distances, lengths, plate_ids
    )
    assert np.all(clearance[first.seed_indices] >= config.boundary_clearance_percent)
    assert np.all(
        (first.widths_percent >= config.min_width_percent)
        & (first.widths_percent <= config.max_width_percent)
    )
    assert np.all(
        (first.heights_percent >= config.min_height_percent)
        & (first.heights_percent <= config.max_height_percent)
    )


def test_hotspot_potential_config_and_bias_control_placement():
    mesh = _mesh()
    plate_ids = np.zeros(len(mesh.vertices), dtype=np.int64)
    boundary_edges = np.empty(0, dtype=np.int64)
    strongly_biased = HotspotConfig(
        count=4,
        min_seed_distance=0.1,
        potential=NoiseConfig(octaves=1, base_frequency=0.3),
        potential_bias=4.0,
    )
    uniform = _hotspots(
        mesh, replace(strongly_biased, potential_bias=0.0), plate_ids, boundary_edges
    )
    biased = _hotspots(mesh, strongly_biased, plate_ids, boundary_edges)
    repeated = _hotspots(mesh, strongly_biased, plate_ids, boundary_edges)

    assert np.all((biased.potential >= 0.0) & (biased.potential <= 1.0))
    np.testing.assert_array_equal(uniform.potential, biased.potential)
    np.testing.assert_array_equal(biased.potential, repeated.potential)
    np.testing.assert_array_equal(biased.seed_indices, repeated.seed_indices)
    assert not np.array_equal(uniform.seed_indices, biased.seed_indices)


def test_hotspot_potential_is_independent_of_plate_and_crust_field_configs():
    base_config = GeologyConfig(
        plates=PlateConfig(growth_method="dijkstra"),
        crust=CrustConfig(growth_method="dijkstra"),
    )
    baseline = _generate(base_config)
    changed_fields = _generate(
        replace(
            base_config,
            plates=replace(
                base_config.plates,
                field=NoiseConfig(octaves=1, base_frequency=2.0),
            ),
            crust=replace(
                base_config.crust,
                field=NoiseConfig(octaves=1, base_frequency=2.0),
            ),
        )
    )

    assert not np.array_equal(baseline.plate_ids, changed_fields.plate_ids)
    assert not np.array_equal(
        baseline.crust.region_ids, changed_fields.crust.region_ids
    )
    np.testing.assert_array_equal(
        baseline.hotspots.potential, changed_fields.hotspots.potential
    )


def test_plate_field_config_changes_dijkstra_ownership_not_hotspot_potential():
    config = GeologyConfig(plates=PlateConfig(growth_method="dijkstra"))
    baseline = _generate(config)
    changed = _generate(
        replace(
            config,
            plates=replace(
                config.plates,
                field=NoiseConfig(octaves=1, base_frequency=2.0),
            ),
        )
    )

    assert not np.array_equal(baseline.plate_ids, changed.plate_ids)
    np.testing.assert_array_equal(
        baseline.hotspots.potential, changed.hotspots.potential
    )


def test_potential_config_changes_dijkstra_hotspots_not_plate_ownership():
    config = GeologyConfig(plates=PlateConfig(growth_method="dijkstra"))
    baseline = _generate(config)
    changed = _generate(
        replace(
            config,
            hotspots=replace(
                config.hotspots,
                potential=NoiseConfig(octaves=1, base_frequency=2.0),
            ),
        )
    )

    np.testing.assert_array_equal(baseline.plate_ids, changed.plate_ids)
    assert not np.array_equal(baseline.hotspots.potential, changed.hotspots.potential)
    assert not np.array_equal(
        baseline.hotspots.seed_indices, changed.hotspots.seed_indices
    )


def test_zero_hotspot_count_returns_empty_readonly_arrays():
    mesh = _mesh()
    plate_ids = np.zeros(len(mesh.vertices), dtype=np.int64)
    empty = _hotspots(
        mesh,
        HotspotConfig(count=0),
        plate_ids,
        np.empty(0, dtype=np.int64),
    )

    assert empty.potential.shape == (len(mesh.vertices),)
    assert not empty.potential.flags.writeable
    for values in (
        empty.seed_indices,
        empty.plate_ids,
        empty.widths_percent,
        empty.heights_percent,
    ):
        assert values.size == 0
        assert not values.flags.writeable


def _generate(config):
    mesh = _mesh()
    return generate_geology(
        mesh,
        config,
        potential_noise_seed=11,
        plate_seed_rng=np.random.default_rng(12),
        plate_motion_rng=np.random.default_rng(13),
        plate_noise_seed=14,
        crust_noise_seed=15,
        crust_rng=np.random.default_rng(16),
        density_noise_seed=17,
        hotspot_rng=np.random.default_rng(18),
    )


def test_changing_hotspot_config_does_not_change_existing_geology_stages():
    config = GeologyConfig()
    without_hotspots = _generate(
        replace(config, hotspots=replace(config.hotspots, count=0))
    )
    with_hotspots = _generate(
        replace(config, hotspots=replace(config.hotspots, count=4))
    )

    for name in (
        "seed_indices",
        "plate_ids",
        "plate_rotation",
        "plate_velocity",
        "boundary_edge_indices",
        "boundary_convergence",
        "boundary_divergence",
        "boundary_shear",
    ):
        np.testing.assert_array_equal(
            getattr(with_hotspots, name), getattr(without_hotspots, name)
        )
    np.testing.assert_array_equal(
        with_hotspots.crust.region_ids, without_hotspots.crust.region_ids
    )
    np.testing.assert_array_equal(
        with_hotspots.crust.effective_density, without_hotspots.crust.effective_density
    )
    np.testing.assert_array_equal(
        with_hotspots.crust.density_anomaly, without_hotspots.crust.density_anomaly
    )
