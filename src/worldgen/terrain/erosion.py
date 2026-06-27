import numpy as np

from src.worldgen.config.worldgen_config import ErosionConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.geometry.torus import torus_distance
from src.worldgen.types import Float64Array, Int32Array, IntPArray
from src.worldgen.workspace import Workspace
from src.worldgen.noise.field import FractalField
from src.worldgen.noise.rng import FIELD_EROSION_INIT
from src.worldgen.geometry.field_ops import diffuse
from src.worldgen.terrain.routing import (
    accumulate_drainage,
    compute_receivers,
    priority_flood,
)
from src.worldgen.types import Float64Array, Int32Array


def stream_power_pass(
    *,
    z: Float64Array,
    z_route: Float64Array,
    receiver: Int32Array,
    drainage: Float64Array,
    uplift: Float64Array,
    geometry: MeshGeometry,
    cfg: ErosionConfig,
) -> None:
    """Single implicit stream-powered erosion pass.

    Processes cells from lowest to highest ``z_route`` so every
    receiver's new height is available before its donors are
    processed (Braun & Willett 2013).

    The implicit scheme is unconditionally stable: each cell's new
    height is a weighted average of its uplifted position and the
    receiver's already-updated height, so it can approach but
    never overshoot the receiver.

    Args:
        z: Per-cell ground elevation (mutated in place).
        z_route: Water-surface elevation from ``priority_flood``.
        receiver: Downstream cell id; ``-1`` = base level.
        drainage: Per-cell upstream area from
            ``accumulate_drainage``.
        uplift: Tectonic push-up rate per cell.
        geometry: Torus mesh with CSR adjacency.
        cfg: Erosion parameters (``dt``, ``K``, ``m``).
    """
    order: IntPArray = np.argsort(a=z_route)

    for cell_id in order:
        r: int = int(receiver[cell_id])

        if r < 0:
            # Base-level cell (ocean / pit) — no downstream receiver.
            continue

        if z[cell_id] < z_route[cell_id]:
            # Submerged cell (under lake water) — channel erosion
            # does not occur on submerged rock.
            continue

        # --- implicit stream-power update (Braun & Willett 2013) ---
        # Extract scalars as Python float before arithmetic so
        # every local variable is strongly typed (repo convention).
        z_i: float = float(z[cell_id])
        z_r: float = float(z[r])
        d_i: float = float(drainage[cell_id])
        u_i: float = float(uplift[cell_id])

        # Torus-aware distance from this cell to its receiver.
        dist: float = torus_distance(
            a=geometry.sites[cell_id],
            b=geometry.sites[r],
            width=geometry.width,
            height=geometry.height,
        )

        # Stream-power weight: f = dt * K * A^m / L
        f: float = cfg.dt * cfg.K * (d_i**cfg.m) / dist

        # Implicit update: weighted average of the uplifted height
        # and the receiver's already-computed new height.
        z[cell_id] = (z_i + cfg.dt * u_i + f * z_r) / (1.0 + f)


class ErosionStage:
    """Tectonically-driven terrain: uplift-scaled initial height carved
    by stream-power erosion and hillslope diffusion.

    Pipeline order: ``Mesh → Plates → BoundaryUplift → Erosion → …``
    """

    reads: tuple[str, ...] = ("uplift",)
    writes: tuple[str, ...] = ("drainage", "elevation", "receiver", "z_route")

    def run(self, ctx: Workspace) -> None:
        """Run the full erosion loop and write ``elevation``."""
        cfg: ErosionConfig = ctx.config.erosion
        n: int = ctx.geometry.n_cells

        # --- prerequisites ---
        uplift: Float64Array = ctx.fields.uplift

        # --- initial elevation ---
        # z = uplift * initial_scale + small_noise
        noise_field: FractalField = FractalField(
            sampler=ctx.noise_for("erosion_init"),
            field_id=FIELD_EROSION_INIT,
            octaves=3,
        )

        sites: Float64Array = ctx.geometry.sites
        xs: Float64Array = sites[:, 0]
        ys: Float64Array = sites[:, 1]
        span: float = min(ctx.geometry.width, ctx.geometry.height)
        frequency: float = 4.0 / span

        noise: Float64Array = np.fromiter(
            (
                noise_field.sample(x=float(x_val), y=float(y_val), frequency=frequency)
                for x_val, y_val in zip(xs, ys)
            ),
            dtype=np.float64,
            count=n,
        )

        z: Float64Array = (
            uplift * cfg.initial_scale + noise * cfg.initial_noise_amplitude
        )

        # --- erosion loop ---
        if cfg.iterations <= 0:
            msg: str = "ErosionConfig.iterations must be > 0"
            raise ValueError(msg)

        for _iteration in range(cfg.iterations):
            # Determine provisional ocean cells (lowest percentile by current z).
            n_base: int = max(1, int(cfg.base_level_fraction * n))
            base_cells: Int32Array = np.argpartition(z, n_base)[:n_base].astype(
                np.int32
            )

            z_route: Float64Array = priority_flood(
                geometry=ctx.geometry,
                z=z,
                base_cells=base_cells,
            )
            receiver: Int32Array = compute_receivers(
                geometry=ctx.geometry,
                z_route=z_route,
            )
            drainage: Float64Array = accumulate_drainage(
                receiver=receiver,
                z_route=z_route,
            )
            stream_power_pass(
                z=z,
                z_route=z_route,
                receiver=receiver,
                drainage=drainage,
                uplift=uplift,
                geometry=ctx.geometry,
                cfg=cfg,
            )
            # Hillslope diffusion: one neighbour-mean relaxation pass, so
            # stream-power erosion doesn't sharpen ridges into knife edges.
            z = diffuse(
                geometry=ctx.geometry,
                field=z,
                strength=cfg.diffusion,
                passes=1,
            )

        # --- store on ctx.fields before the last-iteration locals are dropped ---
        # (z_route, receiver, drainage are used inside the loop; the final
        # iteration's values are what flow downstream to FinalizeStage.)
        ctx.fields.elevation = z
        ctx.fields.z_route = z_route
        ctx.fields.receiver = receiver
        ctx.fields.drainage = drainage
