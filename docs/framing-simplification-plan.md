# Framing Simplification Plan

> **Status:** Proposed, for review. Incremental — each step is one green commit.
> **Goal:** Parallelize the framing phase and tighten its data model, *without*
> losing functionality or weakening the discrete/trainable small-model design.

## What & why

The framing phase is a serial chain (`roll_gate → segmenter → attribute_selector`)
and `attribute_selector` is a single node emitting **four** outputs
(`attribute`, `target`, `pillar`, `push`) — against the one-judgment-per-node
principle. We:

1. Replace the three rating ints with a **`ratings: dict[Channel,int]`** map,
   killing the duplicated `match attribute` pool-lookup in `dice_scale` and
   `apply_effect`.
2. Introduce **`ActionIntent`** — a frozen value object (`attribute`, `target`,
   `pillar`, `push`) exposed as a `GraphState.action_intent` derived view, so
   consumers read one cohesive object.
3. **Split** the action-read into discrete parallel classifiers — `approach`
   (attribute), `pillar`, `push` — and **derive `target` in code** (0–1 entities
   → deterministic, no call; 2+ → a `target` classifier). All run in parallel
   with each other *and* with the `classify_threat` fan-out, joining at the roll.

This keeps every LLM call narrow (better metrics, cheaper per-module routing per
decision #18), removes a serial hop, and saves the target call in the common
single-foe case. Net: tinier/parallel/routable calls, lower latency, data model
tightened.

## Data model

```
# core/model/action.py
@dataclass(frozen=True)
class ActionIntent:
    attribute: Channel | None
    target: str
    pillar: ThreatPillar | None
    push: bool

# GraphState
ratings: dict[Channel, int]              # replaces corpus/mens/anima_rating
# flat fields attribute/target_entity/target_pillar/push_for_effect stay
# (written by the split nodes); add:
@property
def action_intent(self) -> ActionIntent: ...     # view over the flat fields
def pool_for_attribute(self) -> int:              # ratings[attribute], 0 default
```

`ActionIntent` is a *read view* (the split nodes can't share one stored object);
the field-count win comes from `ratings` (−2). `CharacterSheet`/`SceneInfo`
clustering is deferred to the later state pass.

## Nodes (frame/)

- `approach.py` — `ApproachNode` + signature → `attribute` (Channel). Always.
- `pillar.py` — `PillarNode` + signature → `target_pillar`. Always. (Pillar is
  read from the verb — "scare it" → WILLING — so it needs no resolved target.)
- `push.py` — `PushNode` + signature → `push_for_effect` (bool). Always, tiny.
- `target.py` — `TargetNode`: code-derive (`0 entities → ""`, `1 → that name`),
  LLM classifier only when `≥2` entities. Writes `target_entity`.
- delete `attribute_selector.py`.

## Wiring

```
roll_gate ─(roll)─► segmenter ─┬─ approach ─┐
                               ├─ pillar    ─┤
                               ├─ push      ─┤
                               ├─ target    ─┼─► dice_scale → apply_effect
                               └─ classify_threat ×N → gather ─┘
```
`dice_scale` waits for all framing nodes + `gather`. Caution: confirm a source
(`segmenter`) may carry both static edges (to the framing nodes) and the
conditional `Send` fan-out (to `classify_threat`); if LangGraph balks, emit the
framing nodes as Sends from the fan-out function too. Verify with a graph
topology test before/after.

## Incremental steps (each green commit)

1. **`ratings` map** — replace the 3 ints; coordinator builds it; `dice_scale` +
   `apply_effect` use `state.pool_for_attribute()`. Isolated, no graph change.
2. **`ActionIntent` view** — add the dataclass + property; consumers read it.
   No behavior/graph change (`attribute_selector` still one node).
3. **Split + parallelize** — add `approach`/`pillar`/`push`/`target`, delete
   `attribute_selector`, rewire `segmenter` to fan out to them ∥ the threat
   fan-out, join at `dice_scale`. Topology test + full suite.

## Cautions

- **Target derivation must not lose function:** `apply_effect` only acts on
  CREATURE targets, so a mis-derived object/none target safely no-ops; the only
  risk is a contested beat with one creature *not* aimed at it (rare) — accepted.
- **No judgment merging** — splits only; each node stays single-purpose.
- **Call count rises** for the action read (1 → 3) but each is tiny, parallel,
  and individually routable; target-derive claws one back in the common case.
