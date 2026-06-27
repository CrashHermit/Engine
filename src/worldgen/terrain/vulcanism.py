"""Vulcanism: subduction arcs, hotspot island chains, and rift/ridge volcanism.

Runs after boundary uplift and before erosion, reading the shared
``BoundaryFacts``.  It contributes edifice height to ``uplift`` (so erosion
dissects and drains the volcanic terrain like everything else), builds a
present-day-activity ``volcanism`` field, and marks discrete ``Volcano`` summits.

Three mechanisms, all keyed off plate type and subduction polarity:

* **Subduction arcs** — convergent boundaries that involve an oceanic plate
  (never continent-continent).  Arc potential is seeded on the *overriding*
  plate's trench cells and BFS-marched inland to ``arc_offset`` hops, so the arc
  sits behind the trench: a continental arc (CONV_OC) inland, an offshore island
  arc (CONV_OO).
* **Hotspots** — fixed plate-interior points whose host plate's drift stamps a
  decaying trail of volcanoes (active head, subsiding tail), i.e. an island
  chain laid out spatially instead of over time.
* **Rifts / ridges** — ocean-ocean divergence raises a mid-ocean ridge (which
  boundary uplift left uncarved); continental rifts get flank volcanism.
"""

import random
from collections import deque
from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from src.worldgen.config.worldgen_config import VulcanismConfig
from src.core.model.environment.terrain.volcano import VolcanoKind, VolcanoStatus
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.terrain.boundaries import BoundaryFacts, BoundaryKind
from src.worldgen.terrain.plate_personalities import PlateProperties
from src.worldgen.types import BoolArray, Float64Array, Int8Array, Int32Array
from src.worldgen.workspace import Workspace
from src.core.model.environment.terrain.volcano import (
    Volcano,
)
from src.worldgen.terrain.boundaries import BoundaryFacts
from src.worldgen.types import BoolArray, Float64Array, Int32Array


@dataclass
class VolcanoSeed:
    """A discrete volcano before it gets a global id (filled by the stage)."""

    cell: int
    kind: VolcanoKind
    status: VolcanoStatus
    chain_id: int
    activity: float
    has_caldera: bool = False


@dataclass
class VulcanismResult:
    """Per-cell contributions plus the discrete volcanoes to materialize."""

    uplift_add: Float64Array  # added to ctx.fields.uplift (>= 0)
    volcanism: Float64Array  # [0,1] present-day activity field
    volcanoes: list[VolcanoSeed]


def _status_from_activity(activity: float) -> VolcanoStatus:
    """Bucket a [0,1] activity level into active / dormant / extinct."""
    if activity > 0.66:
        return VolcanoStatus.ACTIVE
    if activity > 0.33:
        return VolcanoStatus.DORMANT
    return VolcanoStatus.EXTINCT


def _torus_distance(
    a: Float64Array, b: Float64Array, width: float, height: float
) -> float:
    """Minimum-image distance between two sites on the torus."""
    dx: float = abs(float(a[0]) - float(b[0]))
    dy: float = abs(float(a[1]) - float(b[1]))
    dx = min(dx, width - dx)
    dy = min(dy, height - dy)
    return float(np.hypot(dx, dy))


def _stamp_bump(
    *,
    geometry: MeshGeometry,
    uplift_add: Float64Array,
    activity: Float64Array,
    cell: int,
    height: float,
    smear: int,
    falloff: float,
) -> None:
    """Add a small radial edifice bump around ``cell`` (BFS to ``smear`` hops)."""
    uplift_add[cell] += height
    activity[cell] = max(activity[cell], min(1.0, height))
    if smear <= 0:
        return
    frontier: list[int] = [cell]
    level_height: float = height
    hop: int = 0
    seen: set[int] = {cell}
    while frontier and hop < smear:
        level_height *= falloff
        hop += 1
        nxt: list[int] = []
        for c in frontier:
            for nb in geometry.neighbors_of(cell_id=c):
                nb_i: int = int(nb)
                if nb_i in seen:
                    continue
                seen.add(nb_i)
                uplift_add[nb_i] += level_height
                activity[nb_i] = max(activity[nb_i], min(1.0, level_height))
                nxt.append(nb_i)
        frontier = nxt


