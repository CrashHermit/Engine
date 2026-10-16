import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.render.layers import elevation_colormap, layer_style


def test_elevation_layers_anchor_sea_level_and_accept_fixed_range() -> None:
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    default = layer_style(world, "elevation")
    base = layer_style(world, "base-elevation")

    for style in (default, base):
        zero_fraction = (0.0 - style.clim[0]) / (style.clim[1] - style.clim[0])
        np.testing.assert_allclose(
            style.cmap(zero_fraction)[:3],
            np.array([244, 241, 220]) / 255,
            atol=0.01,
        )

    fixed = layer_style(world, "elevation", (-12_000.0, 8_000.0))
    assert fixed.clim == (-12_000.0, 8_000.0)
    fixed_map = elevation_colormap(fixed.clim)
    np.testing.assert_allclose(
        fixed_map(0.6)[:3], np.array([244, 241, 220]) / 255, atol=0.01
    )
