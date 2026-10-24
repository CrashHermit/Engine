import numpy as np

from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_transport import TransportedBoundaryVectorField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.differential import VectorHessianSample, VectorSample
from src.worldgen.field.motion import RegionRotationField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.voronoi import VoronoiField3D


def _fields(transform):
    partition = VoronoiField3D(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
    regions = RegionInfluenceField(partition, RegionInfluenceConfig(0.8))
    overlap = RegionOverlapField(regions)
    rotation = RegionRotationField(
        partition,
        np.array([[0.2, -0.1, 0.3], [-0.1, 0.4, 0.2]]),
    )
    raw = BoundaryVectorField(
        overlap, rotation.sample_regions, rotation.sample_regions_with_jacobian
    )
    transported = TransportedBoundaryVectorField(raw, transform[0], transform[1])
    return BoundaryMotionField(raw), BoundaryMotionField(transported), transported


def _identity(points):
    points = np.asarray(points, dtype=np.float64)
    jacobians = np.broadcast_to(np.eye(3), (len(points), 3, 3)).copy()
    return VectorSample(points, jacobians)


def _identity_hessian(points):
    mapping = _identity(points)
    return VectorHessianSample(
        mapping.values, mapping.jacobians, np.zeros((len(points), 3, 3, 3))
    )


def _quadratic(points):
    points = np.asarray(points, dtype=np.float64)
    jacobians = np.broadcast_to(np.eye(3), (len(points), 3, 3)).copy()
    jacobians[:, 0, 1] = 0.4 * points[:, 1]
    return VectorSample(points, jacobians)


def _quadratic_hessian(points):
    mapping = _quadratic(points)
    hessians = np.zeros((len(points), 3, 3, 3), dtype=np.float64)
    hessians[:, 0, 1, 1] = 0.4
    return VectorHessianSample(mapping.values, mapping.jacobians, hessians)


def test_identity_transport_reproduces_raw_pairs_and_motion():
    raw, transported, field = _fields((_identity, _identity_hessian))
    points = np.array([[0.03, 0.12, -0.2], [0.0, 0.0, 0.0], [3.0, 0, 0]])
    raw_sample = raw.vectors.sample(points)
    mapped_sample = transported.vectors.sample(points)
    for name in (
        "query_indices",
        "region_pairs",
        "influence",
        "plane_distance",
        "normals",
        "vectors",
    ):
        np.testing.assert_array_equal(
            getattr(raw_sample, name), getattr(mapped_sample, name)
        )
    raw_motion = raw.sample_with_gradient(points)
    mapped_motion = transported.sample_with_gradient(points)
    np.testing.assert_allclose(
        raw_motion.opening_gradients, mapped_motion.opening_gradients
    )
    np.testing.assert_allclose(
        raw_motion.shear_gradients, mapped_motion.shear_gradients
    )
    empty = field.sample_with_jacobian(np.empty((0, 3)))
    assert empty.sample.vectors.shape == (0, 2, 3)
    assert empty.normal_jacobians.shape == (0, 3, 3)


def test_affine_transport_maps_vectors_and_covectors_with_invariant_opening_sign():
    matrix = np.array([[1.4, 0.25, 0.0], [0.0, 0.8, 0.1], [0.0, 0.0, 1.2]])

    def affine(points):
        points = np.asarray(points, dtype=np.float64)
        values = points @ matrix.T
        jacobians = np.broadcast_to(matrix, (len(points), 3, 3)).copy()
        return VectorSample(values, jacobians)

    def affine_hessian(points):
        mapping = affine(points)
        return VectorHessianSample(
            mapping.values, mapping.jacobians, np.zeros((len(points), 3, 3, 3))
        )

    raw, transported, _ = _fields((affine, affine_hessian))
    points = np.array([[0.03, 0.12, -0.2]])
    raw_pairs = raw.vectors.sample(points)
    world_pairs = transported.vectors.sample(points)
    expected_vectors = np.einsum("ab,nib->nia", matrix, raw_pairs.vectors)
    expected_normals = np.linalg.solve(matrix.T, raw_pairs.normals.T).T
    expected_normals /= np.linalg.norm(expected_normals, axis=1, keepdims=True)
    np.testing.assert_allclose(world_pairs.vectors, expected_vectors)
    np.testing.assert_allclose(world_pairs.normals, expected_normals)
    raw_opening = np.sum(
        (raw_pairs.vectors[:, 1] - raw_pairs.vectors[:, 0]) * raw_pairs.normals,
        axis=1,
    )
    world_opening = np.sum(
        (world_pairs.vectors[:, 1] - world_pairs.vectors[:, 0]) * world_pairs.normals,
        axis=1,
    )
    np.testing.assert_array_equal(np.sign(raw_opening), np.sign(world_opening))


def test_nonuniform_transport_includes_normal_jacobians_in_motion_gradients():
    raw, transported, _ = _fields((_quadratic, _quadratic_hessian))
    point = np.array([[0.03, 0.12, -0.2]])
    source = raw.sample(point)
    world = transported.sample(point)
    np.testing.assert_array_equal(np.sign(source.opening), np.sign(world.opening))
    derivative = transported.sample_with_gradient(point)
    assert np.linalg.norm(derivative.normal_jacobians) > 0.0

    step = 1e-6
    for component, analytic in (
        ("opening", derivative.opening_gradients),
        ("shear", derivative.shear_gradients),
    ):
        numerical = np.empty_like(analytic)
        for axis in range(3):
            offset = np.zeros_like(point)
            offset[0, axis] = step
            positive = getattr(transported.sample(point + offset), component)
            negative = getattr(transported.sample(point - offset), component)
            numerical[:, axis] = (positive - negative) / (2.0 * step)
        np.testing.assert_allclose(analytic, numerical, rtol=2e-5, atol=2e-7)


def test_transport_preserves_all_junction_pairs_without_caller_region_ids():
    seeds = np.array([[-1.0, 0, 0], [1.0, 0, 0], [0.0, 2.0, 0]])
    partition = VoronoiField3D(seeds)
    regions = RegionInfluenceField(partition, RegionInfluenceConfig(0.5))
    overlap = RegionOverlapField(regions)
    rotation = RegionRotationField(
        partition,
        np.array([[0.0, 0.0, 0.0], [-1.0, 1.0, 0.0], [0.0, 0.0, 0.0]]),
    )
    raw = BoundaryVectorField(
        overlap, rotation.sample_regions, rotation.sample_regions_with_jacobian
    )
    field = TransportedBoundaryVectorField(raw, _identity, _identity_hessian)
    point = np.array([[0.0, 0.75, 0.0]])
    raw_sample = raw.sample(point)
    transported_sample = field.sample(point)
    np.testing.assert_array_equal(
        transported_sample.region_pairs, np.array([[0, 1], [0, 2], [1, 2]])
    )
    np.testing.assert_array_equal(transported_sample.vectors, raw_sample.vectors)
