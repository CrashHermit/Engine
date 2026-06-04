# Representation, ECS & Episodic Memory — Architecture Design

> **Status:** Living design doc. Decisions in §3 are locked (this doc's own `D#`
> namespace, distinct from the BitD doc's `#`). **Rollout is "document now,
> migrate opportunistically"** (D15): new work follows these conventions; existing
> code migrates to ECS as each area is touched, so two paradigms coexist for a while.
> **Scope:** how the engine *represents* things and gives them to the LLM — a pure,
> graph-native **ECS substrate**, a derived **Description** system over it, the
> **two-writer mutation** model, and the **Turn**-based **episodic memory**.

---

## 1. Why

Every domain thing (`EntityData`, `CharacterData`, `LocationData`, `WorldData`)
carries a single free-text `description` blob — stored as a DB property, generated
by worldgen, and string-formatted ad-hoc into ~6 signatures plus the narrator
(`f"{e.name}: {e.description}. Location: {e.scene_position}"`, a format even
documented *inside* `roll_gate`/`segmenter` InputFields). The blob is an
inconsistent veneer over genuine structure that already exists beside it (danger,
channels, disposition, stance, status, clocks).

We want the opposite: **structured truth is canonical; the prose handed to the LLM
is derived from it.** And we want that structure to be **composable** — a
mutation-heavy game ("anything can have anything happen to it": curses, wounds,
transforms, substances) is exactly where entity-component composition pays off.

## 2. Facts that shape the design

- **The codebase already does component-as-vertex.** Character attributes
  (`CORPUS`, `MENS`, `STRESS`, `TRAUMA`, the Big-Five traits) are each their **own
  vertex** with a `value`, linked by a `HAS_*` edge (the `ATTRIBUTE.value` pattern
  in `schema.py` / `CharacterRepository`). Pure ECS *generalizes this existing,
  committed pattern* to all entities — it is not a novel bet.
- **The episodic linked list already exists.** `MESSAGE` vertices chain via
  `NEXT_MESSAGE` (head `HAS_MESSAGE`, tail `LAST_MESSAGE`), and a `LOCATED_AT`
  edge type is already defined — but the chain is anchored to the `USER`.
- **Layer rules (code-style §2) are binding.** `core/model` is pure and may not
  import `core/mechanic`; graph nodes may not touch services/repositories; effects
  apply post-`ainvoke` in the coordinator. "Systems" must therefore be
  *distributed*, not one omnipotent layer (D11).
- Performance is **not** a motivation — few entities per scene, LLM-paced. ECS is
  adopted for **composition/uniformity/extensibility**, so we keep the **graph**
  store and do **not** import ECS's columnar/archetype storage.

## 3. Locked decisions

| # | Decision | Rationale |
|---|----------|-----------|
| **D1** | **Hybrid truth, prose derived.** Structured facets are canonical for anything load-bearing or mutable; authored free text only for inert flavor; LLM-facing prose is always *rendered*, never stored as the source. | Kills drift on everything that matters while keeping authoring expressive. |
| **D2** | **Shared `Facet` = kind + text**, kind from a small, shared, **extensible** `FacetKind` enum. (Visibility deferred — D9.) | One Description object across all types; consistent labelled vocabulary for the LLM; fits the heavy-StrEnum house style. |
| **D3** | **FacetKind starter set:** `IDENTITY, APPEARANCE, MANNER, STATE, CAPABILITY, SETTING`. Each type emits its applicable subset; grows (`FORM`/`SENSATION`…) with the body system. | Captures the distinctions consumers care about (threat classifier ← STATE/CAPABILITY; narrator ← APPEARANCE/MANNER/SETTING). |
| **D4** | **`Description` is an ephemeral render view** — built on demand, never persisted. | Truth lives in components; prose is a projection, so it can't go stale or drift. |
| **D5** | **Pure ECS, graph-native.** An entity is an **id + a set of components**; components are **pure data** attachable to any entity; **every component is its own vertex** linked by an edge (generalizing the `ATTRIBUTE` pattern). | Uniform composition; "all entities with component X" is a traversal; consistent with existing character-attribute storage. |
| **D6** | **Behavior lives in systems, not on data.** `describe()` is a **`DescribeSystem`** that dispatches by **per-component-type handlers** (register a handler per component type; never edit a god-method). *Supersedes the interim "components self-describe" once ECS lands.* | ECS-idiomatic; recovers self-describe extensibility (register, don't edit) without putting behavior on components. |
| **D7** | **Render on-demand from structured state.** `GraphState` carries the structured entities/DTOs (components); rendered prose is a **computed property** (`state.entities_prose`) re-rendered on access. | Always fresh through mid-turn mutation; removes the ad-hoc format string and its documented coupling. |
| **D8** | **Render format: labelled lines, fixed kind order.** IDENTITY/name leads; one line per kind (APPEARANCE, MANNER, STATE, CAPABILITY, SETTING); same-kind facets joined. One format for all consumers. | Consistent and parseable (classifier can weight STATE/CAPABILITY) yet readable for the narrator; matches the existing `Name: …` convention. |
| **D9** | **Visibility deferred.** `Facet` stays kind + text; no player-vs-known distinction yet. | Discovery/secrecy is a separate subsystem with no concrete mechanic yet; don't tax every facet/render now. |
| **D10** | **Two writers, both structured.** The deterministic sim mutates derived state (parts/conditions/clocks/substances); the LLM emits **structured** updates (component writes), never prose-as-truth. | Both the simulation and emergent fiction become clean structured deltas; nothing drifts. |
| **D11** | **Systems are distributed across layers, not one layer.** Pure systems (describe, scaling, tick math) in `core/mechanic`; effectful systems (graph reads/writes) in coordinator/services; graph nodes orchestrate. Adopted for composition, **not** performance — keep the graph store. | Respects code-style §2; avoids cargo-culting data-oriented storage we don't need. |
| **D12** | **Episodic unit = `TURN` vertex.** One per resolved cycle: player input + **optional** prose + **game tick** + **real timestamp**. | A turn — not a message or beat — is the natural memory grain; narration-less turns still get a node. |
| **D13** | **History topology:** global **`NEXT_TURN`** chain (whole story) + **`LOCATED_AT`** (per-location recall) + **`CHANGED`** delta-edges to each mutated subject, each edge carrying **delta + game tick + real time**. | Reuses the existing chain + `LOCATED_AT`; one coherent timeline plus cheap location-scoped views; graph-native deltas. |
| **D14** | **Truth vs. record.** Current state is **never** stored as a Description; history is the Turn chain + delta-edges. Prose carries the human-readable change ("deltas prose'd in"); the structured change mutates truth in place. | Current truth is always re-derivable; episodic memory is the prose + graph-linked deltas. |
| **D15** | **Rollout: document now, migrate opportunistically.** This doc is the contract; features continue in the current style and migrate to ECS as each area is touched. | Lowest immediate disruption; the substrate conventions here keep opportunistic migrations consistent. |

## 4. The ECS substrate (D5, D6, D11)

- **Entity** = a vertex with an id (and at most trivial intrinsic tags). No rich data.
- **Component** = a pure-data vertex (`Danger`, `Stance`, `Status`, `Appearance`,
  `Manner`, `Condition`, `Part`, `Substance`, `Clock`, `LocatedAt`, …) linked to its
  entity by a `HAS_*`/`IS_*` edge. Each entity owns its own component instances
  (mirrors per-character `CORPUS`/`STRESS` vertices). The existing `IS_SOURCE` /
  `IS_MANIPULATOR` function-edges are already components.
- **System** = behavior, as a pass over entities carrying the relevant components.
  *Distributed* per D11: pure systems in `core/mechanic`, effectful systems in
  coordinator/services, orchestrated by graph nodes.
- **Hydration:** a single "load entity with all its components" loader keeps the
  read fan-out (vertex + N edge traversals) in one place — the entity analogue of
  today's character-attribute loading.

## 5. The Description system (D1–D4, D6–D8)

- `Description`, `Facet`, `FacetKind`, and the renderer live in `core/model` (pure).
- A `Facet` is `(kind: FacetKind, text: str)`.
- `DescribeSystem` builds a `Description` for an entity by aggregating per-component
  handlers: each component type has a registered handler producing zero or more
  facets (authored components → APPEARANCE/MANNER/IDENTITY; scalar components →
  STATE/CAPABILITY via small lookup tables; rich components → their own facets).
- `Description.render()` emits **labelled lines in fixed kind order** (D8).
- Consumers read computed props on `GraphState` (`entities_prose`, `character_prose`,
  …) that call the describe→render pipeline on access (D7), so output reflects
  mid-turn mutation.

## 6. Mutation & history (D10, D12–D14)

- A change is always a **structured** component mutation (sim or LLM).
- Each resolved cycle produces a `TURN` vertex (input + optional prose + game-tick +
  real-time), appended to the global `NEXT_TURN` chain and `LOCATED_AT` its location.
- The turn emits a `CHANGED` edge to every component/entity it mutated; the edge
  carries the structured **delta** + both timestamps.
- **Current truth** = the live component graph (rendered ephemerally). **Episodic
  memory** = the Turn chain (prose) + `CHANGED` deltas. No Description is ever stored.

## 7. Open / bookmarked

- **Delta payload schema** (what rides a `CHANGED` edge) — blocked on the
  part/mutation verb system; spec when that lands.
- **Room navigation** — keep or drop (gameplay call); determines how many
  narration-less turns exist, but blocks nothing here.
- **Facet visibility / discovery model** — deferred (D9); revisit when a concrete
  secrecy/discovery mechanic exists.
- **First opportunistic targets** when migration begins: the `DescribeSystem` +
  `Facet`/`FacetKind` value types are pure and shippable alone; `EntityData` is the
  natural first entity to re-platform (it already has the most structure and feeds
  both the threat classifier and the narrator).
