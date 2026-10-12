# World generation

Run the interactive globe:

```bash
uv run python -m src.worldgen --layer convergence
```

Available layers: `plates`, `intensity`, `magma`, `velocity`, `convergence`,
`divergence`, and `shear`. Use `--seed 123` and `--frequency 20` to control
the generated world and mesh resolution.

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

Generation assumes valid inputs and outputs. No database is required.
The previous implementation remains in `legacy/` for reference.