def _subduction_arcs(
    *,
    geometry: MeshGeometry,
    facts: BoundaryFacts,
    plate_id: Int32Array,
    cfg: VulcanismConfig,
) -> Float64Array:
    """Return per-cell arc activity (also the arc uplift driver, pre-scale).

    Seed the trench (overriding-side convergent cells, OO/OC only — never CC),
    then BFS inland *within the overriding plate* and shape a band peaking at
    ``arc_offset`` hops from the trench.
    """
    n: int = geometry.n_cells
    conv: Float64Array = facts.convergence
    kind: Int8Array = facts.conv_kind

    subducting: BoolArray = (
        facts.is_overriding
        & (conv > 0.0)
        & ((kind == int(BoundaryKind.CONV_OO)) | (kind == int(BoundaryKind.CONV_OC)))
    )

    hop: Int32Array = np.full(n, -1, dtype=np.int32)
    src_conv: Float64Array = np.zeros(n, dtype=np.float64)
    max_hop: int = cfg.arc_offset + cfg.arc_width + 1

    queue: deque[int] = deque()
    for cell in np.flatnonzero(subducting):
        c: int = int(cell)
        hop[c] = 0
        src_conv[c] = float(conv[c])
        queue.append(c)

    while queue:
        c = queue.popleft()
        if hop[c] >= max_hop:
            continue
        plate_c: int = int(plate_id[c])
        for nb in geometry.neighbors_of(cell_id=c):
            nb_i: int = int(nb)
            if hop[nb_i] != -1:
                continue
            if int(plate_id[nb_i]) != plate_c:
                continue  # stay on the overriding plate
            hop[nb_i] = hop[c] + 1
            src_conv[nb_i] = src_conv[c]
            queue.append(nb_i)

    activity: Float64Array = np.zeros(n, dtype=np.float64)
    reached: BoolArray = hop >= 0
    band: Float64Array = np.maximum(
        0.0, 1.0 - np.abs(hop - cfg.arc_offset) / float(cfg.arc_width + 1)
    )
    activity[reached] = src_conv[reached] * band[reached]
    # Continent-continent collision cells are amagmatic: an arc marching inland
    # off a neighbouring subduction zone must not light up the collision seam
    # (no volcanoes in the Himalayas).
    activity[kind == int(BoundaryKind.CONV_CC)] = 0.0
    return activity


def _hotspot_trails(
    *,
    geometry: MeshGeometry,
    facts: BoundaryFacts,
    plate_id: Int32Array,
    properties: PlateProperties,
    tree: cKDTree,
    cfg: VulcanismConfig,
    rng: random.Random,
    uplift_add: Float64Array,
    activity: Float64Array,
) -> list[VolcanoSeed]:
    """Place hotspots and stamp drift-aligned decaying volcano trails."""
    n: int = geometry.n_cells
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    span: float = max(width, height)
    is_continental: BoolArray = properties.is_continental

    # Candidates: plate interiors (away from boundaries), oceanic-biased.
    boundary: BoolArray = (facts.convergence > 0.0) | (facts.divergence > 0.0)
    interior: Int32Array = np.flatnonzero(~boundary)
    if interior.size == 0:
        return []

    score: dict[int, float] = {}
    for cell in interior:
        c: int = int(cell)
        oceanic: bool = not bool(is_continental[int(plate_id[c])])
        weight: float = 1.0 if oceanic else cfg.hotspot_continental_fraction
        score[c] = rng.random() * weight

    ordered: list[int] = sorted(score, key=lambda c: score[c], reverse=True)
    min_d: float = cfg.hotspot_spacing * span
    hotspots: list[int] = []
    for c in ordered:
        if len(hotspots) >= cfg.hotspot_count:
            break
        if all(
            _torus_distance(sites[c], sites[h], width, height) >= min_d
            for h in hotspots
        ):
            hotspots.append(c)

    volcanoes: list[VolcanoSeed] = []
    used: set[int] = set()
    for chain_id, hc in enumerate(hotspots):
        drift: Float64Array = properties.drift[int(plate_id[hc])]
        origin: Float64Array = sites[hc]
        for k in range(cfg.chain_length):
            offset: float = k * cfg.chain_step * span
            pos = np.array(
                [
                    (origin[0] + offset * drift[0]) % width,
                    (origin[1] + offset * drift[1]) % height,
                ]
            )
            _dist, idx = tree.query(x=pos)
            cell = int(idx)
            if cell in used:
                continue
            used.add(cell)
            decay: float = cfg.chain_decay**k
            height_k: float = cfg.hotspot_peak_uplift * decay
            _stamp_bump(
                geometry=geometry,
                uplift_add=uplift_add,
                activity=activity,
                cell=cell,
                height=height_k,
                smear=cfg.volcano_smear,
                falloff=cfg.bump_falloff,
            )
            volcanoes.append(
                VolcanoSeed(
                    cell=cell,
                    kind=VolcanoKind.SHIELD,
                    status=_status_from_activity(decay),
                    chain_id=chain_id,
                    activity=decay,
                )
            )
    return volcanoes


