"""Build the mesh-independent world fields and sampled world artifact."""

from functools import partial

import numpy as np

from src.worldgen.config import WorldgenConfig
from src.worldgen.elevation.generate import generate_elevation_field
from src.worldgen.elevation.variation import TerrainVariationField
from src.worldgen.field.regions import build_warped_voronoi_field
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.generate import generate_geology_field
from src.worldgen.model import GeneratedWorld
from src.worldgen.surface.field import SurfaceField
from src.worldgen.world import WorldField


def generate_world_field(config: WorldgenConfig) -> WorldField:
    """Build continuous fields independently of mesh, subdivision and radius."""
    streams = np.random.SeedSequence(config.seed).spawn(6)
    regions = build_warped_voronoi_field(
        config.geology.plates.plate_count,
        rng=np.random.default_rng(streams[0]),
        noise_seed=config.seed + 3000,
        noise_config=config.warp_noise,
        warp_config=config.warp,
    )
    noise_rng = np.random.default_rng(streams[4])
    noise_seeds = tuple(
        int(value)
        for value in noise_rng.integers(-(2**31), 2**31, size=4, dtype=np.int64)
    )
    variation_seed = int(
        np.random.default_rng(streams[5]).integers(-(2**31), 2**31, dtype=np.int64)
    )
    geology = generate_geology_field(
        config.geology,
        regions=regions,
        crust_rng=np.random.default_rng(streams[1]),
        motion_rng=np.random.default_rng(streams[2]),
        polarity_rng=np.random.default_rng(streams[3]),
        density_noise_seed=noise_seeds[3],
    )
    source_elevation = generate_elevation_field(
        config.elevation,
        geology=geology,
        noise_seeds=noise_seeds[:3],
    )
    variation = TerrainVariationField(config.elevation.variation, variation_seed)
    return WorldField(
        geology=geology,
        source_elevation=source_elevation,
        variation=variation,
        warp=regions.warp,
    )


def generate_world(config: WorldgenConfig) -> GeneratedWorld:
    """Sample the continuous world fields at the configured icosphere centers."""
    field = generate_world_field(config)
    mesh = Mesh(*generate_icosphere(config.subdivision_frequency))
    sample = field.sample_world(mesh.vertices)
    radius_m = config.planet.radius_m
    center_elevation_m = sample.elevation.elevation * radius_m
    center_elevation_m.setflags(write=False)
    surface_field = SurfaceField(
        config.surface,
        partial(field.sample_elevation_meters, radius_m=radius_m),
        radius_m,
        partial(field.sample_elevation_meters_with_gradient, radius_m=radius_m),
    )
    surface = surface_field.sample(mesh.vertices, center_elevation=center_elevation_m)
    return GeneratedWorld(
        mesh=mesh,
        geology=sample.geology,
        elevation=sample.elevation,
        surface=surface,
        radius_m=radius_m,
        field=field,
        surface_field=surface_field,
    )
