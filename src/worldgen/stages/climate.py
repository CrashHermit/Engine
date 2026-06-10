from __future__ import annotations

import math

from src.worldgen.config.worldgen_config import ClimateConfig
from src.worldgen.context import WorldContext
from src.worldgen.geometry.mesh_index import VoronoiMeshIndex
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.sampler import (
    FIELD_CLIMATE_PRECIP,
    FIELD_CLIMATE_PRECIP_WARP,
    FIELD_CLIMATE_TEMP_WARP,
    FIELD_CLIMATE_WIND_U,
    FIELD_CLIMATE_WIND_V,
)


class ClimateStage:
    """Generates temperature, precipitation, and wind fields on the mesh.

    Temperature: latitude-based cosine band with noise warp and elevation
    lapse-rate cooling.

    Precipitation: latitude band weighted with organic noise, plus
    orographic uplift on windward slopes.

    Wind: Hadley-cell-based direction pattern with noise turbulence.

    Pipeline position: after ``HydrologyStage``.
    """

    def __init__(self, config: ClimateConfig) -> None:
        self._config = config

    def run(self, ctx: WorldContext) -> WorldContext:
        self._generate_wind(ctx)
        self._generate_climate(ctx)
        self._apply_orographic(ctx)
        if self._config.moisture_advection > 0.0:
            self._advect_moisture(ctx)
        return ctx

    # ------------------------------------------------------------------
    # Wind
    # ------------------------------------------------------------------

    def _generate_wind(self, ctx: WorldContext) -> None:
        cfg = self._config
        mesh = ctx.data.mesh

        wind_freq = cfg.noise_scale * cfg.wind_noise_scale_factor
        wind_u_field = FractalField(ctx.sampler, FIELD_CLIMATE_WIND_U, octaves=2)
        wind_v_field = FractalField(ctx.sampler, FIELD_CLIMATE_WIND_V, octaves=2)

        for cell in mesh.cells:
            x, y = cell.site
            normalized_y = (y / mesh.height) * 2.0 - 1.0
            base_u = -math.cos(abs(normalized_y) * math.pi * 2.5)
            hemisphere = -1.0 if normalized_y > 0 else 1.0
            base_v = math.sin(abs(normalized_y) * math.pi * 2.5) * hemisphere

            noise_u = wind_u_field.sample(x, y, wind_freq)
            noise_v = wind_v_field.sample(x, y, wind_freq)
            raw_u = base_u + noise_u * cfg.wind_turbulence
            raw_v = base_v + noise_v * cfg.wind_turbulence
            magnitude = math.sqrt(raw_u**2 + raw_v**2)

            climate = cell.env.climate
            if magnitude > 0.0:
                climate.wind_u = raw_u / magnitude
                climate.wind_v = raw_v / magnitude
                climate.wind_magnitude = magnitude
            else:
                climate.wind_u = 0.0
                climate.wind_v = 0.0
                climate.wind_magnitude = 0.0

    # ------------------------------------------------------------------
    # Temperature and precipitation
    # ------------------------------------------------------------------

    def _generate_climate(self, ctx: WorldContext) -> None:
        cfg = self._config
        mesh = ctx.data.mesh

        temp_warp = FractalField(ctx.sampler, FIELD_CLIMATE_TEMP_WARP, octaves=2)
        precip_field = FractalField(ctx.sampler, FIELD_CLIMATE_PRECIP, octaves=3)
        precip_warp = FractalField(ctx.sampler, FIELD_CLIMATE_PRECIP_WARP, octaves=2)
        organic_weight = 1.0 - cfg.band_weight

        for cell in mesh.cells:
            x, y = cell.site

            # --- temperature ------------------------------------------
            warp_y_t = temp_warp.sample(x, y, cfg.noise_scale) * cfg.warp_amplitude
            warped_y_t = y + warp_y_t
            phase_t = 2.0 * math.pi * warped_y_t / mesh.height * cfg.temperature_bands
            base_temp = (math.cos(phase_t) + 1.0) / 2.0
            elevation_cooling = max(0.0, cell.env.terrain.z) * cfg.lapse_rate
            cell.env.climate.temperature = max(0.0, base_temp - elevation_cooling)

            # --- precipitation ----------------------------------------
            warp_px = precip_warp.sample(x, y, cfg.noise_scale) * cfg.warp_amplitude
            warp_py = (
                precip_warp.sample(x + 5.2, y, cfg.noise_scale) * cfg.warp_amplitude
            )
            wx, wy = x + warp_px, y + warp_py
            warped_y_p = y + warp_py
            normalized_py = (warped_y_p / mesh.height) * 2.0 - 1.0
            band_precip = math.sin(normalized_py * math.pi * cfg.precip_latitude_bands)
            organic_precip = precip_field.sample(wx, wy, cfg.noise_scale)
            cell.env.climate.precipitation = (
                (band_precip * cfg.band_weight)
                + (organic_precip * organic_weight)
                + 1.0
            ) / 2.0

    # ------------------------------------------------------------------
    # Orographic uplift
    # ------------------------------------------------------------------

    def _apply_orographic(self, ctx: WorldContext) -> None:
        cfg = self._config
        mesh = ctx.data.mesh
        mesh_index = VoronoiMeshIndex(mesh)

        for cell in mesh.cells:
            climate = cell.env.climate
            if not cell.env.terrain.is_land:
                continue
            if climate.wind_u == 0.0 and climate.wind_v == 0.0:
                continue
            upwind_id = self._find_upwind_cell(mesh, mesh_index, cell)
            if upwind_id is None:
                continue
            upwind = mesh.cells[upwind_id]
            dz = cell.env.terrain.z - upwind.env.terrain.z
            modifier = dz * climate.wind_magnitude * cfg.orographic_multiplier
            climate.precipitation = max(0.0, climate.precipitation + modifier)

    def _find_upwind_cell(self, mesh, mesh_index, cell) -> int | None:
        climate = cell.env.climate
        step = min(mesh.width, mesh.height) * 0.02
        upwind_x = (cell.site[0] - climate.wind_u * step) % mesh.width
        upwind_y = (cell.site[1] - climate.wind_v * step) % mesh.height
        upwind_id = mesh_index.nearest_cell_id(upwind_x, upwind_y)
        return None if upwind_id == cell.id else upwind_id

    def _advect_moisture(self, ctx: WorldContext) -> None:
        cfg = self._config
        mesh = ctx.data.mesh
        mesh_index = VoronoiMeshIndex(mesh)

        advected = [cell.env.climate.precipitation for cell in mesh.cells]
        for cell in mesh.cells:
            climate = cell.env.climate
            if not cell.env.terrain.is_land:
                continue
            upwind_id = self._find_upwind_cell(mesh, mesh_index, cell)
            if upwind_id is None:
                continue
            upwind = mesh.cells[upwind_id]
            transfer = (
                (upwind.env.climate.precipitation - climate.precipitation)
                * cfg.moisture_advection
                * climate.wind_magnitude
            )
            advected[cell.id] = max(0.0, climate.precipitation + transfer)
        for index, cell in enumerate(mesh.cells):
            cell.env.climate.precipitation = advected[index]
