# ECS Conversion Guide — "Everything Is an Entity"

> **Audience:** you, doing the coding. Shapes, contracts, file-by-file changes,
> and ordering — not finished code.
> **Supersedes:** the storage assumptions in `docs/ecs-implementation-guide.md`
> (that doc's render/`DescribeSystem` half still applies, but it now reads from
> the hydrated component graph below, not flat `EntityData` fields).
> **Prereq reading:** `docs/representation-ecs-design.md` (D1–D15).

---

## 0. The decisions this guide implements

These were locked in conversation and are **not yet in the design doc** — they
amend it, so they're restated here to survive compaction:

1. **Everything is an entity.** One node role. There is no separate "component",
   "leaf", or "attribute" vertex class. Every node is an `ENTITY` vertex; a
   "component" is just an entity attached to another entity by an **owning** edge.
   *(This reverses the earlier "leaves now, promotable" call and drops the
   character `CORPUS → HAS_ATTRIBUTE → ATTRIBUTE{value}` nested-attribute pattern.)*
2. **Values are properties on the entity node.** `Danger{level: standard}` is an
   entity with a `level` property. Not flecs-extreme (values aren't themselves
   relationships).
3. **Multiplicity via keyed component entities.** Many components of the same
   type = many attached entities, disambiguated by a key property. The old
   `clocks: dict[pillar,int]` becomes N `Clock` entities, each `{pillar, filled}`.
   No blob-on-a-vertex.
4. **Hydration recurses the owned tree fully.** Owning edges form a shallow tree
   (no depth cap, no cycle handling needed). The walk follows **owning** edges
   and stops at **reference** edges (load the target's id, don't chase it). Today
   there are *no* reference edges, so this is "recurse everything"; the rule is
   reserved for the first sideways edge (a curse from a witch, a shared item).
5. **No legacy.** Solo project, no production data → **no migration**. Drop and
   re-seed the DB. Make bold changes.

Carried over from earlier (unchanged, not this slice): coarse **PUT/DROP** delta
grain, **proposal → resolver** LLM-write path, **serial turn-ordered** mutation
(`docs/turn-resolution-concurrency.md`).

---

## 1. Target model

```
Goblin            ENTITY {name: "goblin", kind: creature}
 ├─HAS_COMPONENT─ ENTITY {ctype: danger,       level: standard}
 ├─HAS_COMPONENT─ ENTITY {ctype: disposition,  nature: predatory}
 ├─HAS_COMPONENT─ ENTITY {ctype: stance,       posture: hostile}
 ├─HAS_COMPONENT─ ENTITY {ctype: status,       state: active, broken_pillar: -, returns_when: ""}
 ├─HAS_COMPONENT─ ENTITY {ctype: position,     text: "cave mouth"}
 ├─HAS_COMPONENT─ ENTITY {ctype: threat_channel, channel: corpus}
 ├─HAS_COMPONENT─ ENTITY {ctype: clock,        pillar: exists,  filled: 2}   ← keyed multi-instance
 ├─HAS_COMPONENT─ ENTITY {ctype: clock,        pillar: capable, filled: 1}
 └─HAS_COMPONENT─ ENTITY {ctype: pillar_cap,   pillar: aware,   capacity: 4} (authored profile)
```

- **One vertex type:** `ENTITY` for the root *and* every component.
- **One owning edge:** `HAS_COMPONENT` (new). It is the only edge the hydrator
  recurses. `CONTAINS` (location → entity) stays as placement.
- **Discriminator:** every component carries `ctype` (a `ComponentType` value).
  The root carries `kind` (creature/object) and `name`.
- **A "scene entity" vs a "component"** is told apart by its incoming edge: a
  scene entity has a `CONTAINS` in-edge from a LOCATION; a component has a
  `HAS_COMPONENT` in-edge from another entity. (Both share `VertexType.ENTITY`,
  so do **not** use `list_vertices(ENTITY)` to enumerate scene entities — it now
  returns components too. Enumerate via the location's `CONTAINS` out-edges, as
  `list_entities_at` already does.)

---

## 2. EntityData → component decomposition

The current flat `EntityData` (`core/model/location.py`) maps like this:

