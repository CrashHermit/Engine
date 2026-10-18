from dataclasses import replace

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation.config import (
    CollisionConfig,
    DeformationConfig,
    DivergenceConfig,
    SubductionConfig,
    TransformConfig,
)
from src.worldgen.elevation.deformation import TectonicField
from src.worldgen.elevation.profiles import (
    collision_profile,
    divergent_profile,
    subduction_profile,
)
from src.worldgen.elevation.transform import transform_strength
from src.worldgen.generate import generate_world
from src.worldgen.geometry.boundary import BoundaryNetwork


def _world():
    return generate_world(WorldgenConfig(seed=808, subdivision_frequency=10))


def _field(world, config=None):
    geology = world.geology
    boundary = BoundaryNetwork(
        world.mesh, geology.plate_ids, geology.boundary_edge_indices
    )
    return TectonicField(
        world.mesh,
        geology,
        config or DeformationConfig(),
        boundary=boundary,
        arc_noise_seed=413,
    )


def _only_divergence():
    return DeformationConfig(
        collision=CollisionConfig(height_percent=0.0),
        subduction=SubductionConfig(height_percent=0.0),
        divergence=DivergenceConfig(),
        transform=TransformConfig(height_percent=0.0),
    )


def _only_collision():
    return DeformationConfig(
        collision=CollisionConfig(),
        subduction=SubductionConfig(height_percent=0.0),
        divergence=DivergenceConfig(height_percent=0.0),
        transform=TransformConfig(height_percent=0.0),
    )


def _only_subduction():
    return DeformationConfig(
        collision=CollisionConfig(height_percent=0.0),
        subduction=SubductionConfig(),
        divergence=DivergenceConfig(height_percent=0.0),
        transform=TransformConfig(height_percent=0.0),
    )


def _only_transform():
    return DeformationConfig(
        collision=CollisionConfig(height_percent=0.0),
        subduction=SubductionConfig(height_percent=0.0),
        divergence=DivergenceConfig(height_percent=0.0),
        transform=TransformConfig(),
    )


def test_profile_shapes_preserve_crests_trenches_and_axial_valleys():
    broad, crest = collision_profile(0.0, 4.0, 0.2)
    assert broad == 1.0
    assert crest == 1.0
    assert collision_profile(3.5, 4.0, 0.2)[1] == 0.0

    assert subduction_profile(-0.0, 4.0) == subduction_profile(0.0, 4.0)
    assert subduction_profile(-0.0, 4.0) < 0.0
    assert subduction_profile(1.0, 4.0) > 0.0
    assert subduction_profile(4.0, 4.0) == 0.0

    normal_trench = subduction_profile(-0.5, 4.0)
    deep_trench = subduction_profile(-0.5, 4.0, trench_depth_multiplier=4.0)
    np.testing.assert_allclose(deep_trench, normal_trench * 4.0)

    assert divergent_profile(0.0, 4.0, True) < 0.0
    assert divergent_profile(0.0, 4.0, False) > 0.0
    assert divergent_profile(4.0, 4.0, False) == 0.0


def test_field_is_batch_permutation_invariant_and_handles_empty_batches():
    world = _world()
    field = _field(world)
    vertices = world.mesh.vertices[:24]
    expected = field.sample(vertices, world.radius_m)
    order = np.array(
        [
            8,
            2,
            15,
            1,
            23,
            0,
            19,
            4,
            7,
            3,
            12,
            11,
            5,
            10,
            6,
            13,
            14,
            9,
            16,
            17,
            18,
            20,
            21,
            22,
        ]
    )
    np.testing.assert_array_equal(
        field.sample(vertices[order], world.radius_m), expected[order]
    )
    assert field.sample(np.empty((0, 3)), world.radius_m).shape == (0,)


def test_field_scales_with_radius_and_zero_motion_is_zero():
    world = _world()
    field = _field(world)
    points = world.mesh.vertices[:20]
    relief = field.sample(points, world.radius_m)
    np.testing.assert_allclose(
        field.sample(points, world.radius_m * 2.0),
        relief * 2.0,
        rtol=1e-12,
        atol=1e-8,
    )

    geology = world.geology
    still = replace(
        geology,
        plate_rotation=np.zeros_like(geology.plate_rotation),
        boundary_convergence=np.zeros_like(geology.boundary_convergence),
        boundary_divergence=np.zeros_like(geology.boundary_divergence),
        boundary_shear=np.zeros_like(geology.boundary_shear),
    )
    boundary = BoundaryNetwork(world.mesh, still.plate_ids, still.boundary_edge_indices)
    still_field = TectonicField(
        world.mesh, still, DeformationConfig(), boundary=boundary, arc_noise_seed=413
    )
    np.testing.assert_array_equal(still_field.sample(points, world.radius_m), 0.0)


