# Turn Resolution & Concurrency Model

> **Status:** Settled. Records a design decision and the reasoning behind it,
> so the concurrency machinery we rejected does not get rebuilt later.
> **Scope:** How mutations to game state are ordered and applied across a turn.

## The decision

**The engine is serial and turn-ordered. There is one writer at a time, and
mutations apply one at a time in a defined order.** We do not use — and should
not add — concurrency-control machinery (commutative-merge requirements as a
*correctness* tool, CRDTs, compare-and-swap loops, or accumulate-then-resolve
phases introduced for throughput).

## Why

Performance is not a constraint here. The LLM calls dominate wall-clock time by
orders of magnitude; the state operations between them are free by comparison.
Every concurrency-control technique exists to answer one question — *how do two
writers safely touch the same data at the same time* — and in a turn-ordered
engine that situation does not arise. There is no second writer to race.

With a single serial writer, the things we spent effort worrying about dissolve:

- **Conditionals just work.** A read-decide-write (e.g. "if stress ≥ threshold
  and not already broken → flip to breakdown") always reads current truth,
  because nothing else is writing concurrently. The classic double-fire cannot
  happen.
- **No merge semantics.** Mutations apply top-to-bottom; no field needs a
  reducer for *correctness*. Within a single action, effects run in authored
  code order, each seeing what the previous left.
- **Derived state is recomputed, never raced.** `Status` and the other derived
  views (`action_intent`, `landed_threats`, `current_threat`) are computed on
  read. There is nothing to keep in sync.

### Simultaneity vs. concurrency

The one thing that survives is *fictional simultaneity*: when the game says two
things happen "at once" (two actors act this tick). This is a **game-design**
ordering question, not a systems one, and turn order already answers it — it is
a total, deterministic order. Pick the order, loop, apply one at a time. We do
**not** need accumulate-then-resolve for fairness today; if a specific beat ever
needs ties to land before any resolution (e.g. two simultaneous hits that should
both register before a death check), that is a deliberate, local design choice —
not the default architecture.

## How this maps to the current graph

The resolution graph (`src/graph/resolution_graph.py`) *does* run nodes in
parallel via LangGraph `Send` fan-out — but only over genuinely independent
work, which is consistent with the serial model: parallel branches never touch
the same mutable state, so their relative order is irrelevant.

Two fan-outs run off the segmenter in one superstep
(`fan_out_frame_and_threats`):

1. **Framing classifiers** (`approach`, `pillar`, `push`, `target`, `duration`)
   write **five disjoint fields** — `attribute`, `target_pillar`,
   `push_for_effect`, `target_entity`, `beat_span`. No two write the same key.
2. **Threat classifiers** (one `classify_threat` per source) write **only**
   `pending_threats`, the single channel with a reducer
   (`Annotated[list[Threat], operator.add]` — commutative append).

The two arms are independent: `classify_threat` reads only shared read-only
inputs plus its own `Send` payload, never a field the framing arm writes.
Everything order-sensitive — the roll (`dice_scale`), `apply_effect`, the resist
cycle — runs **after** the `gather_threats` join, fully serialized.

So `operator.add` on `pending_threats` (and the message histories) is the *only*
commutative reducer, and it is used for parallel **append**, not as a
general-purpose concurrent-mutation strategy.

## Mutation inventory

Every state write, classified. Verified against the node code; current as of
this commit. The point of the table is that the **parallel** rows are *only*
disjoint-set or commutative-add, and every order-sensitive read-modify-write is
**serial**.

### Parallel writes (segmenter superstep) — safe by construction

| Field(s) | Writer(s) | Kind |
|---|---|---|
| `attribute`, `target_pillar`, `push_for_effect`, `target_entity`, `beat_span` | framing fan-out (`approach`/`pillar`/`push`/`target`/`duration`) | disjoint blind-set — each a distinct key |
| `pending_threats` | `classify_threat` ×N | commutative append (`operator.add` reducer) |

### Serial read-modify-write — order matters, so it is sequenced (never fanned out)

| Field(s) | Writer(s) | Why it is an RMW |
|---|---|---|
| `stress`, `trauma` | `apply_effect`, `resist_roll` | `add_stress(state.stress, …)` reads then accumulates |
| `scene_entities` | `engagement`, `apply_effect` | clock fill + status/posture rewrite over the current list |
| `threats` | `gather` → `dice_scale` → `resist_roll` | whole-list rewrite, each reads the prior |
| `resist_cursor` | `held_planner` (init 0), `resist_roll` (+1) | increment |
| `trauma_gained`, `character_lost` | `apply_effect`, `resist_roll` | OR-accumulated — monotonic *and* commutative (defensive; serial anyway) |

All other fields are serial single-writer blind-sets (`contested_beat`,
`needs_roll`, `roll_result`, `resolution_outcome`, the planner scaffolds, the
resist transients, the narration fields, etc.). `message_history` and
`intent_alignment_history` carry `operator.add` reducers but are written by one
node per run — the reducer is for append semantics, not concurrency.

### Two RMW hotspots to never parallelize

1. **The clock-fill clamp** — `apply_effect.py`,
   `filled = min(capacity, target.clocks.get(pillar, 0) + segments)`. This is a
   *saturating add*: near the cap the result depends on order, so it is **not**
   commutative. It is correct today only because it is serial (one writer,
   reading current truth). If effect application ever fans out (e.g. several
   simultaneous attackers filling one clock), this clamp must become
   accumulate-raw-then-clamp-once, not per-writer `min`.
2. **Stress accumulation** — `add_stress` is the same shape. Multiple concurrent
   stress sources would need commutative accumulation; today they are serial.

These two are the concrete instances of the general rule below.

## Invariants to preserve

1. **Order-sensitive logic lives after a join, never inside a fan-out.** If a
   step reads state another step writes, the two must be sequenced by an edge,
   not run concurrently.
2. **Concurrent branches stay independent.** Each parallel branch may read only
   shared read-only inputs and its own `Send` payload, and may write only a
   field no other concurrent branch writes (or a commutative-`add` channel).
   This is a convention, not a guardrail — disjoint-key writes never raise, so
   LangGraph will not catch a violation. The contract is pinned on
   `fan_out_frame_and_threats` in `src/graph/routers.py`.
3. **Superstep alignment around the roll is load-bearing.** The framing and
   threat arms rejoin at `gather_threats` in the same superstep so the roll
   fires exactly once; changing either arm's hop count can silently re-break it
   (see the note at `resolution_graph.py`).
