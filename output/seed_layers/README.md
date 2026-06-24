# Seed Layer Images

This directory contains procedurally generated world maps showing all visualization layers for different seeds.

## Overview

Generated **5 different seeds** with **25 layers each** = **125 total images**

Each seed (42, 123, 456, 789, 999) has the complete pipeline visualization showing the progression from raw terrain generation through climate simulation to final biome assignment.

## Directory Structure

```
output/seed_layers/
├── seed_42/
├── seed_123/
├── seed_456/
├── seed_789/
├── seed_999/
└── README.md (this file)
```

## Layer Categories

### Terrain & Geology (7 layers)
- **elevation** - Normalized terrain height (-1 to 1, where 0 is sea level)
- **land** - Simple land vs ocean binary mask
- **plates** - Tectonic plate distribution (ragged Voronoi)
- **uplift** - Base tectonic uplift from plate interactions
- **drainage** - Water flow accumulation (upstream area)
- **volcanism** - Volcanic activity and hotspots
- **mesh** - Raw Voronoi mesh visualization

### Climate & Weather (8 layers)
- **latitude** - Signed latitude gradient (0 = equator, ±1 = poles)
- **insolation** - Solar radiation intensity from latitude
- **temperature** - Combined temperature from lapse rate and maritime moderation
- **sst** - Sea surface temperature
- **sst_anomaly** - SST deviation from baseline
- **wind** - Wind direction and magnitude (3-cell zonal belts)
- **convergence** - Wind convergence zones
- **precipitation** - Rainfall from latitude belts and moisture advection

### Water Systems (3 layers)
- **discharge** - Rain-weighted water flow accumulation
- **savagery** - Danger/wildness metric from geography
- **regions** - Named geographic regions (landmasses and ocean bodies)

### Magic Systems (5 layers)
- **magic_strength** - Vein intensity (accumulated mana flow)
- **magic_channels** - Mana composition (corpus/mens/anima channels)
- **magic_flow** - Direction and speed of mana currents
- **veins** - Leyline vein networks
- **nexuses** - Magical nexus pole locations

### Biomes & Biology (2 layers)
- **biomes** - Soft biome distribution weighted by climate
- **biome_regions** - Named biome regions (forest, plains, etc.)

## Seed Parameters

- **Grid Size**: 100×100 gameplay tiles
- **Render Resolution**: 512×512 (producing 1024×1024 PNG output)
- **Scale**: 2 pixels per node

## Color Legend

Each layer uses domain-specific coloring:
- **Elevation**: Blue (ocean) → Brown (mountains)
- **Plates**: Distinct colors per plate
- **Temperature**: Blue (cold) → Red (hot)
- **Precipitation**: Light (dry) → Dark (wet)
- **Biomes**: Distinct colors per biome type
- **Magic**: Gradient showing mana concentration and flow

## How to Use

View any layer by opening its PNG file:
```bash
# View a specific layer
open output/seed_layers/seed_42/elevation.png

# Compare the same layer across different seeds
open output/seed_layers/seed_*/elevation.png
```

## Generation Script

The images were generated using `scripts/generate_seed_layers.py`:
```bash
python scripts/generate_seed_layers.py
```

This script generates all layers for seeds [42, 123, 456, 789, 999] and organizes them by seed number.

## Layer Pipeline Order

The layers represent the order of the worldgen pipeline:
1. Plates → Tectonic generation
2. Uplift → Mountain building
3. Drainage → Water flow
4. Volcanism → Hotspots and arcs
5. Climate (Latitude, Temperature, Precipitation)
6. Water Systems
7. Magic Systems
8. Biomes → Final land cover

## Total Statistics

- **Seeds**: 5
- **Layers per seed**: 25
- **Total images**: 125
- **Image size**: 1024×1024 pixels each
- **Approximate storage**: ~50-100 MB (PNG compressed)
