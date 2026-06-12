from src.worldgen.pipeline import WorldgenPipeline
from src.worldgen.config.worldgen_config import WorldgenConfig, MeshConfig

ctx = WorldgenPipeline(
    WorldgenConfig(mesh=MeshConfig(cell_count=2000))
).run(seed=42, size=100)

print(ctx.fields.elevation.min(), ctx.fields.elevation.max(), ctx.fields.is_land.mean())
# expect ~0.0, ~1.0, and a land fraction between 0 and 1




from src.worldgen.noise.rng import NoiseSource
n = NoiseSource(42, 100.0, 50.0)  # non-square on purpose
assert n.sample(0, 0, 4.0) == n.sample(100.0, 0, 4.0)   # x wraps at width
assert n.sample(0, 0, 4.0) == n.sample(0, 50.0, 4.0)     # y wraps at height