def _greedy_spaced(
    *,
    geometry: MeshGeometry,
    score: Float64Array,
    candidate: BoolArray,
    spacing_frac: float,
    exclude: set[int],
) -> list[int]:
    """Accept highest-score candidate cells with a minimum torus spacing."""
    sites: Float64Array = geometry.sites
    width: float = geometry.width
    height: float = geometry.height
    min_d: float = spacing_frac * max(width, height)

    order: Int32Array = np.argsort(-score, kind="stable")
    accepted: list[int] = []
    for cell in order:
        c: int = int(cell)
        if not candidate[c] or score[c] <= 0.0 or c in exclude:
            continue
        if all(
            _torus_distance(sites[c], sites[a], width, height) >= min_d
            for a in accepted
        ):
            accepted.append(c)
    return accepted


def compute_vulcanism(
    *,
    geometry: MeshGeometry,
    facts: BoundaryFacts,
    plate_id: Int32Array,
    properties: PlateProperties,
    cfg: VulcanismConfig,
    seed: int,
) -> VulcanismResult:
    """Compute uplift contribution, the volcanism field, and discrete volcanoes."""
    n: int = geometry.n_cells
    rng: random.Random = random.Random(seed)
    tree: cKDTree = cKDTree(
        data=geometry.sites, boxsize=[geometry.width, geometry.height]
    )

    uplift_add: Float64Array = np.zeros(n, dtype=np.float64)
    activity: Float64Array = np.zeros(n, dtype=np.float64)

    # --- 1. subduction arcs ---
    arc_activity: Float64Array = _subduction_arcs(
        geometry=geometry, facts=facts, plate_id=plate_id, cfg=cfg
    )
    uplift_add += cfg.arc_uplift * arc_activity
    activity = np.maximum(activity, arc_activity)

    # --- 2. mid-ocean ridges (OO divergence, raised — boundary uplift skipped it) ---
    ridge: Float64Array = np.where(
        facts.div_kind == int(BoundaryKind.DIV_OO), facts.divergence, 0.0
    )
    uplift_add += cfg.ridge_uplift * ridge
    activity = np.maximum(activity, ridge)

    # --- 3. continental rift flank volcanism (no extra uplift; valley already cut) ---
    rift_mask: BoolArray = (facts.div_kind == int(BoundaryKind.DIV_OC)) | (
        facts.div_kind == int(BoundaryKind.DIV_CC)
    )
    rift_activity: Float64Array = np.where(
        rift_mask, cfg.rift_flank_strength * facts.divergence, 0.0
    )
    activity = np.maximum(activity, rift_activity)

    # --- 4. hotspots (stamp trails into uplift_add and activity directly) ---
    volcanoes: list[VolcanoSeed] = _hotspot_trails(
        geometry=geometry,
        facts=facts,
        plate_id=plate_id,
        properties=properties,
        tree=tree,
        cfg=cfg,
        rng=rng,
        uplift_add=uplift_add,
        activity=activity,
    )
    used: set[int] = {v.cell for v in volcanoes}

    # --- 5. arc volcanoes (stratovolcanoes), grouped by connected arc band ---
    arc_band: BoolArray = arc_activity > 0.0
    arc_labels: Int32Array = _components(geometry=geometry, mask=arc_band)
    chain_base: int = cfg.hotspot_count
    arc_cells: list[int] = _greedy_spaced(
        geometry=geometry,
        score=arc_activity,
        candidate=arc_band,
        spacing_frac=cfg.arc_volcano_spacing,
        exclude=used,
    )
    for c in arc_cells:
        norm: float = float(min(1.0, arc_activity[c]))
        status: VolcanoStatus = (
            VolcanoStatus.DORMANT
            if rng.random() < cfg.dormant_fraction
            else VolcanoStatus.ACTIVE
        )
        volcanoes.append(
            VolcanoSeed(
                cell=c,
                kind=VolcanoKind.STRATO,
                status=status,
                chain_id=chain_base + int(arc_labels[c]),
                # Arc cones read as present-day active ground even where the raw
                # convergence band is faint, so floor their activity.
                activity=max(norm, 0.34),
            )
        )
        used.add(c)

    # --- 6. ridge / rift fissure volcanoes (solitary) ---
    fissure_score: Float64Array = np.maximum(ridge, rift_activity)
    fissure_cells: list[int] = _greedy_spaced(
        geometry=geometry,
        score=fissure_score,
        candidate=fissure_score > 0.0,
        spacing_frac=cfg.rift_volcano_spacing,
        exclude=used,
    )
    for c in fissure_cells:
        volcanoes.append(
            VolcanoSeed(
                cell=c,
                kind=VolcanoKind.FISSURE,
                status=VolcanoStatus.ACTIVE,
                chain_id=-1,
                activity=float(min(1.0, max(0.5, fissure_score[c]))),
            )
        )
        used.add(c)

    # --- caldera flag (a crater lake gets injected later for land calderas) ---
    for vseed in volcanoes:
        vseed.has_caldera = rng.random() < cfg.caldera_fraction

    # --- normalize the activity field to [0,1] ---
    peak: float = float(activity.max())
    volcanism: Float64Array = activity / peak if peak > 0.0 else activity
    np.clip(volcanism, 0.0, 1.0, out=volcanism)

    return VulcanismResult(
        uplift_add=uplift_add, volcanism=volcanism, volcanoes=volcanoes
    )


