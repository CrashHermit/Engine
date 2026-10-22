"""Explicit scalar and style selection for continuous world samples."""

from dataclasses import dataclass

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from src.worldgen.surface.model import SurfaceResult
from src.worldgen.world import WorldSample

LAYERS = (
    "plates",
    "crust",
    "crust-regions",
    "continental-weight",
    "subduction-preference-strength",
    "max-plate-weight",
    "region-overlap",
    "convergence",
    "divergence",
    "shear",
    "coastal-elevation",
    "convergent-relief",
    "divergent-relief",
    "tectonic-relief",
    "transform-relief",
    "volcanic-relief",
    "volcanic-potential",
    "volcanic-strength",
    "shear-relief",
    "terrain-variation",
    "elevation",
    "land-height",
    "water-depth",
    "slope",
    "local-relief",
    "roughness",
)


@dataclass(frozen=True, slots=True)
class LayerStyle:
    values: np.ndarray
    cmap: object
    title: str
    clim: tuple[float, float] | None = None
    categorical: bool = False
    annotations: dict[int, str] | None = None


def layer_title(layer: str) -> str:
    if layer in ("coastal-elevation", "elevation"):
        return "Elevation (m; sea level 0)"
    if layer in (
        "convergent-relief",
        "divergent-relief",
        "tectonic-relief",
        "transform-relief",
        "volcanic-relief",
        "terrain-variation",
    ):
        return layer.replace("-", " ").title() + " (m)"
    if layer in ("volcanic-potential", "volcanic-strength"):
        return layer.replace("-", " ").title()
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
    if layer == "crust":
        return "Crust: 0 oceanic, 1 continental"
    return layer.replace("-", " ").title()


_OCEAN_STOPS = (
    (0.0, "#061b3a"),
    (0.35, "#0b4f8a"),
    (0.78, "#3b9ac2"),
    (1.0, "#f4f1dc"),
)
_LAND_STOPS = (
    (0.0, "#f4f1dc"),
    (0.16, "#8fbf6a"),
    (0.42, "#c7b86a"),
    (0.72, "#986b45"),
    (1.0, "#f2f0e8"),
)


def _cropped_colormap(
    name: str,
    stops: tuple[tuple[float, str], ...],
    start: float,
    end: float,
) -> LinearSegmentedColormap:
    base = LinearSegmentedColormap.from_list(name, stops, N=4096)
    positions = [start]
    positions.extend(position for position, _ in stops if start < position < end)
    positions.append(end)
    return LinearSegmentedColormap.from_list(
        name,
        [
            ((position - start) / (end - start), base(position))
            for position in positions
        ],
        N=4096,
    )


def elevation_colormap(clim: tuple[float, float]) -> LinearSegmentedColormap:
    """Return a sea-level-anchored palette, cropped for one-sided ranges."""
    low, high = clim
    if low >= 0.0:
        return _cropped_colormap(
            "worldgen-hypsometric-land", _LAND_STOPS, low / high, 1.0
        )
    if high <= 0.0:
        return _cropped_colormap(
            "worldgen-hypsometric-ocean", _OCEAN_STOPS, 0.0, (high - low) / -low
        )

    zero = (0.0 - low) / (high - low)
    return LinearSegmentedColormap.from_list(
        "worldgen-hypsometric",
        [
            (0.0, _OCEAN_STOPS[0][1]),
            (zero * 0.35, _OCEAN_STOPS[1][1]),
            (zero * 0.78, _OCEAN_STOPS[2][1]),
            (zero, _LAND_STOPS[0][1]),
            (zero + (1.0 - zero) * 0.16, _LAND_STOPS[1][1]),
            (zero + (1.0 - zero) * 0.42, _LAND_STOPS[2][1]),
            (zero + (1.0 - zero) * 0.72, _LAND_STOPS[3][1]),
            (1.0, _LAND_STOPS[4][1]),
        ],
        N=4096,
    )


def common_elevation_range(
    sample: WorldSample,
    *,
    radius_m: float,
    other_sample: WorldSample | None = None,
) -> tuple[float, float]:
    samples = (sample,) if other_sample is None else (sample, other_sample)
    values = (
        np.concatenate(
            [
                channel
                for item in samples
                for channel in (
                    item.elevation.elevation,
                    item.elevation.coastal_elevation,
                )
            ]
        )
        * radius_m
    )
    low = min(float(np.min(values, initial=0.0)), 0.0)
    high = max(float(np.max(values, initial=0.0)), 0.0)
    return (-1e-12, 1e-12) if low == high else (low, high)


def layer_style(
    sample: WorldSample,
    layer: str,
    *,
    radius_m: float,
    elevation_range: tuple[float, float] | None = None,
    surface: SurfaceResult | None = None,
) -> LayerStyle:
    geology, elevation = sample.geology, sample.elevation
    if layer == "plates":
        return LayerStyle(
            geology.plate_ids, "tab20", layer_title(layer), categorical=True
        )
    if layer == "crust":
        return LayerStyle(
            geology.continental_mask.astype(np.int64),
            ["royalblue", "tan"],
            layer_title(layer),
            (0, 1),
            True,
            {0: "oceanic", 1: "continental"},
        )
    if layer == "crust-regions":
        return LayerStyle(
            geology.crust_region_ids, "tab20", layer_title(layer), categorical=True
        )
    if layer in ("continental-weight", "max-plate-weight"):
        values = (
            geology.continental_weight
            if layer == "continental-weight"
            else geology.max_plate_weight
        )
        return LayerStyle(values, "viridis", layer_title(layer), (0.0, 1.0))
    if layer in (
        "subduction-preference-strength",
        "region-overlap",
        "convergence",
        "divergence",
        "shear",
    ):
        values = getattr(geology, layer.replace("-", "_"))
        return LayerStyle(
            values,
            "inferno",
            layer_title(layer),
            (0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer in ("volcanic-potential", "volcanic-strength"):
        values = getattr(elevation, layer.replace("-", "_"))
        return LayerStyle(values, "inferno", layer_title(layer), (0.0, 1.0))
    if layer in ("coastal-elevation", "elevation"):
        values = (
            getattr(
                elevation,
                "coastal_elevation" if layer == "coastal-elevation" else "elevation",
            )
            * radius_m
        )
        clim = elevation_range or common_elevation_range(sample, radius_m=radius_m)
        return LayerStyle(values, elevation_colormap(clim), layer_title(layer), clim)
    if layer in (
        "convergent-relief",
        "divergent-relief",
        "tectonic-relief",
        "transform-relief",
        "volcanic-relief",
        "shear-relief",
        "terrain-variation",
    ):
        values = getattr(elevation, layer.replace("-", "_")) * radius_m
        extent = max(float(np.max(np.abs(values), initial=0.0)), 1.0)
        return LayerStyle(values, "coolwarm", layer_title(layer), (-extent, extent))
    if layer == "land-height":
        values = surface.land_height
        return LayerStyle(
            values,
            "YlOrBr",
            layer_title(layer),
            (0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "water-depth":
        values = surface.water_depth
        return LayerStyle(
            values,
            "Blues",
            layer_title(layer),
            (0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "slope":
        return LayerStyle(
            surface.slope_degrees, "magma", layer_title(layer), (0.0, 90.0)
        )
    if layer == "local-relief":
        values = surface.local_relief
        return LayerStyle(
            values,
            "viridis",
            layer_title(layer),
            (0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    if layer == "roughness":
        values = surface.roughness
        return LayerStyle(
            values,
            "inferno",
            layer_title(layer),
            (0.0, max(float(np.max(values, initial=0.0)), 1.0)),
        )
    raise KeyError(layer)
