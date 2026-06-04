# ECS Implementation Guide — Slice 1: The Description System

> **Audience:** the person writing the code (you). This is a step-by-step build
> guide, not finished code — it gives the shapes, placements, contracts, and
> call sites so the implementation is unambiguous, and leaves the typing to you.
> **Source of truth:** `docs/representation-ecs-design.md` (decisions D1–D15).
> **This slice implements:** D1, D2, D3, D4, D6, D7, D8 — the *render half* of the
> substrate. It deliberately does **not** touch graph/DB storage (D5
> component-vertices) or episodic memory (D12–D14); those are later slices,
> sketched at the end.

---

## 0. Why this slice first

Per the design doc §7, the `Description` value types + `DescribeSystem` are
"pure and shippable alone," and `EntityData` is the natural first entity to
re-platform. Two concrete payoffs:

1. **Kills the ad-hoc format string.** Today `coordinator._build_graph_state`
   (`src/session/coordinator.py:245`) builds entity prose once:
   ```python
   entities_at_location = [
       f"{e.name}: {e.description}. Location: {e.scene_position}" for e in entities
   ]
   ```
   and ~8 nodes do `"\n".join(state.entities_at_location)`. This is the coupling
   D7 wants gone.
2. **Fixes a real staleness bug.** That list is frozen at turn-start, but
   `engagement` (stance) and `apply_effect` (clocks/status) mutate entities
   *mid-turn*. The narrator currently describes the pre-turn scene. A
   render-on-access computed property fixes this for free.

---

## 1. Layer & placement map

Respect code-style §2 (core/model is pure; it may **not** import core/mechanic):

| Artifact | Lives in | Layer rule |
|---|---|---|
| `FacetKind`, `Facet`, `Description` (+ `render()`) | `src/core/model/description.py` | pure value types — **no** mechanic imports |
| `describe_entity()` + handler registry (the `DescribeSystem`) | `src/core/mechanic/describe.py` | a *pure system*; may import `core/model` (both `description` and `location.EntityData`) |
| `GraphState.entities_prose` computed property | `src/state.py` | already imports `core/mechanic`, so it may call `describe_entity` |

`Description.render()` is pure string formatting → it stays in `core/model`. The
*system* that decides which facets an entity has (and needs `pillar_capacity`
etc. from `core/mechanic`) is `describe_entity` in `core/mechanic`. That split is
the whole point of D6.

---

## 2. Step 1 — pure value types (`core/model/description.py`)

```python
from dataclasses import dataclass, field
from enum import StrEnum

class FacetKind(StrEnum):
    """D3 starter set. Fixed render order is the declaration order below."""
    IDENTITY   = "identity"
    APPEARANCE = "appearance"
    MANNER     = "manner"
    STATE      = "state"
    CAPABILITY = "capability"
    SETTING    = "setting"

@dataclass(frozen=True)
class Facet:
    kind: FacetKind
    text: str

@dataclass
class Description:
    facets: list[Facet] = field(default_factory=list)

    def render(self) -> str:
        ...  # see §6 for the exact format contract
```

Contract notes:
- `FacetKind` must be a `StrEnum` (house style) and **extensible** (D2): later
  slices add `FORM`, `SENSATION`, etc. — appending is non-breaking.
