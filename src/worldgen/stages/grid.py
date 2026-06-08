from __future__ import annotations
import math

from src.worldgen.data import GridTileData, GridPositionData, WorldData
from pyfastnoiselite import FastNoiseLite, NoiseType

class GridStage:
    def __init__(self, seed: int):
        self._seed: int = seed

    def generate_base_grid(self, world_data: WorldData) -> WorldData:
        for x in range(world_data.size):
            for y in range(world_data.size):
                world_data.grid.append(GridTileData(position=GridPositionData(x=x, y=y, z=0)))
        return world_data

    def generate_neighbors(self, world_data: WorldData) -> WorldData:
        for tile in world_data.grid:
            neighbors: list[GridPositionData] = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    wrap_x = (tile.position.x + dx) % world_data.size
                    wrap_y = (tile.position.y + dy) % world_data.size
                    neighbors.append(GridPositionData(x=wrap_x, y=wrap_y, z=0))
            tile.neighbors = neighbors
        return world_data

    def generate_height_map(self, world_data: WorldData) -> WorldData:
        simplex = FastNoiseLite(seed=self._seed)
        simplex.noise_type = NoiseType.NoiseType_OpenSimplex2S

        voronoi = FastNoiseLite(seed=self._seed + 1)
        voronoi.noise_type = NoiseType.NoiseType_Cellular

        for tile in world_data.grid:
            latitude: float = (tile.position.x / world_data.size) * math.pi - (math.pi / 2)
            longitude: float = (tile.position.y / world_data.size) * math.pi * 2

            nx: float = math.cos(latitude) * math.cos(longitude) * world_data.noise_scale
            ny: float = math.cos(latitude) * math.sin(longitude) * world_data.noise_scale
            nz: float = math.sin(latitude) * world_data.noise_scale

            base_noise: float = simplex.get_noise(nx, ny, nz)
            feature_noise: float = voronoi.get_noise(nx, ny, nz)
            mask: float = max(0, base_noise)
            
            tile.position.z = base_noise + (feature_noise * mask * world_data.roughness)
        
        return world_data

    def generate_climate(self, world_data: WorldData) -> WorldData:
        # We need a new noise map just to break up the moisture bands
        moisture_noise = FastNoiseLite(seed=self._seed + 2)
        moisture_noise.noise_type = NoiseType.NoiseType_OpenSimplex2S
        
        for tile in world_data.grid:
            # 1. Recalculate latitude (from -PI/2 to PI/2)
            latitude = (tile.position.y / world_data.size) * math.pi - (math.pi / 2)
            longitude = (tile.position.x / world_data.size) * math.pi * 2
            
            # --- TEMPERATURE ---
            # Base temp based on latitude (1.0 at equator, 0.0 at poles)
            base_temp = math.cos(latitude) 
            
            # Subtract temp based on altitude (z > 0 is land)
            altitude_cooling = max(0, tile.position.z) * 0.5 
            tile.position.temperature = base_temp - altitude_cooling
            
            # --- MOISTURE ---
            # Create the 0, 30, 60, 90 degree precipitation bands
            band_moisture = math.cos(latitude * 6) 
            
            # Get organic noise using 3D coordinates
            nx = math.cos(latitude) * math.cos(longitude) * world_data.noise_scale
            ny = math.cos(latitude) * math.sin(longitude) * world_data.noise_scale
            nz = math.sin(latitude) * world_data.noise_scale
            organic_moisture = moisture_noise.get_noise(nx, ny, nz)
            
            # Blend the bands and the noise (normalized roughly 0.0 to 1.0)
            tile.position.moisture = ((band_moisture * 0.5) + (organic_moisture * 0.5) + 1.0) / 2.0
            
            # --- BIOME ASSIGNMENT ---
            if tile.position.z < 0:
                tile.position.biome = "Ocean"
            elif tile.position.temperature < 0.2:
                tile.position.biome = "Tundra/Ice"
            elif tile.position.temperature > 0.7:
                if tile.position.moisture > 0.6:
                    tile.position.biome = "Rainforest"
                else:
                    tile.position.biome = "Desert"
            else:
                if tile.position.moisture > 0.5:
                    tile.position.biome = "Forest"
                else:
                    tile.position.biome = "Grassland"
                    
        return world_data