def test_process_fields_preserve_collision_trench_and_transform_intent():
    world = _world()
    geology = world.geology
    sections = geology.boundary_sections
    edge_sections = sections.edge_section_ids
    continental_collision = sections.continental_sides[edge_sections].all(axis=1)
    collision_ids = np.flatnonzero(
        continental_collision & (geology.boundary_convergence > 0.0)
    )
    assert len(collision_ids)
    collision = _field(world, _only_collision())
    collision_midpoint = (
        collision.boundary.starts[collision_ids[0]]
        + collision.boundary.ends[collision_ids[0]]
    )
    collision_midpoint /= np.linalg.norm(collision_midpoint)
    assert collision.sample(collision_midpoint[None, :], world.radius_m)[0] > 0.0

    subduction_ids = np.flatnonzero(
        (sections.subducting_plate_ids[edge_sections] >= 0)
        & (geology.boundary_convergence > 0.0)
    )
    assert len(subduction_ids)
    subduction = _field(world, _only_subduction())
    trench_midpoint = (
        subduction.boundary.starts[subduction_ids[0]]
        + subduction.boundary.ends[subduction_ids[0]]
    )
    trench_midpoint /= np.linalg.norm(trench_midpoint)
    assert subduction.sample(trench_midpoint[None, :], world.radius_m)[0] < 0.0

    normal = geology.boundary_convergence - geology.boundary_divergence
    transform_ids = np.flatnonzero(
        transform_strength(normal, geology.boundary_shear) != 0.0
    )
    assert len(transform_ids)
    transform = _field(world, _only_transform())
    transform_midpoint = (
        transform.boundary.starts[transform_ids[0]]
        + transform.boundary.ends[transform_ids[0]]
    )
    transform_midpoint /= np.linalg.norm(transform_midpoint)
    assert transform.sample(transform_midpoint[None, :], world.radius_m)[0] != 0.0


def test_subduction_field_uplifts_overriding_side_and_not_descending_side():
    world = _world()
    geology = world.geology
    sections = geology.boundary_sections
    section_ids = sections.edge_section_ids
    selected = int(
        np.flatnonzero(
            (sections.subducting_plate_ids[section_ids] >= 0)
            & (geology.boundary_convergence > 0.0)
        )[0]
    )
    edge_index = int(geology.boundary_edge_indices[selected])
    boundary = BoundaryNetwork(
        world.mesh, geology.plate_ids, np.asarray([edge_index], dtype=np.int64)
    )
    field = TectonicField(
        world.mesh,
        geology,
        _only_subduction(),
        boundary=boundary,
        arc_noise_seed=413,
    )
    midpoint = boundary.starts[0] + boundary.ends[0]
    midpoint /= np.linalg.norm(midpoint)
    normal = np.cross(boundary.starts[0], boundary.ends[0])
    normal /= np.linalg.norm(normal)
    edge_vertices = world.mesh.edges[edge_index]
    positive_side_is_left = np.dot(normal, world.mesh.vertices[edge_vertices[0]]) > 0.0
    descending = int(sections.subducting_plate_ids[section_ids[selected]])
    descending_is_left = int(geology.plate_ids[edge_vertices[0]]) == descending
    positive_side_is_descending = positive_side_is_left == descending_is_left
    offset = (
        _only_subduction().subduction.arc_offset_fraction
        * _only_subduction().subduction.width_percent
        * (2.0 * np.pi / 100.0)
    )
    toward_positive_side = 1.0 if positive_side_is_descending else -1.0
    descending_point = (
        midpoint * np.cos(offset) + normal * np.sin(offset) * toward_positive_side
    )
    overriding_point = (
        midpoint * np.cos(offset) - normal * np.sin(offset) * toward_positive_side
    )
    relief = field.sample(
        np.stack((descending_point, overriding_point)), world.radius_m
    )
    assert relief[0] <= 0.0
    assert relief[1] > 0.0


def test_divergent_field_is_continuous_across_active_arc_and_section_end():
    world = _world()
    selected = int(np.flatnonzero(world.geology.boundary_divergence > 0.0)[0])
    field = _field(world, _only_divergence())
    boundary = field.boundary
    midpoint = boundary.starts[selected] + boundary.ends[selected]
    midpoint /= np.linalg.norm(midpoint)
    normal = np.cross(boundary.starts[selected], boundary.ends[selected])
    normal /= np.linalg.norm(normal)
    offset = 1e-6
    left = midpoint * np.cos(offset) + normal * np.sin(offset)
    right = midpoint * np.cos(offset) - normal * np.sin(offset)
    values = field.sample(np.stack((left, midpoint, right)), world.radius_m)
    assert np.any(values != 0.0)
    assert abs(values[0] - values[2]) < max(1.0, abs(values[1]) * 1e-3)

    section_ids = world.geology.boundary_sections.edge_section_ids
    endpoint = None
    for segment in np.flatnonzero(world.geology.boundary_divergence > 0.0):
        for vertex in boundary.vertex_indices[segment]:
            neighbors = np.flatnonzero(
                np.any(boundary.vertex_indices == vertex, axis=1)
            )
            if np.any(section_ids[neighbors] != section_ids[segment]):
                endpoint = (int(segment), int(vertex))
                break
        if endpoint is not None:
            break
    assert endpoint is not None
    segment, vertex = endpoint
    end = world.mesh.dual_vertices[vertex]
    other = (
        boundary.ends[segment]
        if np.allclose(boundary.starts[segment], end)
        else boundary.starts[segment]
    )
    tangent = other - np.dot(other, end) * end
    tangent /= np.linalg.norm(tangent)
    offset = 1e-7
    inside = end * np.cos(offset) + tangent * np.sin(offset)
    outside = end * np.cos(offset) - tangent * np.sin(offset)
    values = field.sample(np.stack((inside, end, outside)), world.radius_m)
    assert abs(values[0] - values[2]) < max(1.0, abs(values[1]) * 1e-3)


def test_sampling_remains_consistent_across_large_query_partitions():
    world = _world()
    field = _field(world)
    points = np.random.default_rng(701).normal(size=(2051, 3))
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    whole = field.sample(points, world.radius_m)
    split = np.concatenate(
        [
            field.sample(points[:1023], world.radius_m),
            field.sample(points[1023:1025], world.radius_m),
            field.sample(points[1025:2048], world.radius_m),
            field.sample(points[2048:], world.radius_m),
        ]
    )
    np.testing.assert_array_equal(split, whole)
    np.testing.assert_array_equal(
        field.sample(points[::-1].copy(), world.radius_m), whole[::-1]
    )