- `Facet` is frozen (it's an immutable value). `Description` is a thin holder.
- **No visibility field** (D9 — deferred). Just `kind + text`.

---

## 3. Step 2 — the DescribeSystem (`core/mechanic/describe.py`)

This is the part that earns the "register a handler, never edit a god-method"
property (D6). `EntityData` is not yet decomposed into component vertices (that's
D5, a later slice), so for now each handler reads the *field* that will later
become a component. The registry shape keeps the migration honest: when a field
becomes a real component vertex, only its handler changes.

```python
from collections.abc import Callable
from src.core.model.description import Description, Facet, FacetKind
from src.core.model.location import EntityData

EntityHandler = Callable[[EntityData], list[Facet]]
_HANDLERS: list[EntityHandler] = []

def _handler(fn: EntityHandler) -> EntityHandler:
    _HANDLERS.append(fn)
    return fn

# one handler per logical component — see the mapping table in §5
@_handler
def _identity(e: EntityData) -> list[Facet]:
    return [Facet(FacetKind.IDENTITY, e.name)]

# ... _appearance, _setting, _manner, _state, _capability ...

def describe_entity(e: EntityData) -> Description:
    return Description([f for h in _HANDLERS for f in h(e)])
```

Rules for handlers:
- Each handler owns **one** logical component and returns **zero or more**
  facets. Returning `[]` (e.g. no clocks filled → no damage STATE facet) is
  normal and must be safe.
- Handlers are **pure** and **total** — never raise on default/empty entities
  (a freshly-spawned `EntityData` with default fields must render cleanly).
- Handlers may import from `core/mechanic` (e.g. `pillar_capacity` from
  `effect.py`) since they live there. Keep that to the `STATE`/`CAPABILITY`
  scalar handlers that genuinely need lookups.
- Do **not** branch on `EntityKind` inside one mega-handler; prefer a handler
  that no-ops for objects (e.g. the clock/STATE handler returns `[]` when
  `kind != CREATURE`). Composition over conditionals.

---

## 4. Step 3 — the computed property (`src/state.py`)

Add to `GraphState` (D7 — render on access, always fresh):

```python
@property
def entities_prose(self) -> str:
    from src.core.mechanic.describe import describe_entity
    return "\n\n".join(describe_entity(e).render() for e in self.scene_entities)
```

- Import `describe_entity` **inside** the property (or at module top if no cycle)
  — `state.py` already imports `core/mechanic`, but a function-local import is the
  safe choice against any future cycle through `describe.py`.
- Join entities with a blank line so multi-line per-entity blocks stay readable.
- This reads `scene_entities` (the structured spine) — which IS kept fresh
  through mid-turn mutation — so the staleness bug is gone.

---

## 5. Facet mapping — EntityData field → FacetKind

This is the actual content of the handlers. EntityData fields
(`src/core/model/location.py:14`):

| EntityData field | FacetKind | Handler notes |
|---|---|---|
| `name` | IDENTITY | leading line; always present |
| `kind` (CREATURE/OBJECT) | IDENTITY | optional — only annotate OBJECT ("(object)"); creatures implied |
| `description` (authored free text) | APPEARANCE | D1 inert authored flavor — passed through verbatim |
| `scene_position` | SETTING | the `Location:` of the old f-string |
| `disposition` | MANNER | static nature (predatory/skittish…); skip if NEUTRAL to reduce noise |
| `stance` (unaware/wary/hostile) | STATE | current posture; the aggro axis |
| `status` (active/suspended/gone) | STATE | annotate only non-ACTIVE (suspended/gone) |
| `clocks` + `broken_pillar` | STATE | per-pillar damage: `Capable 2/4`, `(Aware broken)`; uses `pillar_capacity` |
| `danger` | CAPABILITY | threat ceiling (low/standard/elite/deadly) |
| `threat_channels` | CAPABILITY | how it threatens (corpus/mens/anima) |
| `returns_when` | — | omit (internal re-engage condition; not player-facing prose) |
| `pillar_profile` | — | omit (static config / immunities; revisit if the classifier needs it) |
| `id` | — | never rendered |

Keep STATE handlers terse — the classifier weights STATE/CAPABILITY (D3/D8), so
favor parseable tags (`Capable 2/4`, `hostile`) over prose.

---

## 6. Render format contract (`Description.render()`, D8)

- **Labelled lines, fixed kind order** = the `FacetKind` declaration order:
  IDENTITY → APPEARANCE → MANNER → STATE → CAPABILITY → SETTING.
- **IDENTITY leads and is bare** (the name, no label) — matches the existing
  `Name: …` convention.
- **One line per kind.** Same-kind facets joined with `; ` (or `, `).
- **Kinds with no facets are skipped** (no empty `Manner:` line).
- Non-IDENTITY lines are `Label: text` with the kind title-cased.

Worked example (a wounded, engaged creature):
```
Wolf
Appearance: a lean grey wolf, hackles raised.
Manner: predatory.
State: hostile; favoring a torn flank (Capable 2/4).
Capability: standard threat; strikes via corpus.
Setting: crouched at the cave mouth.
```
A freshly-spawned default entity must still render to at least its IDENTITY line
with no crash and no stray labels.

---

## 7. Step 4 — swap the consumers

Every node currently declares an `entities_at_location` InputField and does:
```python
entities = "\n".join(state.entities_at_location) if state.entities_at_location else ""
```
Replace that local with `state.entities_prose` (the InputField name on the
signature can stay — only the value source changes). Call sites:

- `src/node/intent/question_generator.py`
- `src/node/intent/alignment_router.py`
- `src/node/frame/roll_gate.py`
- `src/node/frame/segmenter.py`
- `src/node/frame/duration.py`
- `src/node/resolve/narrator.py`
- `src/node/resolve/held_planner.py`
- `src/node/resolve/final_planner.py`

Do them all in one pass so no consumer reads the stale list while another reads
the fresh prop.

---

## 8. Step 5 — coordinator cleanup

In `src/session/coordinator.py:245`:
- **Delete** the `entities_at_location = [f"{e.name}: …"]` list build and stop
  passing `entities_at_location=` into `GraphState(...)`. Keep passing
  `scene_entities=list(entities)` — that's the spine `entities_prose` renders.
- **Remove** the `entities_at_location` field from `GraphState` (`state.py:35`)
  once no consumer references it. (Grep `entities_at_location` to confirm zero
  hits before deleting the field.)

> Note: the TUI (`src/tui/...`) reads `entity.description` directly off the DB
> model — that is **out of scope** here and should keep working untouched. This
> slice only changes the *LLM-facing* render path.

---

## 9. Tests

Add `test/.../test_describe.py` (pure, no LLM, no DB):

1. **Default entity renders cleanly** — `describe_entity(EntityData(name="X", description="", scene_position=""))` → render contains the IDENTITY line, no empty labels, no exception.
2. **Field → facet mapping** — an entity with a filled `Capable` clock, HOSTILE stance, PREDATORY disposition renders the expected STATE/MANNER/CAPABILITY lines.
3. **Kind order is fixed** — assert APPEARANCE precedes STATE precedes SETTING regardless of handler registration order.
4. **Empty kinds skipped** — a NEUTRAL/UNAWARE object yields no MANNER line.
5. **Freshness (integration-ish, optional)** — mutate a `scene_entities` entry's stance, assert `state.entities_prose` reflects it (guards the bug this slice fixes).
6. **Handler registry is append-only safe** — registering a new handler doesn't reorder render output (order comes from `FacetKind`, not registration).

`uv run pytest` + `ruff check` should be green before committing.

---

## 10. Suggested commit sequence

Each step is independently green:

1. `core/model/description.py` + its unit tests (value types + render). *Ships alone.*
2. `core/mechanic/describe.py` (handlers + `describe_entity`) + its tests.
3. `GraphState.entities_prose` property.
4. Swap the 8 consumers + drop the coordinator f-string and the
   `entities_at_location` field. *(This is the one cross-cutting commit.)*

---

## 11. What this slice defers (and where it goes next)

- **D5 — component-as-vertex storage.** EntityData is still one dataclass. The
  next slice decomposes it into component vertices in `schema.py` +
  `EntityRepository` + a hydration loader ("load entity with all components").
  Because the handlers in §3 are already per-component, that migration changes
  handlers one at a time, not the render contract.
- **D10 second writer — structured LLM updates.** Once components are vertices,
  the LLM emits component writes (not prose-as-truth).
- **D12–D14 — episodic memory.** `TURN` vertices on a `NEXT_TURN` chain +
  `CHANGED` delta-edges. **Blocked** (§7): the delta payload schema waits on the
  part/mutation-verb system. Don't start this until that lands.
- **`character_prose` / world prose.** Same pattern as `entities_prose`, applied
  to `CharacterData`/`WorldData` when those areas are next touched (D15
  opportunistic).

The invariant to carry forward: **structured truth is canonical; the prose handed
to the LLM is always rendered on access, never stored** (D1/D4/D7).
