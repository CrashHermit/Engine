from __future__ import annotations

import math
from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, NoiseType
from src.worldgen.data import GridTileData, GridPositionData, WorldData

class GridStage:
    def __init__(self, seed: int) -> None:
        self._seed: int = seed

    def generate_base_grid(self, world_data: WorldData) -> WorldData:
        for x in range(world_data.size):
            for y in range(world_data.size):
                world_data.grid.append(GridTileData(position=GridPositionData(x=x, y=y)))
        return world_data

    def generate_neighbors(self, world_data: WorldData) -> WorldData:
        for tile in world_data.grid:
            neighbors: list[GridPositionData] = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    # Torus wrapping math
                    wrap_x: int = (tile.position.x + dx) % world_data.size
                    wrap_y: int = (tile.position.y + dy) % world_data.size
                    
                    neighbor_index: int = wrap_x * world_data.size + wrap_y
                    neighbors.append(world_data.grid[neighbor_index].position)
                    
            tile.neighbors = neighbors
        return world_data

    def get_torus_coords(self, x: int, y: int, size: int, scale: float) -> tuple[float, float, float]:
        """Helper method to convert 2D grid coordinates into 3D Torus coordinates."""
        theta: float = (x / size) * math.pi * 2
        phi: float = (y / size) * math.pi * 2
        
        # R = major radius, r = minor radius (tube thickness)
        R: float = 1.0 
        r: float = 0.5 
        
        nx: float = (R + r * math.cos(phi)) * math.cos(theta) * scale
        ny: float = (R + r * math.cos(phi)) * math.sin(theta) * scale
        nz: float = r * math.sin(phi) * scale
        
        return nx, ny, nz

    def generate_wind(self, world_data: WorldData) -> WorldData:
        # Noise to make the wind organic and swirling
        wind_noise_u = FastNoiseLite(seed=self._seed + 20)
        wind_noise_u.noise_type = NoiseType.NoiseType_OpenSimplex2
        
        wind_noise_v = FastNoiseLite(seed=self._seed + 21)
        wind_noise_v.noise_type = NoiseType.NoiseType_OpenSimplex2
        
        turbulence: float = 0.4 # How chaotic the wind gets
        
        for tile in world_data.grid:
            # 1. Base planetary latitude math
            normalized_y = (tile.position.y / world_data.size) * 2.0 - 1.0
            
            # The 2.5 multiplier creates the 3 distinct wind cells per hemisphere
            # u (East/West): Negative is East-to-West, Positive is West-to-East
            base_u = -math.cos(abs(normalized_y) * math.pi * 2.5)
            
            # v (North/South): Blows toward equator (0) and sub-polar lows (+/- 0.6)
            # We use sine to calculate the north/south drift
            hemisphere_modifier = -1.0 if normalized_y > 0 else 1.0
            base_v = math.sin(abs(normalized_y) * math.pi * 2.5) * hemisphere_modifier
            
            # 2. Add organic turbulence using our Torus coordinates
            nx, ny, nz = self.get_torus_coords(
                x=tile.position.x, 
                y=tile.position.y, 
                size=world_data.size, 
                scale=world_data.noise_scale * 0.5 # Wind patterns are generally larger scale
            )
            
            noise_u = wind_noise_u.get_noise(nx, ny, nz)
            noise_v = wind_noise_v.get_noise(nx, ny, nz)
            
            # 3. Combine and normalize the vector
            raw_u = base_u + (noise_u * turbulence)
            raw_v = base_v + (noise_v * turbulence)
            
            # Calculate magnitude (speed) using Pythagorean theorem
            magnitude = math.sqrt(raw_u**2 + raw_v**2)
            
            # Prevent division by zero
            if magnitude > 0:
                tile.position.wind_u = raw_u / magnitude
                tile.position.wind_v = raw_v / magnitude
                # Magnitude is roughly 0.0 to 1.0+ depending on turbulence
                tile.position.wind_magnitude = magnitude 
            else:
                tile.position.wind_u = 0.0
                tile.position.wind_v = 0.0
                tile.position.wind_magnitude = 0.0
                
        return world_data

    def generate_height_map(self, world_data: WorldData) -> WorldData:
        simplex: FastNoiseLite = FastNoiseLite(seed=self._seed)
        simplex.noise_type = NoiseType.NoiseType_OpenSimplex2S

        voronoi: FastNoiseLite = FastNoiseLite(seed=self._seed + 1)
        voronoi.noise_type = NoiseType.NoiseType_Cellular

        for tile in world_data.grid:
            nx, ny, nz = self.get_torus_coords(
                tile.position.x, 
                tile.position.y, 
                world_data.size, 
                world_data.noise_scale
            )

            base_noise: float = simplex.get_noise(nx, ny, nz)
            feature_noise: float = voronoi.get_noise(nx, ny, nz)
            mask: float = max(0, base_noise)
            
            tile.position.z = base_noise + (feature_noise * mask * world_data.roughness)
        
        return world_data

    def apply_orographic_effect(self, world_data: WorldData) -> WorldData:
        # How intensely the mountain slope affects the rain
        orographic_multiplier: float = 1.5 
        
        for tile in world_data.grid:
            # Skip the deep ocean (optional, but saves CPU)
            if tile.position.z < 0.0:
                continue
                
            # 1. Figure out which way the wind is coming FROM
            # Wind vectors point to where the wind is going. We want the opposite.
            # We round to the nearest integer to find the discrete grid neighbor
            dx = int(round(tile.position.wind_u))
            dy = int(round(tile.position.wind_v))
            
            # If the wind is completely dead, there is no orographic effect
            if dx == 0 and dy == 0:
                continue
                
            # 2. Find the Upwind Tile (using Torus wrapping math)
            upwind_x = (tile.position.x - dx) % world_data.size
            upwind_y = (tile.position.y - dy) % world_data.size
            
            upwind_index = upwind_x * world_data.size + upwind_y
            upwind_tile = world_data.grid[upwind_index]
            
            # 3. Calculate Elevation Gradient (Slope)
            # Positive dz: Wind is climbing (Windward)
            # Negative dz: Wind is falling (Leeward)
            dz = tile.position.z - upwind_tile.position.z
            
            # 4. Apply the modifier
            # We scale the slope by the strength of the wind and our multiplier
            modifier = dz * tile.position.wind_magnitude * orographic_multiplier
            
            # Apply to base precipitation, clamping to ensure it doesn't drop below 0.0
            tile.position.precipitation = max(0.0, tile.position.precipitation + modifier)
            
        return world_data

    def generate_climate(self, world_data: WorldData) -> WorldData:
        temp_warp = FastNoiseLite(seed=self._seed + 10)
        temp_warp.noise_type = NoiseType.NoiseType_OpenSimplex2
        
        precip_warp = FastNoiseLite(seed=self._seed + 11)
        precip_warp.noise_type = NoiseType.NoiseType_OpenSimplex2

        precip_noise = FastNoiseLite(seed=self._seed + 2)
        precip_noise.noise_type = NoiseType.NoiseType_OpenSimplex2S
        
        warp_amp: float = 1.5 
        lapse_rate: float = 0.5  
        
        off_y: float = 5.2
        off_z: float = 1.3
        
        for tile in world_data.grid:
            base_nx, base_ny, base_nz = self.get_torus_coords(
                x=tile.position.x, 
                y=tile.position.y, 
                size=world_data.size, 
                scale=world_data.noise_scale
            )
            
            # --- TEMPERATURE (Optimized: Y-Warp Only) ---
            # We only warp Y because temperature relies strictly on latitude
            t_warp_y = temp_warp.get_noise(base_nx + off_y, base_ny, base_nz)
            tny = base_ny + (t_warp_y * warp_amp)
            
            normalized_ty = (tny / world_data.size) * 2.0 - 1.0
            base_temp = 1.0 - abs(normalized_ty) 
            
            elevation_cooling = max(0.0, tile.position.z) * lapse_rate
            tile.position.temperature = max(0.0, base_temp - elevation_cooling)
            
            # --- PRECIPITATION (Full 3D Warp) ---
            # We warp X, Y, and Z because they feed into a 3D noise map
            p_warp_x = precip_warp.get_noise(base_nx, base_ny, base_nz)
            p_warp_y = precip_warp.get_noise(base_nx + off_y, base_ny, base_nz)
            p_warp_z = precip_warp.get_noise(base_nx, base_ny + off_z, base_nz)
            
            pnx = base_nx + (p_warp_x * warp_amp)
            pny = base_ny + (p_warp_y * warp_amp)
            pnz = base_nz + (p_warp_z * warp_amp)
            
            normalized_py = (pny / world_data.size) * 2.0 - 1.0
            band_precip = math.sin(normalized_py * math.pi * 3)
            organic_precip = precip_noise.get_noise(x=pnx, y=pny, z=pnz)
            
            tile.position.precipitation = ((band_precip * 0.5) + (organic_precip * 0.5) + 1.0) / 2.0
            
        return world_data

    def _tile_index(self, world_data: WorldData) -> dict[tuple[int, int], GridTileData]:
        return {(tile.position.x, tile.position.y): tile for tile in world_data.grid}

    def generate_rivers(self, world_data: WorldData) -> WorldData:
        tile_index = self._tile_index(world_data)

        # 1. Reset river data
        for tile in world_data.grid:
            tile.position.river_volume = 0.0
            tile.position.is_lake = False

        # 2. Trace water from every land tile
        for tile in world_data.grid:
            # Skip the ocean or perfectly dry tiles
            if tile.position.z <= 0.0 or tile.position.precipitation <= 0.0:
                continue

            current_tile = tile
            volume = tile.position.precipitation

            # Keep track of where this specific drop has been to prevent infinite loops
            path_visited: set[tuple[int, int]] = set()

            while current_tile.position.z > 0.0:
                current_tile.position.river_volume += volume
                path_visited.add((current_tile.position.x, current_tile.position.y))

                # Find the steepest way down
                lowest_neighbor = min(current_tile.neighbors, key=lambda n: n.z)

                # Normal downhill flow
                if lowest_neighbor.z < current_tile.position.z:
                    current_tile = tile_index[(lowest_neighbor.x, lowest_neighbor.y)]

                # Pit detected! Trigger the lake fill.
                else:
                    pour_point = self._fill_lake_and_find_spillway(
                        current_tile.position,
                        tile_index,
                    )

                    if pour_point and (pour_point.x, pour_point.y) not in path_visited:
                        # Teleport the raindrop to the spillway to continue its journey
                        current_tile = tile_index[(pour_point.x, pour_point.y)]
                    else:
                        # Landlocked basin (e.g., Dead Sea). Lake cannot overflow.
                        break

        return world_data

    def _fill_lake_and_find_spillway(
        self,
        start_pos: GridPositionData,
        tile_index: dict[tuple[int, int], GridTileData],
    ) -> GridPositionData | None:
        start_key = (start_pos.x, start_pos.y)
        lake_basin: set[tuple[int, int]] = {start_key}
        start_tile = tile_index[start_key]
        edge_pool: set[tuple[int, int]] = {
            (neighbor.x, neighbor.y) for neighbor in start_tile.neighbors
        } - lake_basin

        water_level = start_pos.z

        while edge_pool:
            # Find the lowest tile on the perimeter of our growing lake
            lowest_edge_key = min(
                edge_pool,
                key=lambda key: tile_index[key].position.z,
            )
            lowest_edge = tile_index[lowest_edge_key].position

            # If the edge is lower than our water level, we found a way out!
            if lowest_edge.z < water_level:
                # 1. Flag the tiles as a lake
                # 2. Physically flatten the terrain so future rivers cross it instantly
                for key in lake_basin:
                    position = tile_index[key].position
                    position.is_lake = True
                    position.z = water_level
                return lowest_edge

            # Otherwise, the lake fills up to this new edge height
            water_level = lowest_edge.z
            lake_basin.add(lowest_edge_key)
            edge_pool.remove(lowest_edge_key)

            # Add the new tile's neighbors to the search perimeter
            for neighbor in tile_index[lowest_edge_key].neighbors:
                neighbor_key = (neighbor.x, neighbor.y)
                if neighbor_key not in lake_basin:
                    edge_pool.add(neighbor_key)

        # If we run out of tiles (the whole continent is a bowl)
        for key in lake_basin:
            position = tile_index[key].position
            position.is_lake = True
            position.z = water_level

        return None