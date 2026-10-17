from dataclasses import replace
import heapq

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.elevation.config import (
    CollisionConfig,
    DeformationConfig,
    DivergenceConfig,
    ElevationConfig,
    SubductionConfig,
    TransformConfig,
)
from src.worldgen.elevation.deformation import tectonic_relief
from src.worldgen.elevation.generate import generate_elevation
from src.worldgen.elevation.profiles import (
    divergent_profile,
    divergent_response,
    subduction_profile,
)


def _relief(
    world,
    geology,
    radius_m=None,
    *,
    width_percent=1.5,
    height_percent=0.03,
    divergence_width_percent=1.5,
    divergence_height_percent=0.03,
    transform_width_percent=8.0,
    transform_height_percent=0.0,
    arc_variation=None,
    **crest_settings,
):
    config = DeformationConfig(
        collision=CollisionConfig(
            width_percent=width_percent,
            height_percent=height_percent,
            crest_height_multiplier=crest_settings.get("crest_height_multiplier", 2.0),
        ),
        subduction=SubductionConfig(
            width_percent=width_percent, height_percent=height_percent
        ),
        divergence=DivergenceConfig(
            width_percent=divergence_width_percent,
            height_percent=divergence_height_percent,
        ),
        transform=TransformConfig(
            width_percent=transform_width_percent,
            height_percent=transform_height_percent,
        ),
    )
    return tectonic_relief(
        world.mesh,
        config,
        world.radius_m if radius_m is None else radius_m,
        crust=geology.crust.continental_mask,
        plate_ids=geology.plate_ids,
        boundary_edge_indices=geology.boundary_edge_indices,
        boundary_sections=geology.boundary_sections,
        boundary_convergence=geology.boundary_convergence,
        boundary_divergence=geology.boundary_divergence,
        boundary_shear=geology.boundary_shear,
        arc_variation=(
            np.ones(len(world.mesh.vertices))
            if arc_variation is None
            else arc_variation
        ),
    )


def _source_distance(world, source_edge, target, plate, *, initial, lengths):
    """Shortest same-plate distance from an edge's half-length source."""
    distances = {
        int(vertex): initial
        for vertex in source_edge
        if world.geology.plate_ids[vertex] == plate
    }
    queue = [(distance, vertex) for vertex, distance in distances.items()]
    heapq.heapify(queue)
    while queue:
        distance, vertex = heapq.heappop(queue)
        if distance != distances[vertex]:
            continue
        if vertex == target:
            return distance
        start, end = world.mesh.neighbor_offsets[vertex : vertex + 2]
        for neighbor_value in world.mesh.neighbor_indices[start:end]:
            neighbor = int(neighbor_value)
            if (
                world.geology.plate_ids[neighbor] != plate
                or world.geology.crust.continental_mask[neighbor]
            ):
                continue
            edge = int(
                np.flatnonzero(
                    np.all(
                        world.mesh.edges == np.sort([vertex, neighbor]),
                        axis=1,
                    )
                )[0]
            )
            candidate = distance + float(lengths[edge])
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))
    return float("inf")


def _motion_geology(
    world,
    section_id: int,
    motion: float,
    *,
    divergent: bool = False,
    shear: float | None = None,
):
    geology = world.geology
    convergence = np.zeros_like(geology.boundary_convergence)
    divergence = np.zeros_like(geology.boundary_divergence)
    boundary_shear = np.zeros_like(geology.boundary_shear)
    selected = int(
        np.flatnonzero(geology.boundary_sections.edge_section_ids == section_id)[0]
    )
    if divergent:
        divergence[selected] = motion
    else:
        convergence[selected] = motion
    if shear is not None:
        boundary_shear[selected] = shear
    return replace(
        geology,
        boundary_convergence=convergence,
        boundary_divergence=divergence,
        boundary_shear=boundary_shear,
    ), selected


def _world():
    return generate_world(WorldgenConfig(seed=808, subdivision_frequency=10))


def test_convergent_continental_collision_uplifts_both_sides():
    world = _world()
    sections = world.geology.boundary_sections
    collision = int(np.flatnonzero(np.all(sections.continental_sides, axis=1))[0])
    geology, selected = _motion_geology(world, collision, 1.0)
    relief = _relief(world, geology)
    edge = world.mesh.edges[geology.boundary_edge_indices[selected]]
    assert np.all(relief[edge] > 0.0)


