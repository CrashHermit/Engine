"""Compose source-space relief consumers from shared geological fields."""

from src.worldgen.relief.config import ReliefConfig
from src.worldgen.relief.field import SourceReliefField
from src.worldgen.relief.coastal import SourceCoastalField
from src.worldgen.relief.tectonic_response import TectonicResponseSampler
from src.worldgen.field.boundary_response import BoundaryResponseField
from src.worldgen.geology.field import GeologyField
from src.worldgen.relief.ridge_detail import RidgeDetailField


def generate_source_relief_field(
    config: ReliefConfig,
    *,
    geology: GeologyField,
    noise_seeds: tuple[int, int, int],
) -> SourceReliefField:
    coastal = SourceCoastalField(
        sample_continental_weight=lambda positions: (
            geology.material.sample(positions).continental_weight
        ),
        sample_density_anomaly=geology.density.sample,
        influence_span_noise_seeds=noise_seeds,
        config=config.coastal,
        sample_continental_weight_with_gradient=geology.sample_continental_weight_with_gradient,
        sample_density_anomaly_with_gradient=geology.density.sample_with_gradient,
    )
    sampler = TectonicResponseSampler(
        geology.context.sample_pairs,
        config.tectonic,
        RidgeDetailField(noise_seeds[0] ^ 0x13579B, config.ridge_detail),
        sample_context_with_gradient=geology.context.sample_pairs_with_gradient,
    )
    return SourceReliefField(
        sample_relief_inputs=geology.sample_relief_inputs,
        sample_relief_inputs_with_gradient=geology.sample_relief_inputs_with_gradient,
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
    )
