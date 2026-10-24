"""Build reusable continuous geological fields from independent seed streams."""

from src.worldgen.field.compose import PushforwardVectorField
import numpy as np

from src.worldgen.field.boundary_motion import BoundaryMotionField
from src.worldgen.field.boundary_transport import TransportedBoundaryVectorField
from src.worldgen.field.boundary_vector import BoundaryVectorField
from src.worldgen.field.interaction import BoundaryInteractionField
from src.worldgen.field.region_influence import (
    RegionInfluenceConfig,
    RegionInfluenceField,
)
from src.worldgen.field.region_overlap import RegionOverlapField
from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.geology.config import GeologyConfig
from src.worldgen.geology.crust_field import build_crust_field
from src.worldgen.geology.crust_influence import CrustInfluenceField
from src.worldgen.geology.density import CrustDensityField
from src.worldgen.geology.field import GeologyField
from src.worldgen.geology.motion import build_plate_motion_field
from src.worldgen.geology.subduction_preference import SubductionPreferenceField
from src.worldgen.geology.tectonic_context import TectonicContextField


def generate_geology_field(
    config: GeologyConfig,
    *,
    regions: WarpedVoronoiField,
    crust_rng: np.random.Generator,
    motion_rng: np.random.Generator,
    polarity_rng: np.random.Generator,
    density_noise_seed: int,
) -> GeologyField:
    """Compose plate, crust, motion, and pair-response inputs in source space."""
    plate_influence = RegionInfluenceField(
        regions.voronoi,
        RegionInfluenceConfig(config.plates.transition_half_width_percent / 100.0),
    )
    crust = build_crust_field(config.crust, rng=crust_rng)
    crust_influence = RegionInfluenceField(
        crust.partition,
        RegionInfluenceConfig(config.crust.transition_half_width_percent / 100.0),
    )
    material = CrustInfluenceField(crust, crust_influence)
    preference = SubductionPreferenceField(crust, crust_influence)
    density = CrustDensityField(config.density, density_noise_seed)
    rotations = build_plate_motion_field(
        regions.voronoi, config.plates.motion, rng=motion_rng
    )
    overlap = RegionOverlapField(plate_influence)
    raw_vectors = BoundaryVectorField(
        overlap,
        rotations.sample_regions,
        rotations.sample_regions_with_jacobian,
    )
    vectors = TransportedBoundaryVectorField(
        raw_vectors,
        regions.warp.inverse_with_jacobian,
        regions.warp.inverse_with_hessian,
    )
    motion = BoundaryMotionField(vectors, config=config.boundary_motion)
    interaction = BoundaryInteractionField(motion)

    pair_signs = np.zeros(
        (len(regions.voronoi.seeds), len(regions.voronoi.seeds)),
        dtype=np.float64,
    )
    pair_rows = plate_influence.region_pairs
    signs = np.where(polarity_rng.integers(0, 2, size=len(pair_rows)) == 0, -1.0, 1.0)
    pair_signs[pair_rows[:, 0], pair_rows[:, 1]] = signs
    pair_signs[pair_rows[:, 1], pair_rows[:, 0]] = -signs
    pair_signs.setflags(write=False)

    world_preference = PushforwardVectorField(
        regions.warp.inverse_with_jacobian,
        preference.sample,
        regions.warp.inverse_with_hessian,
        preference.sample_with_jacobian,
    )
    context = TectonicContextField(
        material.sample,
        world_preference.sample,
        pair_signs,
        directed=True,
        blend=config.material_blend,
        polarity=config.polarity,
        sample_material_gradient=material.sample_with_gradient,
        sample_preference_jacobian=world_preference.sample_with_jacobian,
    )
    return GeologyField(
        regions=regions,
        plate_influence=plate_influence,
        crust=crust,
        crust_influence=crust_influence,
        material=material,
        preference=preference,
        rotations=rotations,
        overlap=overlap,
        motion=motion,
        interaction=interaction,
        context=context,
        density=density,
    )
