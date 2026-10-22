"""Compose source-space elevation consumers from shared geological fields."""

from src.worldgen.elevation.config import ElevationConfig
from src.worldgen.elevation.field import SourceElevationField
from src.worldgen.elevation.source_coastal import SourceCoastalField
from src.worldgen.elevation.tectonic_response import TectonicResponseSampler
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.geology.field import GeologyField
from src.worldgen.elevation.ridge_detail import RidgeDetailField
from src.worldgen.elevation.volcanism import VolcanicField


def generate_elevation_field(
    config: ElevationConfig,
    *,
    geology: GeologyField,
    noise_seeds: tuple[int, int, int],
) -> SourceElevationField:
    """Compose coastal, volcanic and tectonic tools over shared geology."""
    coastal = SourceCoastalField(
        sample_continental_weight=lambda positions: (
            geology.material.sample(positions).continental_weight
        ),
        sample_density_anomaly=geology.sample_density_anomaly,
        span_noise_seeds=noise_seeds,
        config=config.coastal,
        sample_continental_weight_with_gradient=geology.sample_continental_weight_with_gradient,
        sample_density_anomaly_with_gradient=geology.sample_density_anomaly_with_gradient,
    )
    volcanic = VolcanicField(geology, noise_seeds[0] ^ 0x2468AC, config.volcanism)
    sampler = TectonicResponseSampler(
        geology.context.sample_pairs,
        config.tectonic,
        RidgeDetailField(noise_seeds[0] ^ 0x13579B, config.ridge_detail),
        sample_context_with_gradient=geology.context.sample_pairs_with_gradient,
    )
    return SourceElevationField(
        geology=geology,
        coastal=coastal,
        sampler=sampler,
        tectonic=BoundaryResponseField(
            geology.motion, sampler, sampler.sample_with_gradient
        ),
        convergent=BoundaryResponseField(
            geology.motion,
            sampler.sample_convergent,
            sampler.sample_convergent_with_gradient,
        ),
        divergent=BoundaryResponseField(
            geology.motion,
            sampler.sample_divergent,
            sampler.sample_divergent_with_gradient,
        ),
        transform=BoundaryResponseField(
            geology.motion,
            sampler.sample_transform,
            sampler.sample_transform_with_gradient,
        ),
        shear=BoundaryResponseField(
            geology.motion, sampler.sample_shear, sampler.sample_shear_with_gradient
        ),
        volcanism=volcanic,
    )
