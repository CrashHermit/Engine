from dataclasses import replace

import numpy as np

from src.worldgen.climate.generate import generate_climate_field
from src.worldgen.config import WorldgenConfig
from src.worldgen.relief.generate import generate_source_relief_field
from src.worldgen.relief.variation import TerrainVariationField
from src.worldgen.relief.volcanism import VolcanicField
from src.worldgen.relief.impact import generate_impact_field
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField
from src.worldgen.geology.generate import generate_geology_field
from src.worldgen.geology.subduction_preference import overriding_weights
from src.worldgen.world import WorldField


_AMPLITUDE = 0.7


def _world():
    def shear(plane, iteration, axis, frequency):
        return plane[:, 0] ** 2 if axis == 0 else np.zeros(len(plane))

    def shear_gradient(plane, iteration, axis, frequency):
        gradient = np.zeros((len(plane), 2))
        if axis == 0:
            gradient[:, 0] = 2 * plane[:, 0]
        return shear(plane, iteration, axis, frequency), gradient

    def shear_hessian(plane, iteration, axis, frequency):
        values, gradient = shear_gradient(plane, iteration, axis, frequency)
        hessian = np.zeros((len(plane), 2, 2))
        if axis == 0:
            hessian[:, 0, 0] = 2.0
        return values, gradient, hessian

    warp = ShearWarpField(
        ShearWarpConfig(iterations=1, amplitude=_AMPLITUDE),
        shear,
        shear_gradient,
        shear_hessian,
    )
    partition = VoronoiField3D(np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
    config = WorldgenConfig(seed=811)
    geology_config = replace(
        config.geology,
        plates=replace(config.geology.plates, plate_count=2),
        crust=replace(config.geology.crust, continental_seeds=1, oceanic_seeds=1),
        polarity=replace(config.geology.polarity, preference_scale=2.0),
    )
    geology = generate_geology_field(
        geology_config,
        regions=WarpedVoronoiField(warp, partition),
        crust_rng=np.random.default_rng(311),
        motion_rng=np.random.default_rng(413),
        polarity_rng=np.random.default_rng(519),
        density_noise_seed=43,
    )
    source_relief = generate_source_relief_field(
        config.relief, geology=geology, noise_seeds=(31, 37, 41)
    )
    return WorldField(
        geology,
        source_relief,
        TerrainVariationField(config.relief.variation, noise_seed=53),
        warp,
        generate_impact_field(config.relief.impacts, seed=59),
        VolcanicField(
            sample_relief_inputs=geology.sample_relief_inputs,
            sample_relief_inputs_with_gradient=geology.sample_relief_inputs_with_gradient,
            noise_seed=61,
            warp=warp,
            config=config.relief.volcanism,
        ),
        generate_climate_field(config.climate, config.planet.rotation_axis),
    )


def _positions():
    return np.array([[0.02, 0.3, 0.1], [-0.04, 0.6, -0.2], [0.06, -0.4, 0.3]])


def test_generated_interactions_use_transported_vectors_and_normals_not_source_motion():
    field = _world()
    source = _positions()
    world = field.warp.inverse(source)
    raw = field.geology.motion.vectors.source.sample(source)
    sample = field.geology.sample_source(source)
    inverse_jacobian = np.broadcast_to(np.eye(3), (len(source), 3, 3)).copy()
    inverse_jacobian[:, 0, 1] = -2 * _AMPLITUDE * source[:, 1]
    expected_vectors = np.einsum("nij,nsj->nsi", inverse_jacobian, raw.vectors)
    expected_normals = np.column_stack(
        (np.ones(len(source)), 2 * _AMPLITUDE * source[:, 1], np.zeros(len(source)))
    )
    expected_normals /= np.linalg.norm(expected_normals, axis=1, keepdims=True)
    relative = expected_vectors[:, 1] - expected_vectors[:, 0]
    expected_opening = np.einsum("ni,ni->n", relative, expected_normals)
    np.testing.assert_allclose(sample.motion.opening, expected_opening, atol=1e-13)
    np.testing.assert_allclose(sample.motion.normals, expected_normals, atol=1e-13)
    source_opening = raw.vectors[:, 1, 0] - raw.vectors[:, 0, 0]
    assert not np.allclose(expected_opening, source_opening)
    np.testing.assert_array_equal(np.sign(expected_opening), np.sign(source_opening))

    preference = np.einsum(
        "nij,nj->ni", inverse_jacobian, field.geology.preference.sample(source)
    )
    expected_polarity = overriding_weights(
        np.einsum("ni,ni->n", preference, expected_normals),
        np.full(len(source), field.geology.context.pair_signs[0, 1]),
        directed=True,
        config=field.geology.context.polarity,
    )
    np.testing.assert_allclose(sample.context.b_overrides_weight, expected_polarity)
    pairs = field.sample_boundary_vectors(world)
    np.testing.assert_allclose(pairs.vectors, expected_vectors, atol=1e-13)
    np.testing.assert_allclose(pairs.normals, expected_normals, atol=1e-13)


def test_generated_motion_and_world_velocity_derivatives_include_nonuniform_transport():
    field = _world()
    source = _positions()
    sampled = field.geology.sample_source_with_gradient(source)
    step = 1e-6
    for name, actual in (
        ("opening", sampled.motion.opening_gradients),
        ("convergence", sampled.motion.convergence_gradients),
        ("divergence", sampled.motion.divergence_gradients),
        ("shear", sampled.motion.shear_gradients),
    ):
        numerical = np.column_stack(
            [
                (
                    getattr(
                        field.geology.sample_source(
                            source + np.eye(3)[axis] * step
                        ).motion,
                        name,
                    )
                    - getattr(
                        field.geology.sample_source(
                            source - np.eye(3)[axis] * step
                        ).motion,
                        name,
                    )
                )
                / (2 * step)
                for axis in range(3)
            ]
        )
        np.testing.assert_allclose(actual, numerical, rtol=2e-6, atol=2e-8)
    for name, actual in (
        ("b_overrides_weight", sampled.context.b_overrides_weight_gradients),
        ("continental_blend", sampled.context.continental_blend_gradients),
    ):
        numerical = np.column_stack(
            [
                (
                    getattr(
                        field.geology.sample_source(
                            source + np.eye(3)[axis] * step
                        ).context,
                        name,
                    )
                    - getattr(
                        field.geology.sample_source(
                            source - np.eye(3)[axis] * step
                        ).context,
                        name,
                    )
                )
                / (2 * step)
                for axis in range(3)
            ]
        )
        np.testing.assert_allclose(actual, numerical, rtol=2e-6, atol=2e-8)
    world = field.warp.inverse(source)
    velocity = field.region_velocity.sample_with_jacobian(world)
    numerical = np.stack(
        [
            (
                field.region_velocity.sample(world + np.eye(3)[axis] * step)
                - field.region_velocity.sample(world - np.eye(3)[axis] * step)
            )
            / (2 * step)
            for axis in range(3)
        ],
        axis=2,
    )
    np.testing.assert_allclose(velocity.jacobians, numerical, rtol=2e-6, atol=2e-8)
    for channel in (field.convergence, field.divergence, field.shear):
        actual = channel.sample_with_gradient(world)
        numerical = np.column_stack(
            [
                (
                    channel.sample(world + np.eye(3)[axis] * step)
                    - channel.sample(world - np.eye(3)[axis] * step)
                )
                / (2 * step)
                for axis in range(3)
            ]
        )
        np.testing.assert_allclose(actual.gradients, numerical, rtol=2e-6, atol=2e-8)
