import numpy as np

from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.geology.config import CrustPartitionConfig
from src.worldgen.geology.crust_field import (
    CrustField,
    build_crust_field,
)
from src.worldgen.geology.crust_influence import CrustInfluenceField


def test_categorical_crust_ownership_retains_region_labels():
    crust = CrustField(
        VoronoiField3D(np.array([[-1.0, 0, 0], [0.0, 0, 0], [1.0, 0, 0]])),
        np.array([True, True, False]),
    )
    points = np.array([[-0.75, 0, 0], [0.25, 0, 0], [0.75, 0, 0]])
    sample = crust.sample(points)

    np.testing.assert_array_equal(sample.region_ids, [0, 1, 2])
    np.testing.assert_array_equal(sample.continental, [True, True, False])
    assert not sample.region_ids.flags.writeable
    assert not sample.continental.flags.writeable


def test_seed_counts_reproducibility_and_material_union():
    config = CrustPartitionConfig(3, 7)
    first = build_crust_field(config, rng=np.random.default_rng(42))
    second = build_crust_field(config, rng=np.random.default_rng(42))
    np.testing.assert_array_equal(first.partition.seeds, second.partition.seeds)
    np.testing.assert_array_equal(first.continental_regions, second.continental_regions)
    assert first.continental_regions.sum() == 3
    assert len(first.partition.seeds) == 10

    points = np.random.default_rng(17).uniform(-1.0, 1.0, size=(64, 3))
    regions = RegionInfluenceField(
        first.partition, RegionInfluenceConfig(transition_half_width=0.2)
    )
    material = CrustInfluenceField(first, regions).sample(points)
    regional = regions.sample(points)
    expected = regional.weights @ first.continental_regions.astype(np.float64)
    np.testing.assert_allclose(material.continental_weight, expected)
    assert np.all(
        (material.continental_weight >= 0.0) & (material.continental_weight <= 1.0)
    )


def test_single_material_is_constant_across_all_regional_transitions():
    seeds = np.array([[-1.0, 0, 0], [0.0, 0, 0], [1.0, 0, 0]])
    points = np.array([[-0.5, 0, 0], [0.0, 0, 0], [0.5, 0, 0]])
    regions = RegionInfluenceField(
        VoronoiField3D(seeds), RegionInfluenceConfig(transition_half_width=0.5)
    )
    for label, expected in ((True, 1.0), (False, 0.0)):
        crust = CrustField(regions.partition, np.full(3, label, dtype=np.bool_))
        influence = CrustInfluenceField(crust, regions).sample(points)
        np.testing.assert_array_equal(
            influence.continental_weight, np.full(len(points), expected)
        )
