import numpy as np

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geology.boundary_sections import BoundarySections
from src.worldgen.geology.model import CrustResult, HotspotResult
from src.worldgen.geology.config import VolcanismConfig
from src.worldgen.geology.model import VolcanoSource, VolcanoState
from src.worldgen.geology.volcanism import generate_volcanism


def _fixture():
    mesh = Mesh(*generate_icosphere(12))
    plate_ids = (mesh.vertices[:, 0] >= 0.0).astype(np.int64)
    edges = np.flatnonzero(plate_ids[mesh.edges[:, 0]] != plate_ids[mesh.edges[:, 1]])
    count = len(mesh.vertices)
    boundary_count = len(edges)
    crust = CrustResult(
        region_ids=np.zeros(count, dtype=np.int64),
        seed_indices=np.array([0]),
        continental_regions=np.array([False]),
        continental_mask=np.zeros(count, dtype=bool),
        shaping_field=np.zeros(count),
        effective_density=np.ones(count),
        density_anomaly=np.zeros(count),
        region_effective_density=np.ones(1),
    )
    sections = BoundarySections(
        edge_section_ids=np.zeros(boundary_count, dtype=np.int64),
        plate_pairs=np.array([[0, 1]], dtype=np.int64),
        continental_sides=np.zeros((1, 2), dtype=bool),
        side_effective_density=np.ones((1, 2)),
        subducting_plate_ids=np.array([0], dtype=np.int64),
    )
    hotspots = HotspotResult(
        seed_indices=np.empty(0, dtype=np.int64),
        plate_ids=np.empty(0, dtype=np.int64),
        widths_percent=np.empty(0),
        heights_percent=np.empty(0),
        potential=np.zeros(count),
    )
    return mesh, plate_ids, edges, crust, sections, hotspots


def _generate(config, *, convergence=None, divergence=None, seed=37):
    mesh, plates, edges, crust, sections, hotspots = _fixture()
    return generate_volcanism(
        mesh,
        config,
        hotspots=hotspots,
        crust=crust,
        plate_ids=plates,
        boundary_edge_indices=edges,
        boundary_sections=sections,
        boundary_convergence=(
            np.ones(len(edges)) if convergence is None else convergence
        ),
        boundary_divergence=(
            np.zeros(len(edges)) if divergence is None else divergence
        ),
        rng=np.random.default_rng(seed),
        subduction_width_percent=4.0,
        arc_offset_fraction=0.0,
        arc_width_fraction=0.5,
        divergence_width_percent=2.0,
        axial_width_fraction=0.5,
        arc_variation=np.ones(len(mesh.vertices)),
    )


def test_divergent_and_subduction_fields_respect_support_regions():
    mesh, plates, edges, *_ = _fixture()
    config = VolcanismConfig(supplied_site_count=0, historical_extinct_site_count=0)
    arc = _generate(config)
    assert np.any(arc.subduction_potential > 0.0)
    assert np.all(arc.subduction_potential[plates == 0] == 0.0)

    divergent = _generate(
        config,
        convergence=np.zeros(len(edges)),
        divergence=np.ones(len(edges)),
    )
    assert np.any(divergent.divergence_potential > 0.0)
    assert np.all(divergent.potential >= divergent.divergence_potential)
    assert not divergent.potential.flags.writeable
    assert not divergent.divergence_potential.flags.writeable
    assert len(mesh.vertices) == len(divergent.potential)


def test_extinct_historical_sites_keep_geometry_without_activity():
    config = VolcanismConfig(
        supplied_site_count=4,
        historical_extinct_site_count=3,
        supply_persistence_probability=0.0,
        eruption_probability=1.0,
        min_site_distance=0.0,
    )
    result = _generate(config)
    sites = result.sites
    historical = sites.source_types == VolcanoSource.HISTORICAL
    assert np.count_nonzero(historical) == 3
    assert np.all(sites.states == VolcanoState.EXTINCT)
    assert np.all(sites.supply_strength == 0.0)
    assert np.all(sites.eruption_intensity == 0.0)
    assert np.all(sites.widths_percent[historical] > 0.0)
    assert np.all(sites.heights_percent[historical] > 0.0)
    assert np.all(sites.widths_percent[~historical] == 0.0)
    assert not np.any(result.activity)
    assert np.array_equal(
        result.volcanic_mask, result.potential >= config.potential_threshold
    )
    assert len(np.unique(sites.cell_indices)) == len(sites.cell_indices)


def test_supplied_eruption_and_generation_are_reproducible_and_readonly():
    config = VolcanismConfig(
        supplied_site_count=3,
        historical_extinct_site_count=1,
        supply_persistence_probability=1.0,
        eruption_probability=1.0,
        min_site_distance=0.0,
    )
    first = _generate(config)
    second = _generate(config)
    np.testing.assert_array_equal(first.potential, second.potential)
    np.testing.assert_array_equal(first.activity, second.activity)
    np.testing.assert_array_equal(first.sites.cell_indices, second.sites.cell_indices)
    assert np.all(first.sites.states[:3] == VolcanoState.ERUPTING)
    assert np.all(first.sites.source_types[:3] == VolcanoSource.SUBDUCTION)
    assert np.any(first.activity > 0.0)
    assert np.array_equal(
        first.volcanic_mask, first.potential >= config.potential_threshold
    )
    assert not first.sites.states.flags.writeable


def test_boundary_potential_preserves_motion_scale():
    _, _, edges, *_ = _fixture()
    config = VolcanismConfig(supplied_site_count=0, historical_extinct_site_count=0)
    full = _generate(config, convergence=np.ones(len(edges)))
    half = _generate(config, convergence=np.full(len(edges), 0.5))
    np.testing.assert_allclose(
        half.subduction_potential, full.subduction_potential * 0.5
    )
    stopped = _generate(
        config, convergence=np.zeros(len(edges)), divergence=np.zeros(len(edges))
    )
    assert np.all(stopped.potential == 0.0)


def test_dormant_volcanoes_retain_supply_without_erupting():
    result = _generate(
        VolcanismConfig(
            supplied_site_count=3,
            historical_extinct_site_count=0,
            supply_persistence_probability=1.0,
            eruption_probability=0.0,
            min_site_distance=0.0,
        )
    )
    assert np.all(result.sites.states == VolcanoState.DORMANT)
    assert np.all(result.sites.supply_strength > 0.0)
    assert np.all(result.sites.eruption_intensity == 0.0)
    assert np.all(result.activity == 0.0)
    assert np.any(result.volcanic_mask)