def _surfacing_mask(*, geometry: MeshGeometry, is_land: BoolArray) -> BoolArray:
    """Cells that breached: on land, or coastal (a land neighbour).

    A discrete landmark volcano has to be somewhere you could stand or sail to.
    Land summits qualify directly; a just-submarine summit one cell off a coast
    qualifies too, so an island edifice whose summit cell happens to fall on the
    ocean side of the Voronoi split is not lost to mesh resolution.
    """
    surfacing: BoolArray = is_land.copy()
    cell: int
    for cell in np.flatnonzero(~is_land):
        c: int = int(cell)
        for nb in geometry.neighbors_of(cell_id=c):
            if is_land[int(nb)]:
                surfacing[c] = True
                break
    return surfacing


def select_landmark_volcanoes(
    *,
    geometry: MeshGeometry,
    candidates: list[VolcanoSeed],
    is_land: BoolArray,
    cfg: VulcanismConfig,
) -> list[VolcanoSeed]:
    """Thin the pre-erosion candidate set down to iconic landmark volcanoes.

    Candidates are generated *before* erosion and sea level, so they trace every
    submarine arc, ridge, and seamount — a near-continuous string of points
    along every plate boundary.  A ``Volcano`` feature, though, should be an
    *iconic landmark*: an edifice that actually breached (land or coastal) and
    is prominent enough to name.  Selection runs in three steps:

    1. **Per chain**, keep only breached members, capped to the strongest
       ``max_per_chain`` (the chain head — highest down-trail activity).  A
       chain that stayed entirely submarine contributes nothing: an underwater
       seamount is not a landmark (the volcanism *field* still carries it).
    2. **Solitary** fissures: keep only the ones that breached.
    3. **Global cap**: keep only the ``max_volcanoes`` most prominent of those
       (land summits over coastal, then by activity), so a single busy arc can't
       flood the map.  The result is a handful of Vesuvius/Fuji landmarks, not
       a scatter of dozens.

    Selection only filters and never rewrites a candidate (kind / chain /
    activity / caldera preserved), and the original candidate order is kept so a
    chain's ascending id stays its trail order.

    Args:
        geometry: Torus mesh (for the coastal test).
        candidates: Pre-erosion volcano seeds from :func:`compute_vulcanism`.
        is_land: Finalised land mask (so surfacing is known).
        cfg: Vulcanism config (``max_per_chain``, ``max_volcanoes``).

    Returns:
        The kept seeds, in their original candidate order.
    """
    if not candidates:
        return []

    surfacing: BoolArray = _surfacing_mask(geometry=geometry, is_land=is_land)

    chains: dict[int, list[int]] = {}
    solitary: list[int] = []
    idx: int
    for idx, seed in enumerate(candidates):
        if seed.chain_id < 0:
            solitary.append(idx)
        else:
            chains.setdefault(seed.chain_id, []).append(idx)

    kept_idx: list[int] = []

    # Chains (arcs, hotspot trails): keep the breached members, capped to the
    # strongest few.  Submarine-only chains are dropped (no anchor — not a
    # landmark); the volcanism field keeps the submarine picture.
    for members in chains.values():
        breached: list[int] = [i for i in members if surfacing[candidates[i].cell]]
        if not breached:
            continue
        if len(breached) > cfg.max_per_chain:
            breached = sorted(
                breached, key=lambda i: candidates[i].activity, reverse=True
            )[: cfg.max_per_chain]
        kept_idx.extend(breached)

    # Solitary fissures: only the ones that actually breached.
    kept_idx.extend(i for i in solitary if surfacing[candidates[i].cell])

    # Global prominence cap: prefer land summits over coastal, then activity.
    def _prominence(i: int) -> tuple[int, float]:
        return (int(is_land[candidates[i].cell]), candidates[i].activity)

    if len(kept_idx) > cfg.max_volcanoes:
        kept_idx = sorted(kept_idx, key=_prominence, reverse=True)[
            : cfg.max_volcanoes
        ]

    keep_set: set[int] = set(kept_idx)
    return [seed for i, seed in enumerate(candidates) if i in keep_set]