def test_crest_raises_collision_center_without_widening_broad_uplift():
    world = generate_world(WorldgenConfig(seed=808, subdivision_frequency=40))
    sections = world.geology.boundary_sections
    collision = int(np.flatnonzero(np.all(sections.continental_sides, axis=1))[0])
    geology, selected = _motion_geology(world, collision, 1.0)
    broad = _relief(world, geology, crest_height_multiplier=0.0)
    crested = _relief(world, geology)
    edge = world.mesh.edges[geology.boundary_edge_indices[selected]]
    assert np.all(crested[edge] > broad[edge])
    assert np.all(crested >= broad)
    np.testing.assert_array_equal(crested > 0.0, broad > 0.0)
    outer_belt = (broad > 0.0) & (broad < 0.5 * 0.03 * world.radius_m / 100.0)
    assert np.any(outer_belt)
    np.testing.assert_array_equal(crested[outer_belt], broad[outer_belt])


def test_crest_does_not_change_subduction_trenches_or_divergent_relief():
    world = _world()
    sections = world.geology.boundary_sections
    mixed = int(
        np.flatnonzero(
            sections.continental_sides[:, 0] != sections.continental_sides[:, 1]
        )[0]
    )
    for divergent in (False, True):
        geology, _ = _motion_geology(world, mixed, 1.0, divergent=divergent)
        broad = _relief(world, geology, crest_height_multiplier=0.0)
        crested = _relief(world, geology)
        np.testing.assert_array_equal(crested[broad < 0.0], broad[broad < 0.0])
        if divergent:
            np.testing.assert_array_equal(crested, broad)


def test_divergence_rifts_continents_and_builds_oceanic_ridges():
    world = generate_world(WorldgenConfig(seed=808, subdivision_frequency=40))
    sections = world.geology.boundary_sections
    for continental_sides, expected_sign in ((True, -1.0), (False, 1.0)):
        section_id = int(
            np.flatnonzero(
                np.all(sections.continental_sides == continental_sides, axis=1)
            )[0]
        )
        geology, selected = _motion_geology(world, section_id, 1.0, divergent=True)
        relief = _relief(world, geology)
        edge = world.mesh.edges[geology.boundary_edge_indices[selected]]
        assert np.all(relief[edge] * expected_sign > 0.0)

    mixed = int(
        np.flatnonzero(
            sections.continental_sides[:, 0] != sections.continental_sides[:, 1]
        )[0]
    )
    geology, selected = _motion_geology(world, mixed, 1.0, divergent=True)
    relief = _relief(world, geology)
    edge = world.mesh.edges[geology.boundary_edge_indices[selected]]
    for side, plate in enumerate(sections.plate_pairs[mixed]):
        vertex = next(int(v) for v in edge if geology.plate_ids[v] == plate)
        expected_sign = divergent_response(
            bool(sections.continental_sides[mixed, side])
        )
        assert relief[vertex] * expected_sign > 0.0
    np.testing.assert_allclose(_relief(world, geology, world.radius_m * 2), relief * 2)


def test_transform_restraining_and_releasing_relief_acts_on_both_boundary_sides():
    world = _world()
    sections = world.geology.boundary_sections
    collision = int(np.flatnonzero(np.all(sections.continental_sides, axis=1))[0])
    for motion, shear, sign in ((1.0, 1.0, 1.0), (-1.0, 1.0, -1.0)):
        geology, selected = _motion_geology(world, collision, motion, shear=shear)
        relief = _relief(
            world,
            geology,
            width_percent=0.0,
            divergence_width_percent=0.0,
            transform_height_percent=0.05,
            transform_width_percent=8.0,
        )
        edge = world.mesh.edges[geology.boundary_edge_indices[selected]]
        assert np.all(relief[edge] * sign > 0.0)


def test_transform_requires_both_normal_motion_and_shear():
    world = _world()
    collision = int(
        np.flatnonzero(
            np.all(world.geology.boundary_sections.continental_sides, axis=1)
        )[0]
    )
    for motion, shear in ((0.0, 1.0), (1.0, 0.0)):
        geology, _ = _motion_geology(world, collision, motion, shear=shear)
        relief = _relief(
            world,
            geology,
            width_percent=0.0,
            divergence_width_percent=0.0,
            transform_height_percent=0.05,
            transform_width_percent=8.0,
        )
        np.testing.assert_array_equal(relief, np.zeros(len(world.mesh.vertices)))


