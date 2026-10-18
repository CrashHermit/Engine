"""Explicit scalar and style selection for worldgen render layers."""

from dataclasses import dataclass

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from src.worldgen.model import GeneratedWorld
from src.worldgen.geology.model import VolcanoState

LAYERS = (
    "plates",
    "volcanic-potential",
    "hotspot-potential",
    "volcanic-activity",
    "volcanic-areas",
    "volcano-state",
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
    "coastal-elevation",
    "elevation",
    "tectonic-relief",
    "volcanism",
    "terrain-variation",
    "impact-relief",
    "margin-distance",
    "land-height",
    "water-depth",
    "slope",
    "local-relief",
    "roughness",
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
    if layer in ("coastal-elevation", "elevation"):
        return "Elevation (m; sea level 0)"
    if layer == "land-height":
        return "Land height (m)"
    if layer == "water-depth":
        return "Water depth below sea level (m)"
    if layer == "slope":
        return "Surface slope (degrees)"
    if layer == "local-relief":
        return "Local relief (m)"
    if layer == "roughness":
        return "Detrended roughness (m RMS)"
    if layer == "terrain-variation":
        return "Terrain variation (m)"
    if layer == "impact-relief":
        return "Impact relief (m)"
    if layer == "volcanism":
        return "Volcanic uplift (m)"
    if layer == "margin-distance":
        return "Margin distance (% circumference; positive continental)"
    if layer == "crust":
        return "Crust: 0 oceanic, 1 continental"
    if layer == "volcano-state":
        return "Volcano sites: 0 none, 1 dormant, 2 erupting, 3 extinct"
    if layer == "volcanic-activity":
        return "Volcanic activity (procedural strength)"
    if layer == "volcanic-potential":
        return "Source-derived volcanic potential (procedural strength)"
    return layer


def elevation_colormap(clim: tuple[float, float]) -> LinearSegmentedColormap:
    """Return bathymetry and hypsometric tints anchored at sea level."""
    low, high = clim
    zero = (0.0 - low) / (high - low)
    return LinearSegmentedColormap.from_list(
        "worldgen-hypsometric",
        [
            (0.0, "#061b3a"),
            (zero * 0.35, "#0b4f8a"),
            (zero * 0.78, "#3b9ac2"),
            (zero, "#f4f1dc"),
            (zero + (1.0 - zero) * 0.16, "#8fbf6a"),
            (zero + (1.0 - zero) * 0.42, "#c7b86a"),
            (zero + (1.0 - zero) * 0.72, "#986b45"),
            (1.0, "#f2f0e8"),
        ],
        N=4096,
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
    surface = world.surface
    if layer == "plates":
        return LayerStyle(geology.plate_ids, "tab20", title=layer_title(layer))
    if layer == "hotspot-potential":
        return LayerStyle(
            geology.hotspots.potential,
            "viridis",
            title=layer_title(layer),
            clim=(0, 1),
        )
    if layer in ("volcanic-potential", "volcanic-activity"):
        values = (
            geology.volcanism.potential
            if layer == "volcanic-potential"
            else geology.volcanism.activity
        )
        return LayerStyle(
            values,
            "inferno",
            title=layer_title(layer),
            clim=(0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "volcanic-areas":
        return LayerStyle(
            geology.volcanism.volcanic_mask.astype(np.int64),
            ["lightgray", "orangered"],
            title="Volcanic area: 0 no, 1 yes",
            clim=(0, 1),
        )
    if layer == "volcano-state":
        values = np.zeros(len(world.mesh.vertices), dtype=np.int64)
        sites = geology.volcanism.sites
        for state, code in (
            (VolcanoState.DORMANT, 1),
            (VolcanoState.ERUPTING, 2),
            (VolcanoState.EXTINCT, 3),
        ):
            values[sites.cell_indices[sites.states == state]] = code
        return LayerStyle(
            values,
            ["lightgray", "gold", "orangered", "slategray"],
            title=layer_title(layer),
            clim=(0, 3),
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
    if layer in ("elevation", "coastal-elevation"):
        values = (
            elevation.elevation if layer == "elevation" else elevation.coastal_elevation
        )
        clim = (
            elevation_range
            if elevation_range is not None
            else (
                elevation.elevation_range_m
                if layer == "elevation"
                else elevation.coastal_elevation_range_m
            )
        )
        return LayerStyle(
            values, elevation_colormap(clim), title=layer_title(layer), clim=clim
        )
    if layer == "land-height":
        values = surface.land_height
        return LayerStyle(
            values,
            "YlOrBr",
            title=layer_title(layer),
            clim=(0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "water-depth":
        values = surface.water_depth
        return LayerStyle(
            values,
            "Blues",
            title=layer_title(layer),
            clim=(0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "slope":
        return LayerStyle(
            surface.slope_degrees,
            "magma",
            title=layer_title(layer),
            clim=(0.0, 90.0),
        )
    if layer == "local-relief":
        values = surface.local_relief
        return LayerStyle(
            values,
            "viridis",
            title=layer_title(layer),
            clim=(0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "roughness":
        values = surface.roughness
        return LayerStyle(
            values,
            "inferno",
            title=layer_title(layer),
            clim=(0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "terrain-variation":
        values = elevation.terrain_variation
        extent = max(
            abs(world.elevation_field.variation.config.amplitude_percent)
            * (world.radius_m / 100.0),
            1.0,
        )
        return LayerStyle(
            values,
            "coolwarm",
            title=layer_title(layer),
            clim=(-extent, extent),
        )

    if layer == "impact-relief":
        values = elevation.impact_relief
        lower, upper = world.elevation_field.impacts.bounds(world.radius_m)
        extent = max(abs(lower), abs(upper), 1.0)
        return LayerStyle(
            values,
            "coolwarm",
            title=layer_title(layer),
            clim=(-extent, extent),
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
