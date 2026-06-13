@dataclass(frozen=True)
class PlateProperties:
    """Per-plate tectonic metadata."""

    is_continental: BoolArray  # shape (n_plates,)
    drift: Float64Array        # shape (n_plates, 2), unit vectors
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