def test_transform_strength_scales_without_world_max_normalization():
    world = _world()
    collision = int(
        np.flatnonzero(
            np.all(world.geology.boundary_sections.continental_sides, axis=1)
        )[0]
    )
    first, selected = _motion_geology(world, collision, 1.0, shear=1.0)
    second, _ = _motion_geology(world, collision, 2.0, shear=1.0)
    kwargs = dict(
        width_percent=0.0,
        divergence_width_percent=0.0,
        transform_height_percent=0.05,
        transform_width_percent=8.0,
    )
    first_relief = _relief(world, first, **kwargs)
    second_relief = _relief(world, second, **kwargs)
    edge = world.mesh.edges[first.boundary_edge_indices[selected]]
    np.testing.assert_allclose(second_relief[edge], first_relief[edge] * (4.0 / 3.0))


def test_transform_respects_source_plate_and_crust_regions():
    world = _world()
    sections = world.geology.boundary_sections
    collision = int(np.flatnonzero(np.all(sections.continental_sides, axis=1))[0])
    geology, selected = _motion_geology(world, collision, 1.0, shear=1.0)
    relief = _relief(
        world,
        geology,
        width_percent=0.0,
        divergence_width_percent=0.0,
        transform_width_percent=8.0,
        transform_height_percent=0.05,
    )
    edge = world.mesh.edges[geology.boundary_edge_indices[selected]]
    assert np.all(relief[edge] > 0.0)
    source_plates = sections.plate_pairs[collision]
    source_region = (
        np.isin(geology.plate_ids, source_plates) & geology.crust.continental_mask
    )
    np.testing.assert_array_equal(
        relief[~source_region],
        np.zeros(np.count_nonzero(~source_region)),
    )


def test_disabled_transform_preserves_nontransform_relief():
    world = _world()
    collision = int(
        np.flatnonzero(
            np.all(world.geology.boundary_sections.continental_sides, axis=1)
        )[0]
    )
    without_shear, _ = _motion_geology(world, collision, 1.0, shear=0.0)
    with_shear, _ = _motion_geology(world, collision, 1.0, shear=1.0)
    np.testing.assert_array_equal(
        _relief(world, without_shear),
        _relief(world, with_shear),
    )


def test_convergence_settings_do_not_change_divergent_relief():
    world = _world()
    sections = world.geology.boundary_sections
    section_id = int(np.flatnonzero(np.all(~sections.continental_sides, axis=1))[0])
    geology, _ = _motion_geology(world, section_id, 1.0, divergent=True)

    baseline = _relief(world, geology, width_percent=1.5, height_percent=0.03)
    changed_convergence = _relief(world, geology, width_percent=8.0, height_percent=0.5)

    np.testing.assert_array_equal(changed_convergence, baseline)


def test_divergence_settings_do_not_change_convergent_relief():
    world = _world()
    sections = world.geology.boundary_sections
    section_id = int(np.flatnonzero(np.all(sections.continental_sides, axis=1))[0])
    geology, _ = _motion_geology(world, section_id, 1.0)

    baseline = _relief(
        world, geology, divergence_width_percent=1.5, divergence_height_percent=0.03
    )
    changed_divergence = _relief(
        world, geology, divergence_width_percent=8.0, divergence_height_percent=0.5
    )

    np.testing.assert_array_equal(changed_divergence, baseline)


def test_disabling_either_mechanism_preserves_the_other():
    world = _world()
    sections = world.geology.boundary_sections
    collision = int(np.flatnonzero(np.all(sections.continental_sides, axis=1))[0])
    convergence, _ = _motion_geology(world, collision, 1.0)
    convergence_only = _relief(world, convergence, divergence_width_percent=0.0)
    assert np.any(convergence_only != 0.0)

    ridge = int(np.flatnonzero(np.all(~sections.continental_sides, axis=1))[0])
    divergence, _ = _motion_geology(world, ridge, 1.0, divergent=True)
    divergence_only = _relief(world, divergence, width_percent=0.0)
    assert np.any(divergence_only != 0.0)


