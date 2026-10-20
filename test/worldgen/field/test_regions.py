import numpy as np

from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField
from src.worldgen.field.regions import (
    WarpedVoronoiField,
    build_warped_voronoi_field,
)
from src.worldgen.geometry.icosphere import generate_icosphere


def _field(seed: int = 2026):
    return build_warped_voronoi_field(
        12,
        rng=np.random.default_rng(seed),
        noise_seed=seed,
        noise_config=NoiseConfig(
            octaves=2,
            base_frequency=1.1,
            lacunarity=2.0,
            persistence=0.5,
        ),
        warp_config=ShearWarpConfig(
            iterations=2,
            amplitude=0.12,
            lacunarity=1.7,
            gain=0.6,
        ),
    )


def test_region_field_samples_sphere_centers_and_interior_points_directly():
    field = _field()
    vertices, _ = generate_icosphere(4)
    interior = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.25, -0.4, 0.1],
            [-0.7, 0.2, 0.3],
        ]
    )

    surface = field.sample(vertices)
    volume = field.sample(interior)

    assert len(surface.owner_seed_id) == len(vertices)
    assert len(volume.owner_seed_id) == len(interior)
    np.testing.assert_array_equal(
        field.sample(vertices[::7]).owner_seed_id,
        surface.owner_seed_id[::7],
    )


def test_warped_region_field_samples_ownership():
    def translation_shear(plane_positions, iteration, axis, frequency_multiplier):
        return np.full(len(plane_positions), (0.0, 1.0, 0.25)[axis])

    field = WarpedVoronoiField(
        warp=ShearWarpField(
            config=ShearWarpConfig(iterations=1, amplitude=1.0, gain=1.0),
            shear=translation_shear,
        ),
        voronoi=VoronoiField3D(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])),
    )
    positions = np.array([[0.75, 0.0, 0.5], [0.0, -1.0, 0.0], [1.0, 0.0, 0.0]])

    sample = field.sample(positions)

    np.testing.assert_array_equal(sample.owner_seed_id, [1, 0, 0])
    split = np.concatenate(
        [
            field.sample(positions[index : index + 1]).owner_seed_id
            for index in range(len(positions))
        ]
    )
    np.testing.assert_array_equal(split, sample.owner_seed_id)
    assert field.sample(np.empty((0, 3))).owner_seed_id.shape == (0,)


def test_same_seed_and_configuration_retain_same_region_field_at_any_resolution():
    first = _field(123)
    second = _field(123)
    points = np.random.default_rng(9).uniform(-1.0, 1.0, size=(1305, 3))

    np.testing.assert_array_equal(first.voronoi.seeds, second.voronoi.seeds)
    first_sample = first.sample(points)
    second_sample = second.sample(points)
    np.testing.assert_array_equal(
        first_sample.owner_seed_id, second_sample.owner_seed_id
    )