| EntityData field | Becomes | Notes |
|---|---|---|
| `name`, `kind` | **root** entity props | identity stays on the root |
| `description` | `ctype=appearance {text}` | authored flavor → component |
| `scene_position` | `ctype=position {text}` | |
| `danger` | `ctype=danger {level}` | one per entity |
| `disposition` | `ctype=disposition {nature}` | one per entity |
| `stance` | `ctype=stance {posture}` | one per entity |
| `status`, `broken_pillar`, `returns_when` | `ctype=status {state, broken_pillar, returns_when}` | one per entity |
| `clocks: dict[pillar,int]` | N × `ctype=clock {pillar, filled}` | **keyed multi-instance** |
| `pillar_profile: dict[pillar,int]` | N × `ctype=pillar_cap {pillar, capacity}` | authored capacities |
| `threat_channels: frozenset` | N × `ctype=threat_channel {channel}` | set membership = N leaves |

> Note `capacity` for a *live* clock is not stored — it's computed from
> `danger` + `pillar_cap` at read time (`pillar_capacity()` in
> `core/mechanic/effect.py`), exactly as today. Only authored caps persist.

---

## 3. Step 1 — model layer

**`src/core/model/database.py`**
- Add `EdgeType.HAS_COMPONENT = "HAS_COMPONENT"`.
- (Keep `ENTITY`; drop the `# PROTOTYPE` comment once this lands.)

**`src/core/model/component.py`** (new, pure)
```python
from enum import StrEnum

class ComponentType(StrEnum):
    APPEARANCE     = "appearance"
    POSITION       = "position"
    DANGER         = "danger"
    DISPOSITION    = "disposition"
    STANCE         = "stance"
    STATUS         = "status"
    CLOCK          = "clock"
    PILLAR_CAP     = "pillar_cap"
    THREAT_CHANNEL = "threat_channel"
```

**Decision — keep `EntityData` as a hydrated *projection* for now.** Don't
rewrite the ~8 consumers (`apply_effect`, `engagement`, `routers`, threat
classify, scaling, …) that read `e.danger`/`e.clocks`/`e.stance` in this slice.
Instead, the service rebuilds `EntityData` from the component graph (§5). The
canonical truth becomes the graph; `EntityData` is an ergonomic read view.
Collapsing it into a generic component-accessor is an explicit later slice (§9).
This keeps the storage conversion self-contained and green.

---

## 4. Step 2 — schema (`src/database/schema.py`)

- **`PROPERTY_TYPES`** — add the component property names: `ctype` (STRING),
  `level`, `posture`, `state`, `broken_pillar`, `returns_when`, `pillar`,
  `channel`, `nature`, `text` (STRING); `filled`, `capacity` (INTEGER). (`kind`,
  `name` already exist.)
- **`VERTEX_SCHEMA[VertexType.ENTITY]`** — replace the flat list with the union
  of root + component props: `["name", "kind", "ctype", "level", "posture",
  "state", "broken_pillar", "returns_when", "pillar", "channel", "nature",
  "text", "filled", "capacity"]`. Remove the old `danger`, `threat_channels`,
  `resolution`, `pillar_profile`, `disposition`, `scene_position`.
  *(ArcadeDB tolerates undeclared properties, but declare the union so the types
  and the `id` index are honest.)*
- **`EDGE_SCHEMA`** — add `EdgeType.HAS_COMPONENT: []`.

> Since there's no migration (decision 5), the simplest path: delete the DB file
> and let `SchemaManager.ensure()` rebuild, then re-seed via worldgen.

---

## 5. Step 3 — entity repository (`src/database/repository/entity.py`)

This is the heart of the conversion. Model the verbs on the existing
`CharacterRepository.add_node`/`add_attribute` pattern.

```python
def add_component(self, owner: Vertex, ctype: ComponentType, **props) -> Vertex:
    """Create a component ENTITY and attach it to `owner` (owning edge)."""
    comp = self._base.create_vertex(VertexType.ENTITY, ctype=ctype, **props)
    self._base.create_edge(EdgeType.HAS_COMPONENT, source=owner, target=comp)
    return comp

def components(self, owner: Vertex, ctype: ComponentType | None = None) -> list[Vertex]:
    """Direct component children, optionally filtered by ctype."""
    comps = [e.get_in() for e in owner.get_out_edges(EdgeType.HAS_COMPONENT)]
    return [c for c in comps if ctype is None or c.get("ctype") == ctype]
```

