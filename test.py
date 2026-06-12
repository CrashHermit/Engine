from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.config.worldgen_config import WorldgenConfig, MeshConfig
from src.worldgen.bake import nearest_cell_per_tile, bake_to_grid

ctx = WorldgenPipeline(
    WorldgenConfig(mesh=MeshConfig(cell_count=2000))
).run(seed=42, size=100)

nearest = nearest_cell_per_tile(ctx.geometry, size=ctx.config.size)
grid = bake_to_grid(ctx.fields, nearest)

assert grid.elevation.shape == (10_000,)
assert grid.elevation.min() >= 0.0
assert grid.elevation.max() <= 1.0

mesh_land = float(ctx.fields.is_land.mean())
grid_land = float(grid.is_land.mean())
print(f"mesh land fraction: {mesh_land:.3f}")
print(f"grid land fraction: {grid_land:.3f}")
assert abs(mesh_land - grid_land) < 0.05  # "roughly matches"