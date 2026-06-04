# ECS Conversion Guide — "Everything Is an Entity", Values as Relationships

> **Audience:** you, doing the coding. Shapes, contracts, file-by-file changes,
> and ordering — not finished code.
> **Supersedes:** the storage assumptions in `docs/ecs-implementation-guide.md`
> (its render/`DescribeSystem` half still applies, but reads the hydrated graph
> below). **Prereq:** `docs/representation-ecs-design.md` (D1–D15).

---

## 0. The decisions this guide implements

Locked in conversation, amending the design doc (restated so they survive
compaction):

1. **Everything is an entity.** One node role for domain things and their
   components: every such node is an `ENTITY` vertex; a "component" is just an
   entity attached to another entity by an **owning** edge (`HAS_COMPONENT`).
2. **Values are relationships (three tiers).** A component does **not** store its
   value as a property. It points at a separate **value node** via an edge —
   `Entity → Component → Value`. This generalizes your existing character
   `CORPUS → HAS_ATTRIBUTE → ATTRIBUTE{value}` pattern to everything.
3. **Hybrid value nodes — interned enums, owned scalars.**
   - **Enum values are interned (shared):** each enum member exists once in the
     whole DB; every component with that value points at the same node. Mutation
     re-points the edge; the shared node is never edited and never cascade-deleted.
     Payoff: *"all hostile entities"* = the in-edges of the `HOSTILE` node.
   - **Numeric values are owned (per-component):** the existing `ATTRIBUTE{value:int}`
     node, cascade-deleted with its owner. (Interning integers is pointless.)
   - **Freeform text** (appearance prose, scene position) stays a **property on
     the component node** — no share or query benefit, so no value node. *(If you
     want strict uniformity, make it an owned text node instead; noted in §2.)*
4. **Hydration recurses owning edges; value edges are the boundary.** This is the
   first live instance of the owning-vs-reference rule we reserved: `HAS_COMPONENT`
   and `HAS_ATTRIBUTE` are **owning** (recurse + cascade); `HAS_VALUE` is a
   **reference** to a shared node (read the target, never recurse into or delete
   it). The owned tree is shallow → recurse fully, no depth cap.
5. **No legacy.** Solo project, no production data → **no migration**. Drop and
   re-seed the DB.

Carried over, not this slice: coarse **PUT/DROP** delta grain, **proposal →
resolver** LLM-write path, **serial turn-ordered** mutation.

---

## 1. Target model

A scene with a hostile Wolf (standard danger, mid-fight on its EXISTS clock) and
a wary Guard:

```
Wolf   ENTITY{kind: creature, name: "wolf"}
 ├HAS_COMPONENT→ ENTITY{ctype: stance}  ─HAS_VALUE──▶ VALUE{kind:stance,  member:hostile}  ◀┐ shared
 ├HAS_COMPONENT→ ENTITY{ctype: danger}  ─HAS_VALUE──▶ VALUE{kind:danger,  member:standard}  │
 ├HAS_COMPONENT→ ENTITY{ctype: appearance, text:"a lean grey wolf"}        (text = property) │
 └HAS_COMPONENT→ ENTITY{ctype: clock}                                                        │
                    ├HAS_VALUE──▶ VALUE{kind:pillar, member:exists}   (interned key)         │
                    └HAS_ATTRIBUTE→ ATTRIBUTE{value: 2}               (owned scalar: filled) │
                                                                                             │
Guard  ENTITY{kind: creature, name:"guard"}                                                 │
 ├HAS_COMPONENT→ ENTITY{ctype: stance}  ─HAS_VALUE──▶ VALUE{kind:stance, member:wary}        │
 └HAS_COMPONENT→ ENTITY{ctype: danger}  ─HAS_VALUE──▶ VALUE{kind:danger, member:standard} ───┘ (Wolf shares)
```