def test_divergent_height_scales_relief_and_width_changes_support():
    world = _world()
    sections = world.geology.boundary_sections
    section_id = int(np.flatnonzero(np.all(~sections.continental_sides, axis=1))[0])
    geology, _ = _motion_geology(world, section_id, 1.0, divergent=True)

    baseline = _relief(world, geology)
    doubled = _relief(world, geology, divergence_height_percent=0.06)
    wider = _relief(world, geology, divergence_width_percent=3.0)

    np.testing.assert_allclose(doubled, baseline * 2.0)
    assert np.count_nonzero(wider) > np.count_nonzero(baseline)


def test_divergent_profiles_have_axial_flank_and_compact_outer_support():
    width = 4.0
    for continental, axis_sign in ((False, 1.0), (True, -1.0)):
        axis = divergent_profile(0.0, width, continental)
        flank = divergent_profile(width * 0.5, width, continental)
        outside = divergent_profile(width, width, continental)
        beyond = divergent_profile(width * 1.1, width, continental)
        assert axis * axis_sign > 0.0
        assert flank > 0.0
        assert outside == 0.0
        assert beyond == 0.0

    assert divergent_profile(0.0, width, False, axial_depth_multiplier=0.0) == 1.0
    assert divergent_profile(0.0, width, False) < divergent_profile(
        width * 0.1, width, False
    )


def test_nearest_divergent_source_prevents_farther_oceanic_flanks_filling_axis():
    world = generate_world(WorldgenConfig(seed=808, subdivision_frequency=40))
    sections = world.geology.boundary_sections
    candidates = np.flatnonzero(np.all(~sections.continental_sides, axis=1))
    section_id = next(
        int(section)
        for section in candidates
        if np.count_nonzero(sections.edge_section_ids == section) > 1
    )
    section_edges = np.flatnonzero(sections.edge_section_ids == section_id)
    selected = int(section_edges[0])
    primary_edge = world.mesh.edges[world.geology.boundary_edge_indices[selected]]
    primary_edge_index = int(world.geology.boundary_edge_indices[selected])
    target = int(primary_edge[0])
    plate = int(world.geology.plate_ids[target])
    lengths = world.mesh.edge_lengths_percent
    primary_distance = float(lengths[primary_edge_index]) * 0.5
    secondary = next(
        int(index)
        for index in section_edges[1:]
        if not np.any(
            np.isin(
                world.mesh.edges[world.geology.boundary_edge_indices[index]],
                primary_edge,
            )
        )
        and (
            (
                secondary_distance := _source_distance(
                    world,
                    world.mesh.edges[world.geology.boundary_edge_indices[index]],
                    target,
                    plate,
                    initial=float(lengths[world.geology.boundary_edge_indices[index]])
                    * 0.5,
                    lengths=lengths,
                )
            )
            < 4.0
        )
        and divergent_profile(secondary_distance, 4.0, False)
        > divergent_profile(primary_distance, 4.0, False)
    )
    baseline, _ = _motion_geology(world, section_id, 1.0, divergent=True)
    baseline_relief = _relief(world, baseline, divergence_width_percent=4.0)
    divergence = np.zeros_like(baseline.boundary_divergence)
    divergence[selected] = 1.0
    divergence[secondary] = 1.0
    crowded = replace(baseline, boundary_divergence=divergence)
    crowded_relief = _relief(world, crowded, divergence_width_percent=4.0)
    np.testing.assert_allclose(
        crowded_relief[primary_edge], baseline_relief[primary_edge]
    )
    expected = (
        world.radius_m
        * 0.03
        / 100.0
        * divergent_profile(
            primary_distance,
            4.0,
            False,
        )
    )
    np.testing.assert_allclose(baseline_relief[primary_edge], expected)
    np.testing.assert_allclose(crowded_relief[primary_edge], expected)


def test_subduction_profiles_trench_arc_forearc_and_compact_support():
    width = 4.0
    trench = subduction_profile(0.0, width)
    forearc = subduction_profile(width * 0.2, width)
    arc = subduction_profile(width * 0.25, width)
    outside = subduction_profile(width, width)
    beyond = subduction_profile(width * 1.1, width)
    assert trench < 0.0
    assert forearc < arc
    assert arc > 0.0
    assert outside == 0.0
    assert beyond == 0.0
    assert subduction_profile(-width, width) == 0.0


