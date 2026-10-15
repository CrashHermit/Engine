# World generation

Run the interactive globe:

```bash
uv run python -m src.worldgen --layer convergence
```

The interactive window has clickable layer selectors on the left. One layer
is active at a time; switching preserves the camera and reuses the same world.
Available layers include `plates`, `intensity`, `magma`, `velocity`,
`convergence`, `divergence`, `shear`, `crust`, `crust-regions`, `crust-field`,
`base-elevation`, and `margin-distance`. `crust` shows oceanic material in blue
and continental material in tan; `crust-regions` shows region ownership;
`crust-field` shows the normalized winning region's flood priority, or the
normalized shaping noise when using Dijkstra. `base-elevation` displays the coastal
base profile in metres with sea level at zero; `margin-distance` is signed
distance as a percentage of circumference (positive continental, negative oceanic). `--layer` sets
the initial view. Use `--seed 123` and `--frequency 20` to control the generated
world and mesh resolution. Offscreen screenshots omit controls.

Plates and crust default to connected, noise-biased priority flooding. Run a
higher-resolution crust view:

```bash
uv run python -m src.worldgen --seed 2026 --frequency 40 --layer crust
```

Each seed gets an independent continuous OpenSimplex fBm field sampled on the
unit sphere. Its cell priority is spherical angular distance from that seed
minus `influence` times its noise. Growth advances through the lowest frontier
barrier; crossing a cell retains the maximum priority encountered along that
growth path. Claimed cells cannot be stolen, and seed cells are protected.
This is competitive, graph-based flooding, not ordinary Voronoi assignment or
a globally optimal minimax partition. Every region stays connected to its seed.
Ownership remains discrete; changing mesh resolution can change the geography.

Plate and crust noise are independent of each other and of magma. Magma still
drives plate motion, but does not shape regions when flooding. The existing
sampling streams are preserved; a separate plate-growth noise stream is appended.
Production uses seeded streams rather than the arithmetic world-seed mapping
used by the temporary gallery experiments, so their exact maps can differ.

`PlateConfig.flood` and `CrustConfig.flood` each contain a `PriorityFloodConfig`:
influence `1.1`, five octaves, base frequency `1.4`, lacunarity `2.0`, and
persistence `0.6`. All regions use the same algorithm and settings, with distinct
noise realizations. The CLI independently exposes `--plate-flood-influence` and
`--crust-flood-influence`.

The original distance-weighted Dijkstra algorithm is retained as
`field.partition.weighted_regions`. Select either method independently with
`--plate-growth` and `--crust-growth`, or set each config's `growth_method`:

```bash
uv run python -m src.worldgen --plate-growth dijkstra --crust-growth dijkstra \
  --plate-irregularity 10 --crust-irregularity 10 --layer crust
```

The irregularity flags apply only to Dijkstra, defaulting to `1`. Low field
values are cheap to cross and high values costly; strength controls cost
contrast, not boundary jaggedness. Flood influence is a separate parameter.

Save a diagnostic without opening a window:

```bash
uv run python -m src.worldgen --layer shear --off-screen --screenshot /tmp/shear.png
```

Boundary interactions evaluate both plates' rotation at the same normalized
edge midpoint. Convergence and divergence are the closing and opening components
across the boundary; shear is the unsigned component along it. Mixed convergence
and shear are retained. The three interaction views use the same color range,
in procedural rotation units, not physical velocities. Bright lines indicate
stronger interaction; dark lines indicate weak or absent interaction.

For Dijkstra, plates use magma intensity and independent crust regions use their
own shaping field to set spherical-distance traversal costs. Each edge's geometric
distance is multiplied by `1 + irregularity_strength * average(endpoint field
values)`. The generic Dijkstra partitioner and its original cost model are unchanged.
`WorldgenConfig.geology` composes `MagmaConfig`, `PlateConfig`, and `CrustConfig`
as `magma`, `plates`, and `crust` respectively. Crust defaults to 4 continental
and 11 oceanic seeds. Its Dijkstra noise settings remain `octaves=3`,
`base_frequency=1.0`, `lacunarity=2.0`, and `persistence=0.35`; the separate
`flood` settings apply to priority flooding. Seeds are jointly spaced and randomly
assigned exactly those type counts; cells inherit their region's type.
`GeneratedWorld.geology` retains the flat magma, plate, and boundary arrays and
includes a `crust` result with region IDs, seeds, region types, a continental mask,
and a read-only normalized `shaping_field`. In flood mode that diagnostic samples
each cell's winning region priority; it is not a shared noise or arrival-time field.
Seed counts do not guarantee area percentages or separate continents.
Terrain is a separate, read-only base-elevation field; it does not alter mesh
topology or crust classification.
`WorldgenConfig.terrain` is a `TerrainConfig` with `inland_width_percent=2.0`,
`shelf_width_percent=1.25`, and `slope_width_percent=1.25`. Each independently
specifies a percentage of the globe's circumference; they do not sum to 100%.
Angular edge distances are converted directly to percentages, with no physical
radius or tile-count dependency. Elevation magnitudes are percentages of radius:
`interior_height_percent=0.00942`, `shelf_depth_percent=0.00314`, and
`basin_depth_percent=0.07063`. Depth parameters are positive and subtracted by
the profile. `WorldgenConfig.planet` is a `PlanetConfig` with
`radius_m=6_371_000.0`; these defaults produce approximately +600 m, -200 m,
and -4500 m. A percentage value of `1.0` means 1%, not a fraction of 1.
Generated elevation and `TerrainResult.elevation_range_m` are in metres;
the viewer uses that configured range rather than fixed height limits.
Doubling the radius doubles elevations and implied physical horizontal distances,
without changing unit-sphere noise, ownership, or coastlines. Increasing only
the elevation percentages increases relief. No physical radius is used for noise
sampling. These profile settings are artistic choices, not universal physical
constants. Signed crust-margin distance is a same-class
multi-source Dijkstra approximation initialized at half of each spherical edge
length. The shelf break lies at the crust boundary; the coastline is offset
inland by one shelf width. Increasing mesh resolution samples the intended
widths more finely but does not change their configured scale.

Save a terrain diagnostic:

```bash
uv run python -m src.worldgen --layer base-elevation --off-screen --screenshot /tmp/elevation.png
```

Set the physical planet radius from the CLI:

```bash
uv run python -m src.worldgen --radius-m 12742000 --layer base-elevation
```

Plate generation is composed from `generate_plate_regions`,
`calculate_plate_rotation`, `calculate_plate_velocity`, and
`region_boundary_edges` from `field/partition.py`. The boundary operation accepts
any per-cell region labels, including crust regions or continental/oceanic types.
`generate_plates` returns a named `PlateResult`;
the geology orchestrator computes boundary interactions separately.

Generation assumes valid inputs and outputs. No database is required.
The previous implementation remains in `legacy/` for reference.