# Worldgen

Procedural world generator. A seed and a size in, a `WorldData` out — a torus
world with plates, rivers, a frostbelt, blighted regions, and biomes.

```python
from src.worldgen.pipeline import WorldgenPipeline

world = WorldgenPipeline().run(seed=42, size=100)   # -> WorldData
```

`run` is a pure function of `(seed, size, config)`. The simulation mesh is an
internal intermediate and does not ship on `WorldData`; the viewer uses
`run_debug(seed, size) -> (WorldData, WorldContext)` when it needs mesh-side
state.

## Pipeline order

Stages run in this order (`pipeline.py::_build_stages`). Each is a thin wrapper
that reads `ctx.fields`, calls a pure function in a domain package, and writes
results back.

| # | Stage | Job |
|---|---|---|
| 1 | `PlatesStage` | Grow tectonic plates across the mesh (ragged Voronoi). |
| 2 | `PlatePersonalityStage` | Per-plate uplift rate, drift direction, and density. |
| 3 | `BoundaryClassifyStage` | One plate-border walk → per-cell `BoundaryFacts` (the single source of truth for convergence/divergence, plate-pair type, and subduction polarity). |
| 4 | `BoundaryUpliftStage` | Collision belts (mountains) and rift seams, from the facts. |
| 5 | `ErosionStage` | Stream-power erosion + hillslope diffusion. |
| 6 | `FinalizeStage` | Coastal de-speckle, sea level, landmass labels, coast distance, slope. |
| 7 | `InsolationStage` | Authored hot/cold energy bands around the ring. |
| 8 | `TemperatureStage` | Lapse rate + maritime moderation. |
| 9 | `WindStage` | Zonal wind belts deflected by terrain. |
| 10 | `MoistureStage` | Advect ocean moisture downwind (fan), rain it out. |
| 11 | `DischargeStage` | Re-route on final terrain; rain-weighted flow. |
| 12 | `RiversStage` | Classify river cells; extract `River` objects. |
| 13 | `LakesStage` | Connected depressions → `Lake` objects with outlets. |
| 14 | `FlowStage` | Per-cell flow direction and stylized speed. |
| 15 | `SavageryStage` | Legible danger from geography. |
| 16 | `LeylinesStage` | Nexus placement, MST web, aspects, magic fields. |
| 17 | `BiomeStage` | Soft biome weights from climate via `BIOME_GRID`. |

The grid bake (`bake/`) and river stamp run during assembly, after the stages.

## Field glossary (`GridFields`)

Per-tile product columns. Ranges are noted where meaningful.

| Field | Meaning | Range / dtype |
|---|---|---|
| `elevation` | Normalized height; 0 = sea level | [-1, 1] f64 |
| `is_land` | Land vs ocean | bool |
| `plate_id` | Owning tectonic plate | int32 |
| `uplift` | Base tectonic uplift | f64 |
| `z_route` | Water-routing elevation | f64 |
| `receiver` | Downstream cell id; -1 = base level | int32 |
| `drainage` | Upstream area (uniform-rain) | f64 |
| `slope` | Steepest descent | f64 |
| `coast_distance` | Hops from coast | f64 |
| `landmass_id` | Connected land component; 0 = ocean | int32 |
| `landmass_class` | 0 ocean, 1 island, 2 landmass, 3 major | int8 |
| `temperature` | Warmth; 1 = sunband | [0, 1] f64 |
| `precipitation` | Rainfall | [0, 1] f64 |
| `wind_u`, `wind_v` | Unit wind direction | f64 |
| `wind_magnitude` | Wind speed | [0, 1] f64 |
| `discharge` | Rain-weighted water flow | f64 |
| `is_river` | Tile carries a river | bool |
| `river_id` | `River` id; -1 = none | int32 |
| `flow_u`, `flow_v` | Unit flow direction | f64 |
| `flow_speed` | Stylized flow speed | [0, 1] f64 |
| `is_lake` | Tile under lake water | bool |
| `lake_id` | `Lake` id; -1 = none | int32 |
| `savagery` | Danger/wildness | [0, 1] f64 |
| `magic_strength` | Leyline intensity | [0, 1] f64 |
| `magic_valence` | Corrupt..pure | [-1, 1] f64 |
| `magic_channels` | corpus/mens/anima composition | (n, 3) f64 |
| `biome_weights` | Soft biome distribution | (n, 49) f64 |
| `region_id` | Persistence socket (all -1 for now) | int32 |

Feature objects (`River`, `Lake`, `Landmass`, `LeylineNetwork`) ship on
`WorldData` in mesh-cell coordinates; per-tile lookup is the `river_id` /
`lake_id` columns above.

## How to run

```bash
# Interactive viewer (layers: elevation, plates, climate, water, magic, biomes)
uv run python scripts/view_worldgen.py

# Export a layer to PNG. --resolution decouples render detail from the gameplay
# grid: it bakes the mesh directly at that resolution, so the PNG resolves the
# full Voronoi mesh instead of the coarse gameplay grid (for diagnosis/tuning).
uv run python scripts/export_worldgen.py --seed 7 --size 100 --resolution 1024 --layer elevation
uv run python scripts/export_worldgen.py --seed 7 --resolution 1024 --all-layers -o output/

# One-paragraph census per preset/seed — the regression eyeball
uv run python scripts/census.py

# Tests (fast fixtures, deterministic)
uv run pytest test/worldgen -q
```

Presets live in `config/presets.py`: `earthlike`, `archipelago`, `pangaea`,
`wildlands`.