def test_subduction_trench_is_continuous_from_both_sides_despite_arc_variation():
    for width in (1.0, 4.0):
        for arc_width in (0.2, 0.4):
            for variation in (0.0, 1.0, 2.5):
                values = [
                    subduction_profile(
                        distance * width,
                        width,
                        arc_width_fraction=arc_width,
                        arc_variation=variation,
                    )
                    for distance in (-1e-7, 0.0, 1e-7)
                ]
                np.testing.assert_allclose(values, [-1.0, -1.0, -1.0], atol=1e-10)


def test_arc_variation_preserves_trench_and_forearc_but_changes_arc_peak():
    width = 4.0
    for distance in (-0.1, 0.0, 0.025):
        assert subduction_profile(distance * width, width, arc_variation=0.0) == (
            subduction_profile(distance * width, width, arc_variation=2.0)
        )
    assert subduction_profile(width * 0.25, width, arc_variation=0.0) == 0.0
    np.testing.assert_allclose(
        subduction_profile(width * 0.25, width, arc_variation=2.0),
        2.0 * subduction_profile(width * 0.25, width),
    )
    forearc = [subduction_profile(d * width, width) for d in np.linspace(0, 0.25, 51)]
    assert np.all(np.diff(forearc) >= 0.0)


def test_arc_variation_changes_only_overriding_subduction_relief():
    world = generate_world(WorldgenConfig(seed=808, subdivision_frequency=40))
    sections = world.geology.boundary_sections
    mixed = np.flatnonzero(
        sections.continental_sides[:, 0] != sections.continental_sides[:, 1]
    )
    section_id = next(
        int(i)
        for i in mixed
        if sections.subducting_plate_ids[i] in sections.plate_pairs[i]
    )
    geology, selected = _motion_geology(world, section_id, 1.0)
    baseline = _relief(world, geology, width_percent=8.0)
    varied = _relief(
        world,
        geology,
        width_percent=8.0,
        arc_variation=np.zeros(len(world.mesh.vertices)),
    )
    edge = world.mesh.edges[geology.boundary_edge_indices[selected]]
    subducting = int(sections.subducting_plate_ids[section_id])
    trench_vertex = next(int(v) for v in edge if geology.plate_ids[v] == subducting)
    assert varied[trench_vertex] == baseline[trench_vertex]
    assert np.all(baseline[edge] < 0.0)
    np.testing.assert_array_equal(varied[edge], baseline[edge])
    assert np.any(varied != baseline)


def test_overlapping_duplicate_sources_are_order_invariant_and_radius_scaled():
    world = _world()
    sections = world.geology.boundary_sections
    section_id = int(np.flatnonzero(np.all(sections.continental_sides, axis=1))[0])
    geology, selected = _motion_geology(world, section_id, 1.0)
    baseline = _relief(world, geology)
    doubled_radius = _relief(world, geology, world.radius_m * 2.0)

    np.testing.assert_allclose(doubled_radius, baseline * 2.0)

    edge_ids = np.append(
        geology.boundary_edge_indices, geology.boundary_edge_indices[selected]
    )
    section_ids = np.append(
        geology.boundary_sections.edge_section_ids,
        geology.boundary_sections.edge_section_ids[selected],
    )
    convergence = np.append(
        geology.boundary_convergence, geology.boundary_convergence[selected]
    )
    duplicated = replace(
        geology,
        boundary_edge_indices=edge_ids,
        boundary_convergence=convergence,
        boundary_divergence=np.append(geology.boundary_divergence, 0.0),
        boundary_sections=replace(
            geology.boundary_sections, edge_section_ids=section_ids
        ),
    )
    duplicate_relief = _relief(world, duplicated)
    np.testing.assert_allclose(duplicate_relief, baseline)