- **`create_entity(name, kind, components: list[...])`** — create the root
  ENTITY `{name, kind}`, then `add_component(...)` for each. (Replace the current
  flat signature; delete the dead `wound_capacity`/`wound_filled` params that
  aren't even in the schema.)
- **Hydration loader** — `load(root: Vertex) -> EntityNode` recursing
  `HAS_COMPONENT`:
  ```python
  @dataclass
  class EntityNode:
      id: str
      props: dict[str, object]          # incl. ctype / kind / name
      components: list["EntityNode"]
  ```
  Recurse owning edges only (today that's all of them — a tree, so no visited-set
  needed yet; add one when the first reference edge appears, per decision 4).
- **Cascade delete** — walk `HAS_COMPONENT` recursively and delete the whole
  owned subtree, mirroring `CharacterRepository.delete_character`'s `_OWNED_EDGES`
  cascade. Never follow `CONTAINS` (the location isn't owned).
- **Query-by-component (the payoff)** — e.g. "scene entities with a filled
  Capable clock" becomes a traversal over `CONTAINS` → `HAS_COMPONENT` rather
  than a JSON parse. Add helpers as consumers need them.

---

## 6. Step 4 — location service (`src/service/location.py`)

- **`_to_entity_data(root)`** — rebuild `EntityData` from the hydrated component
  graph instead of parsing JSON. Read `danger` from the `danger` component,
  collect `clock` components into `clocks: dict`, read `status`/`stance`, etc.
- **`persist_entity_state(entities)`** — instead of writing a `resolution` JSON
  blob, **upsert components** (this is where PUT/DROP first appears concretely):
  for each entity, set the `filled` on each `clock` component (creating it if the
  player just attacked a new pillar), and set `state`/`broken_pillar`/`stance` on
  the `status`/`stance` components. Removal of a defeated entity stays
  `remove_entity` (now cascading via §5).
- **Delete** `_resolution_to_json`, `_resolution_from_json`, `_profile_from_json`
  — the JSON blob is gone.

---

## 7. Step 5 — spawn / worldgen (`src/service/world.py`)

Wherever entities are created (around `world.py:87`, `description=entity.description`),
compose components via `create_entity(name, kind, components=[...])` instead of
passing flat props. This is the authoring entry point for the new model.

---

## 8. Tests

Pure-ish, DB-backed where needed:
1. **Round-trip** — `create_entity` with danger/stance/two clocks → `load` →
   `_to_entity_data` reproduces the original `EntityData`.
2. **Keyed multi-instance** — two `clock` components with different `pillar`
   keys both survive and rehydrate into the `clocks` dict.
3. **Mutate-and-persist** — fill a clock via `persist_entity_state`, reload,
   assert the `filled` moved (guards the PUT path).
4. **Cascade delete** — deleting a root removes all its component vertices; a
   `CONTAINS`-linked location is untouched.
5. **Enumeration** — `list_entities_at(location)` returns only the 1 scene
   entity, not its N components (the shared-`VertexType` trap from §1).

`uv run pytest` + `ruff check` green before each commit.

---

## 9. Commit sequence

1. Model layer — `ComponentType`, `HAS_COMPONENT` edge, `EntityNode`. *(ships alone)*
2. Schema — ENTITY property union + `HAS_COMPONENT`; drop the old flat props.
3. Entity repo — `add_component` / `components` / `create_entity` / `load` / cascade.
4. Location service — hydrate from components, persist via component upsert,
   delete the JSON helpers. *(the cross-cutting commit)*
5. Worldgen — compose components on spawn; drop & re-seed the DB.

---

## 10. Deferred to later slices (named, not now)

- **Collapse `EntityData` into a generic component-accessor** — once consumers
  are migrated, the projection DTO can go; nodes read components directly.
- **Characters onto the same registry** — apply this exact model to
  `CharacterRepository`, retiring the `CORPUS → ATTRIBUTE` two-hop (decision: no
  legacy, so do it when characters are next touched).
- **PUT/DROP delta edges + `TURN` history (D12–D14)** — the component upsert in
  §6 is the seam; later it emits `CHANGED` edges off a `TURN` vertex.
- **`DescribeSystem` from components** — the render half (other guide) now reads
  the hydrated `EntityNode`/`EntityData` instead of flat fields.
- **Reference edges** — the first sideways edge (curse, shared item) activates
  the owning-vs-reference boundary in the hydrator (decision 4).