def _components(*, geometry: MeshGeometry, mask: BoolArray) -> Int32Array:
    """Label connected components of ``mask`` (BFS); -1 outside the mask."""
    n: int = len(mask)
    labels: Int32Array = np.full(n, -1, dtype=np.int32)
    component: int = -1
    for cell_id in range(n):
        if not mask[cell_id] or labels[cell_id] >= 0:
            continue
        component += 1
        queue: deque[int] = deque([cell_id])
        labels[cell_id] = component
        while queue:
            current: int = queue.popleft()
            for nb in geometry.neighbors_of(cell_id=current):
                nb_i: int = int(nb)
                if labels[nb_i] >= 0 or not mask[nb_i]:
                    continue
                labels[nb_i] = component
                queue.append(nb_i)
    return labels


class VulcanismStage:
    """Add volcanic uplift, write the volcanism field, stash volcano candidates."""

    reads: tuple[str, ...] = ("plate_id", "uplift")
    writes: tuple[str, ...] = ("volcanism",)

    def run(self, ctx: Workspace) -> None:
        """Contribute edifice height and the volcanism field (pre-erosion)."""
        cfg: VulcanismConfig = ctx.config.vulcanism

        facts: BoundaryFacts | None = ctx.scratch.boundary_facts
        if facts is None:
            msg: str = "boundary_facts must be set before VulcanismStage"
            raise RuntimeError(msg)
        plate_id: Int32Array = ctx.fields.plate_id
        properties: PlateProperties | None = ctx.scratch.plate_properties
        if properties is None:
            msg = "plate_properties must be set before VulcanismStage"
            raise RuntimeError(msg)
        uplift: Float64Array = ctx.fields.uplift

        result = compute_vulcanism(
            geometry=ctx.geometry,
            facts=facts,
            plate_id=plate_id,
            properties=properties,
            cfg=cfg,
            seed=ctx.seed_for("vulcanism"),
        )

        # Add edifice height; clamp so nothing goes negative.
        uplift += result.uplift_add
        np.maximum(uplift, 0.0, out=uplift)
        ctx.fields.volcanism = result.volcanism

        # Discrete volcanoes are materialised after finalize, when we know which
        # edifices breached (see VolcanoesStage).
        ctx.scratch.volcano_candidates = result.volcanoes


class VolcanoesStage:
    """Turn surfaced candidates into discrete ``Volcano`` landmarks (post-finalize)."""

    reads: tuple[str, ...] = ("is_land",)
    writes: tuple[str, ...] = ("is_volcano", "volcano_id")

    def run(self, ctx: Workspace) -> None:
        """Select landmark volcanoes and write their fields and objects."""
        cfg: VulcanismConfig = ctx.config.vulcanism
        candidates: list[VolcanoSeed] = ctx.scratch.volcano_candidates or []

        is_land: BoolArray = ctx.fields.is_land

        selected: list[VolcanoSeed] = select_landmark_volcanoes(
            geometry=ctx.geometry,
            candidates=candidates,
            is_land=is_land,
            cfg=cfg,
        )

        n: int = ctx.geometry.n_cells
        is_volcano: BoolArray = np.zeros(n, dtype=bool)
        volcano_id: Int32Array = np.full(n, -1, dtype=np.int32)
        volcanoes: list[Volcano] = []
        for new_id, seed in enumerate(selected):
            volcanoes.append(
                Volcano(
                    id=new_id,
                    cell=seed.cell,
                    kind=seed.kind,
                    status=seed.status,
                    chain_id=seed.chain_id,
                    activity=seed.activity,
                    has_caldera=seed.has_caldera,
                )
            )
            is_volcano[seed.cell] = True
            volcano_id[seed.cell] = new_id

        ctx.fields.is_volcano = is_volcano
        ctx.fields.volcano_id = volcano_id
        ctx.outputs.volcanoes = volcanoes