def test_final_land_mask_uses_combined_elevation_and_ranges_cover_relief():
    world = _world()
    default_config = ElevationConfig()
    config = replace(
        default_config,
        deformation=replace(
            default_config.deformation,
            collision=replace(
                default_config.deformation.collision,
                width_percent=2.5,
                height_percent=0.15,
            ),
            divergence=replace(
                default_config.deformation.divergence,
                width_percent=1.0,
                height_percent=0.075,
            ),
        ),
    )
    terrain = generate_elevation(
        world.mesh,
        config,
        world.radius_m,
        crust=world.geology.crust,
        plate_ids=world.geology.plate_ids,
        boundary_edge_indices=world.geology.boundary_edge_indices,
        boundary_sections=world.geology.boundary_sections,
        boundary_convergence=world.geology.boundary_convergence,
        boundary_divergence=world.geology.boundary_divergence,
        boundary_shear=world.geology.boundary_shear,
        noise_seeds=(1, 2, 3),
        arc_variation=np.ones(len(world.mesh.vertices)),
        volcano_sites=world.geology.volcanism.sites,
        hotspots=world.geology.hotspots,
    )
    np.testing.assert_array_equal(
        terrain.elevation,
        terrain.base_elevation + terrain.tectonic_relief + terrain.volcanic_relief,
    )
    np.testing.assert_array_equal(terrain.land_mask, terrain.elevation >= 0.0)
    assert terrain.elevation_range_m[0] <= terrain.elevation.min()
    assert terrain.elevation_range_m[1] >= terrain.elevation.max()
    assert terrain.elevation_range_m[1] >= (
        terrain.base_elevation_range_m[1] + terrain.volcanic_relief.max()
    )
    assert terrain.base_elevation_range_m[0] <= terrain.base_elevation.min()
    assert terrain.base_elevation_range_m[1] >= terrain.base_elevation.max()


def test_zero_motion_produces_no_tectonic_relief():
    world = _world()
    geology = replace(
        world.geology,
        boundary_convergence=np.zeros_like(world.geology.boundary_convergence),
        boundary_divergence=np.zeros_like(world.geology.boundary_divergence),
        boundary_shear=np.zeros_like(world.geology.boundary_shear),
    )
    relief = _relief(world, geology)
    np.testing.assert_array_equal(relief, np.zeros(len(world.mesh.vertices)))


def test_arc_noise_config_is_deterministic_and_independent_of_geology_streams():
    config = WorldgenConfig(seed=808, subdivision_frequency=40)
    baseline = generate_world(config)
    repeated = generate_world(config)
    np.testing.assert_array_equal(
        baseline.elevation.tectonic_relief,
        repeated.elevation.tectonic_relief,
    )

    sections = baseline.geology.boundary_sections
    section_id = next(
        int(i)
        for i in np.flatnonzero(sections.subducting_plate_ids >= 0)
        if baseline.geology.boundary_convergence[
            np.flatnonzero(sections.edge_section_ids == i)[0]
        ]
        > 0.0
    )
    overriding_plate = next(
        int(plate)
        for plate in sections.plate_pairs[section_id]
        if plate != sections.subducting_plate_ids[section_id]
    )
    overriding_vertices = baseline.geology.plate_ids == overriding_plate
    deformation = config.elevation.deformation
    for changed_deformation in (
        replace(
            deformation,
            subduction=replace(deformation.subduction, arc_variation_strength=0.0),
        ),
        replace(
            deformation,
            subduction=replace(
                deformation.subduction,
                arc_noise_frequency=deformation.subduction.arc_noise_frequency * 2,
            ),
        ),
    ):
        changed_config = replace(
            config,
            elevation=replace(
                config.elevation,
                deformation=changed_deformation,
            ),
        )
        changed = generate_world(changed_config)
        np.testing.assert_array_equal(
            changed.geology.plate_ids, baseline.geology.plate_ids
        )
        np.testing.assert_array_equal(
            changed.geology.crust.region_ids, baseline.geology.crust.region_ids
        )
        for field in (
            "plate_rotation",
            "plate_velocity",
            "boundary_convergence",
            "boundary_divergence",
            "boundary_shear",
        ):
            np.testing.assert_array_equal(
                getattr(changed.geology, field), getattr(baseline.geology, field)
            )
        np.testing.assert_array_equal(
            changed.elevation.base_elevation,
            baseline.elevation.base_elevation,
        )
        difference = (
            changed.elevation.tectonic_relief - baseline.elevation.tectonic_relief
        )
        assert np.any(difference[overriding_vertices] != 0.0)
        assert np.any(baseline.elevation.tectonic_relief[overriding_vertices] > 0.0)
