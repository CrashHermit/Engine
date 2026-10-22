import numpy as np

from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.geology.config import MaterialBlendConfig
from src.worldgen.geology.crust_field import CrustField
from src.worldgen.geology.crust_influence import (
    CrustInfluenceField,
    continental_response_weight,
)


def _crust(seeds, continental_regions):
    return CrustField(
        VoronoiField3D(np.asarray(seeds, dtype=np.float64)),
        np.asarray(continental_regions, dtype=np.bool_),
    )


def _influence(seeds, continental_regions, transition_half_width=0.5):
    crust = _crust(seeds, continental_regions)
    regions = RegionInfluenceField(
        crust.partition, RegionInfluenceConfig(transition_half_width)
    )
    return CrustInfluenceField(crust, regions)


def test_crust_influence_blends_continental_and_oceanic_membership():
    seeds = [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    points = np.array([[-0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.5, 0.0, 0.0]])
    continental = _influence(seeds, [True, False]).sample(points)
    reversed_material = _influence(seeds, [False, True]).sample(points)

    np.testing.assert_allclose(continental.continental_weight, [1.0, 0.5, 0.0])
    np.testing.assert_allclose(continental.oceanic_weight, [0.0, 0.5, 1.0])
    np.testing.assert_allclose(reversed_material.continental_weight, [0.0, 0.5, 1.0])
    np.testing.assert_allclose(reversed_material.oceanic_weight, [1.0, 0.5, 0.0])
    assert continental.continental_weight[1] == continental.oceanic_weight[1]
    assert not continental.continental_weight.flags.writeable
    assert not continental.oceanic_weight.flags.writeable


def test_same_material_regions_have_no_material_seam():
    seeds = [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    points = np.array([[-0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.5, 0.0, 0.0]])
    all_continental = _influence(seeds, [True, True]).sample(points)
    all_oceanic = _influence(seeds, [False, False]).sample(points)

    np.testing.assert_array_equal(all_continental.continental_weight, 1.0)
    np.testing.assert_array_equal(all_oceanic.continental_weight, 0.0)


def test_crust_influence_handles_empty_queries_and_configured_blending():
    field = _influence([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], [True, False])
    empty = field.sample(np.empty((0, 3)))
    assert empty.continental_weight.shape == (0,)
    assert empty.oceanic_weight.shape == (0,)
    assert not empty.continental_weight.flags.writeable
    assert not empty.oceanic_weight.flags.writeable

    blend = continental_response_weight(
        np.array([0.25, 0.35, 0.45]),
        MaterialBlendConfig(midpoint=0.35, transition_width=0.2),
    )
    np.testing.assert_allclose(blend, [0.0, 0.5, 1.0], atol=1e-14)
    assert not blend.flags.writeable