- **Three vertex families:** `ENTITY` (roots **and** components — the "everything
  is an entity" part), `VALUE` (interned, shared enum members), `ATTRIBUTE`
  (owned numeric values — existing type, reused).
- **Edges:** `HAS_COMPONENT` (new, owning), `HAS_VALUE` (new, reference→shared),
  `HAS_ATTRIBUTE` (existing, owning→scalar).
- **`VALUE` is unique on `(kind, member)`** — that uniqueness *is* the interning.
- **Scene entity vs component vs value:** a scene entity has a `CONTAINS` in-edge
  from a LOCATION; a component has a `HAS_COMPONENT` in-edge. (Both are
  `VertexType.ENTITY`, so never enumerate scene entities with
  `list_vertices(ENTITY)` — go through the location's `CONTAINS` edges.)

---

## 2. Value taxonomy — the rule for "where does this datum live?"

Three buckets; every field falls into exactly one:

| Bucket | Storage | Edge | Lifecycle | Mutation | Query |
|---|---|---|---|---|---|
| **Enum** (stance, danger, status, disposition, channel, pillar) | interned `VALUE{kind, member}` | `HAS_VALUE` | shared, never deleted | **re-point** the edge | reverse-traverse the value node |
| **Scalar** (clock filled, pillar capacity) | owned `ATTRIBUTE{value:int}` | `HAS_ATTRIBUTE` | cascades with owner | update `value` in place | n/a (per-entity) |
| **Text** (appearance, scene position, returns_when) | property on the component node | — | dies with the component | overwrite property | n/a |

A component may hold **several** interned enum values (distinguished by the value
node's `kind`) plus **at most one** owned scalar. Example: a `clock` has a
`pillar` enum (`HAS_VALUE → kind:pillar`) **and** a `filled` scalar
(`HAS_ATTRIBUTE`).

---

## 3. EntityData → component decomposition

| EntityData field | component (`ctype`) | value bucket |
|---|---|---|
| `name`, `kind` | **root** props | — |
| `description` | `appearance` | text (component prop) |
| `scene_position` | `position` | text (component prop) |
| `danger` | `danger` | enum `VALUE{kind:danger}` |
| `disposition` | `disposition` | enum `VALUE{kind:disposition}` |
| `stance` | `stance` | enum `VALUE{kind:stance}` |
| `status` | `status` | enum `VALUE{kind:status}` (state) + optional enum `VALUE{kind:pillar}` (broken_pillar) + text (returns_when) |
| `clocks[pillar]=n` | `clock` × N | enum `VALUE{kind:pillar}` + scalar `ATTRIBUTE{value:n}` |
| `pillar_profile[pillar]=c` | `pillar_cap` × N | enum `VALUE{kind:pillar}` + scalar `ATTRIBUTE{value:c}` |
| `threat_channels` | `threat_channel` × N | enum `VALUE{kind:channel}` |

> Live clock *capacity* is still computed (`pillar_capacity()` in
> `core/mechanic/effect.py`); only authored `pillar_cap` persists.

---

## 4. Step 1 — model layer

**`src/core/model/database.py`**
- `VertexType`: add `VALUE = "VALUE"`. (Keep `ENTITY`, `ATTRIBUTE`.)
- `EdgeType`: add `HAS_COMPONENT`, `HAS_VALUE`. (`HAS_ATTRIBUTE` exists.)

**`src/core/model/component.py`** (new, pure)
```python
from enum import StrEnum

class ComponentType(StrEnum):
    APPEARANCE = "appearance"; POSITION = "position"
    DANGER = "danger"; DISPOSITION = "disposition"
    STANCE = "stance"; STATUS = "status"
    CLOCK = "clock"; PILLAR_CAP = "pillar_cap"; THREAT_CHANNEL = "threat_channel"

class ValueKind(StrEnum):           # the `kind` discriminator on VALUE nodes
    STANCE = "stance"; DANGER = "danger"; STATUS = "status"
    DISPOSITION = "disposition"; CHANNEL = "channel"; PILLAR = "pillar"
```

**Hydration shape** (`EntityNode` — generic, in `core/model` or the repo):
```python
@dataclass
class EntityNode:
    id: str
    kind: str                       # root only
    name: str                       # root only
    components: list["Component"]

@dataclass
class Component:
    ctype: str
    enums: dict[str, str]           # value-kind -> member  (from HAS_VALUE)
    scalar: int | None              # from HAS_ATTRIBUTE
    text: str                       # component-node property
```

**Decision (unchanged):** keep `EntityData` as a hydrated **projection** for now;
the service rebuilds it from `EntityNode` (§7). Don't rewrite the ~8 consumers
this slice. Collapsing the DTO is a later slice (§11).

---

## 5. Step 2 — schema (`src/database/schema.py`)

- **`PROPERTY_TYPES`** — add `ctype` (STRING), `kind` (STRING), `member` (STRING),
  `text` (STRING). **Do not** reuse `value` for the enum member — `value` is
  already `INTEGER` (for `ATTRIBUTE`); the enum member is a separate `member`
  STRING property, which also lets `(kind, member)` be the interning key.
- **`VERTEX_SCHEMA`**:
  - `ENTITY`: `["name", "kind", "ctype", "text"]` — drop all old flat props
    (`danger`, `threat_channels`, `resolution`, `pillar_profile`, `disposition`,
    `scene_position`).
  - `VALUE`: `["kind", "member"]`.
  - `ATTRIBUTE`: `["value"]` (unchanged).
- **`EDGE_SCHEMA`** — add `HAS_COMPONENT: []`, `HAS_VALUE: []`.
- **`_indexes`** — add a **unique composite index on `VALUE (kind, member)`**.
  This enforces interning and powers the lookup-or-create.

No migration: delete the DB file, let `SchemaManager.ensure()` rebuild, re-seed.

---

## 6. Step 3 — entity repository (`src/database/repository/entity.py`)

The heart. Verbs model on `CharacterRepository.add_node`/`add_attribute`.

**Interning (the shared-enum primitive):**
```python
def intern_value(self, kind: ValueKind, member: str) -> Vertex:
    found = self._base.lookup_value(kind, member)     # via the (kind,member) index
    return found or self._base.create_vertex(VertexType.VALUE, kind=kind, member=member)
```
(Add `lookup_value` to `BaseRepository` using
`lookup_by_key(VALUE, keys=["kind","member"], values=[kind, member])`.)

**Compose:**
```python
def add_component(self, owner, ctype) -> Vertex:
    comp = self._base.create_vertex(VertexType.ENTITY, ctype=ctype)
    self._base.create_edge(EdgeType.HAS_COMPONENT, source=owner, target=comp)
    return comp

def set_enum(self, comp, kind, member):      # re-point: at most one edge per kind
    for e in comp.get_out_edges(EdgeType.HAS_VALUE):
        if e.get_in().get("kind") == kind: self._base.delete_edge(e)   # drop old
    self._base.create_edge(EdgeType.HAS_VALUE, comp, self.intern_value(kind, member))

def set_scalar(self, comp, n: int):          # owned ATTRIBUTE, update or create
    edges = comp.get_out_edges(EdgeType.HAS_ATTRIBUTE)
    if edges: self._base.update_vertex(edges[0].get_in(), value=n)
    else:
        attr = self._base.create_vertex(VertexType.ATTRIBUTE, value=n)
        self._base.create_edge(EdgeType.HAS_ATTRIBUTE, comp, attr)
```

**`create_entity(name, kind, spec)`** — create the root `ENTITY{name, kind}`,
then per component: `add_component`, `set_enum`/`set_scalar`, set `text`. (Delete
the dead flat signature with `wound_capacity`/`wound_filled`.)

**Hydrate** — `load(root) -> EntityNode`, walking **owning** edges only:
- `HAS_COMPONENT` → each component; on it, read `ctype`/`text`, collect
  `HAS_VALUE` targets into `enums[kind]=member`, read `HAS_ATTRIBUTE` → `scalar`.
- **Never recurse `HAS_VALUE`** (boundary to shared node). Tree is shallow; no
  visited-set needed yet.

**Cascade delete** — recurse `HAS_COMPONENT`; for each component delete its
owned `ATTRIBUTE` (via `HAS_ATTRIBUTE`) and the component vertex; **drop
`HAS_VALUE` edges but never the `VALUE` nodes** (shared). Never follow `CONTAINS`.

**Query-by-enum (the payoff):**
```python
def with_enum(self, kind, member) -> list[Vertex]:   # -> root entities
    v = self._base.lookup_value(kind, member)
    if v is None: return []
    comps = [e.get_out() for e in v.get_in_edges(EdgeType.HAS_VALUE)]
    return [c.get_in_edges(EdgeType.HAS_COMPONENT)[0].get_out() for c in comps]
```

---

## 7. Step 4 — location service (`src/service/location.py`)

- **`_to_entity_data(root)`** — build from `load(root)`: read the `danger`/`stance`
  components' `enums`, collect `clock` components into `clocks={pillar: filled}`,
  `pillar_cap` into `pillar_profile`, `threat_channel` into the set, `appearance`/
  `position` text, `status` into state/broken_pillar/returns_when.
- **`persist_entity_state(entities)`** — replace the JSON write with component
  upserts (the PUT seam): `set_scalar` each `clock`'s filled (creating the clock
  component if a new pillar was attacked), `set_enum` the `status`/`stance`. This
  is where coarse PUT/DROP lands later.
- **Delete** `_resolution_to_json`, `_resolution_from_json`, `_profile_from_json`.

---

## 8. Step 5 — spawn / worldgen (`src/service/world.py`)

Where entities are created (~`world.py:87`), compose via `create_entity(name,
kind, spec=[...])` instead of flat props. Authoring entry point for the model.

---

## 9. Tests

1. **Round-trip** — `create_entity` (danger, stance, two clocks) → `load` →
   `_to_entity_data` reproduces the `EntityData`.
2. **Interning** — two entities set to `stance=hostile` share **one** `VALUE`
   node (assert identity / one VALUE row).
3. **Re-point** — change an entity's stance; assert its `HAS_VALUE` now targets
   the new member, the old shared node still exists, and *other* entities on the
   old member are unaffected.
4. **Reverse query** — `with_enum(stance, hostile)` returns exactly the hostile
   roots.
5. **Cascade** — deleting a root removes its components + owned `ATTRIBUTE`s but
   **not** the shared `VALUE` nodes; `CONTAINS` location untouched.
6. **Keyed multi-instance** — two `clock` components, different `pillar`, both
   rehydrate into `clocks`.
7. **Enumeration trap** — `list_entities_at(location)` returns the 1 scene
   entity, not its components/values.

`uv run pytest` + `ruff check` green per commit.

---

## 10. Commit sequence

1. Model — `ComponentType`/`ValueKind`, `VALUE` type, `HAS_COMPONENT`/`HAS_VALUE`
   edges, `EntityNode`/`Component`.
2. Schema — vertex/edge schema, `(kind,member)` unique index; drop flat props.
3. Base repo — `lookup_value`.
4. Entity repo — `intern_value` / `add_component` / `set_enum` / `set_scalar` /
   `create_entity` / `load` / cascade / `with_enum`.
5. Location service — hydrate + persist via components; delete JSON helpers.
6. Worldgen — compose on spawn; drop & re-seed DB. *(cross-cutting)*

---

## 11. Deferred (named, not now)

- **Collapse `EntityData`** into a generic component accessor once consumers migrate.
- **Characters onto the same model** — retire `CORPUS → ATTRIBUTE` for the
  uniform `Entity → Component → Value` shape (the interned-enum design is new;
  scalars already match `ATTRIBUTE`).
- **PUT/DROP delta edges + `TURN` history (D12–D14)** — the §7 upsert is the seam.
- **`DescribeSystem` from components** — render reads `EntityNode` (other guide).
- **More reference edges** — `HAS_VALUE` is the first; curses/shared items add more,
  all governed by the same owning-vs-reference boundary (decision 4).
```
