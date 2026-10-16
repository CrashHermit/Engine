"""Explicit scalar and style selection for worldgen render layers."""

from dataclasses import dataclass

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from src.worldgen.model import GeneratedWorld

LAYERS = (
    "plates",
    "volcanic-potential",
    "velocity",
    "convergence",
    "divergence",
    "shear",
    "crust",
    "crust-regions",
    "crust-field",
    "crust-density",
    "crust-region-density",
    "boundary-sections",
    "subducting-plate",
    "base-elevation",
    "tectonic-relief",
    "volcanism",
    "elevation",
    "margin-distance",
)


@dataclass(frozen=True)
class LayerStyle:
    values: np.ndarray
    cmap: object
    title: str
    clim: tuple[float, float] | None = None
    vectors: np.ndarray | None = None


def layer_title(layer: str) -> str:
    """Return the user-facing scalar-bar title, including units where needed."""
    if layer in ("base-elevation", "elevation"):
        return "Elevation (m; sea level 0)"
    if layer == "volcanism":
        return "Volcanic uplift (m)"
    if layer == "margin-distance":
        return "Margin distance (% circumference; positive continental)"
    if layer == "crust":
        return "Crust: 0 oceanic, 1 continental"
    return layer


def elevation_colormap(clim: tuple[float, float]) -> LinearSegmentedColormap:
    """Return a bathymetry-to-land map whose exact sea-level value is pale."""
    low, high = clim
    zero = (0.0 - low) / (high - low)
    return LinearSegmentedColormap.from_list(
        "worldgen-elevation",
        [(0.0, "#174a78"), (zero, "#f4f1dc"), (1.0, "#946b3c")],
    )


def layer_style(
    world: GeneratedWorld,
    layer: str,
    elevation_range: tuple[float, float] | None = None,
) -> LayerStyle:
    """Select values and rendering style for a scalar layer."""
    geology = world.geology
    crust = geology.crust
    elevation = world.elevation
    if layer == "plates":
        return LayerStyle(geology.plate_ids, "tab20", title=layer_title(layer))
    if layer == "volcanic-potential":
        return LayerStyle(
            geology.hotspots.potential,
            "viridis",
            title=layer_title(layer),
            clim=(0, 1),
        )
    if layer == "velocity":
        vectors = geology.plate_velocity
        return LayerStyle(
            np.linalg.norm(vectors, axis=1),
            "viridis",
            title=layer_title(layer),
            clim=(0, 1),
            vectors=vectors,
        )
    if layer == "crust":
        return LayerStyle(
            crust.continental_mask.astype(np.int64),
            ["royalblue", "tan"],
            title=layer_title(layer),
            clim=(0, 1),
        )
    if layer == "crust-regions":
        return LayerStyle(crust.region_ids, "tab20", title=layer_title(layer))
    if layer == "crust-field":
        return LayerStyle(
            crust.shaping_field, "viridis", title=layer_title(layer), clim=(0, 1)
        )
    if layer == "crust-density":
        return LayerStyle(crust.effective_density, "viridis", title=layer_title(layer))
    if layer == "crust-region-density":
        return LayerStyle(
            crust.region_effective_density[crust.region_ids],
            "viridis",
            title=layer_title(layer),
        )
    if layer in ("elevation", "base-elevation"):
        values = (
            elevation.elevation if layer == "elevation" else elevation.base_elevation
        )
        clim = (
            elevation_range
            if elevation_range is not None
            else (
                elevation.elevation_range_m
                if layer == "elevation"
                else elevation.base_elevation_range_m
            )
        )
        return LayerStyle(
            values, elevation_colormap(clim), title=layer_title(layer), clim=clim
        )
    if layer == "tectonic-relief":
        values = elevation.tectonic_relief
        extent = max(float(np.max(np.abs(values))), 1.0)
        return LayerStyle(
            values,
            "coolwarm",
            title=layer_title(layer),
            clim=(-extent, extent),
        )
    if layer == "volcanism":
        values = elevation.volcanic_relief
        return LayerStyle(
            values,
            "inferno",
            title=layer_title(layer),
            clim=(0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "margin-distance":
        values = elevation.margin_distance
        extent = np.max(np.abs(values))
        return LayerStyle(
            values, "coolwarm", title=layer_title(layer), clim=(-extent, extent)
        )
    raise KeyError(layer)
