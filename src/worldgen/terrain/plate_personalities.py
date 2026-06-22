import math
import random
from dataclasses import dataclass

import numpy as np

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.types import BoolArray, Float64Array, Int32Array


@dataclass(frozen=True)
class PlateProperties:
    """Per-plate tectonic metadata."""

    is_continental: BoolArray  # shape (n_plates,)
    drift: Float64Array  # shape (n_plates, 2), unit vectors
    base_uplift: Float64Array  # shape (n_plates,)


def assign_plate_personalities(
    *,
    n_plates: int,
    seed: int,
    config: PlatesConfig,
) -> PlateProperties:
    """Roll continental/oceanic type and drift direction for each plate.

    Returns lookup tables used to fill ``uplift`` and boundary uplift in Step 4.
    """
    if n_plates < 1:
        msg: str = "n_plates must be at least 1"
        raise ValueError(msg)

    rng: random.Random = random.Random(x=seed)

    is_continental: BoolArray = np.zeros(shape=n_plates, dtype=bool)
    drift: Float64Array = np.zeros(shape=(n_plates, 2), dtype=np.float64)
    base_uplift: Float64Array = np.zeros(shape=n_plates, dtype=np.float64)

    plate: int
    for plate in range(n_plates):
        continental: bool = rng.random() < config.continental_fraction
        is_continental[plate] = continental
        base_uplift[plate] = (
            config.continental_uplift if continental else config.oceanic_uplift
        )

        theta: float = rng.random() * 2.0 * math.pi
        drift[plate, 0] = math.cos(theta)
        drift[plate, 1] = math.sin(theta)

    return PlateProperties(
        is_continental=is_continental,
        drift=drift,
        base_uplift=base_uplift,
    )


def fill_uplift_from_plates(
    *,
    plate_id: Int32Array,
    base_uplift: Float64Array,
) -> Float64Array:
    """Map per-plate base uplift onto every cell via ``plate_id`` fancy indexing."""
    return base_uplift[plate_id]
