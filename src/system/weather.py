class WeatherSystem:
    def step(self, grid: WorldGridState)  -> None:
        for y in range(grid.size):
            for x in range(grid.size):
                i: int = y * grid.size + x

                base_t = grid.climate_temperature[i]
                base_p = grid.climate_precipitation[i]

                neighbor_t = average_neighbors(grid.weather_temperature, x, y)
