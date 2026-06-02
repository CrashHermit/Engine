# Graph / State / Node Reorganization — Refactor Plan

> **Status:** Proposed plan for review. No code moved yet.
> **Goal:** Make the resolution pipeline comprehensible — kill the "rats nest"
> feeling — without changing behavior. Pure refactor: every step keeps the full
> test suite green and the graph's runtime behavior identical.
> **Approach:** Incremental. Each numbered step is one small commit with tests
> passing in between. We can stop after any step and still have a working,
> improved tree.

---

## 1. Diagnosis (what's actually wrong)

Two root causes, everything else is downstream:

1. **`GraphState` is a ~45-field flat blackboard** (`src/state.py`). All 22 nodes
   read/write one namespace across six unrelated concerns. The boundaries already
   exist *as comments* (`── Effect-on-target ──`, `── Threats ──`, `── Resist
   cycle ──`, …) — structure's job, done in comments. Durable state
   (`stress`, `scene_entities`) sits beside one-shot transient carriers
   (`classify_source`, `classify_entity`, `resist_response`) with no type-level
   distinction, so a field's lifetime is invisible.
2. **The file layout hides the pipeline's phases.** `node/` is 22 flat files;
   `signature/` is 12 more in a *parallel* flat dir, so each LLM node is split
   from its own signature. `resolution_graph.py` expresses the topology as ~20
   imperative `add_edge` calls with routers interleaved — the shape of a turn is
   the hardest thing to read.

Underneath both: the turn grew **three interleaved axes** (threats-back,
effect-on-target, aggro) threaded through one linear builder and one flat state.

## 2. The phase model (the missing mental model)

A turn is six phases. The node clustering and the state clustering already agree
1:1 — proof the decomposition is real:

| Phase | Nodes | State it owns |
|---|---|---|
| **intent** | alignment_router, question_generator, clarification, synthesizer | `intent_alignment_history`, `question`, `is_intent_alignment_achieved` |
| **frame** | engagement, roll_gate, segmenter, attribute_selector, mundane | `needs_roll`, `lead_up`, `contested_beat`, `deferred_tail`, `attribute`, `target_entity`, `target_pillar`, `push_for_effect`, `roll_result` |
| **threat** | classify_threat, gather_threats, dice_scale, ambush, ambush_scale | `pending_threats`, `threats`, `classify_source`, `classify_entity`, `is_ambush` |
| **effect** | apply_effect | `defeated_target`, `suspended_target`, `resolution_outcome`, `returned_targets`, `engagement_note` |
| **resolve** | held_planner, final_planner, narrator, turn_close | `narration_directive`, `anchors`, `prior_prose`, `held_scaffold`, `final_scaffold` |
| **resist** | resist_offer, resist_push_parser, resist_roll | `resist_queue`, `resist_cursor`, `resist_response`, `resist_action`, `resist_flavor` |

Cross-phase shared state (not owned by one phase): the read-only character sheet
(`character_*`, `*_rating`), location (`location_*`, `entities_at_location`),
the mutable `scene_entities`, the economy (`stress`, `trauma`, `trauma_gained`,
`character_lost`), and `message_history`.

## 3. Target layout

Co-locate each node with its signature (the I/O contract belongs next to the
node), and group by phase. `src/signature/` is dissolved into the node modules.

```
src/node/
  intent/    alignment_router.py  question_generator.py  clarification.py  synthesizer.py
  frame/     engagement.py  roll_gate.py  segmenter.py  attribute_selector.py  mundane.py
  threat/    classify.py  gather.py  dice_scale.py  ambush.py  ambush_scale.py
  effect/    apply_effect.py
  resolve/   held_planner.py  final_planner.py  narrator.py  turn_close.py
  resist/    offer.py  push_parser.py  roll.py

src/graph/
  main_graph.py
  intent_graph.py            (renamed from intent_alignment_graph.py)
  resolution_graph.py        (thin: composes phase blocks)
  routers.py                 (all conditional-edge functions, named + documented)
  logged_node.py
```

Each LLM node module holds both its `*Signature` and its `*Node` class. Pure-code
nodes (ambush, dice_scale, gather, …) are unchanged but relocated.

## 4. Hard constraints (things the refactor must respect)

- **Keep graph node *string ids* stable** (`add_node("classify_threat", …)`).
  Rename files and classes freely, but the LangGraph node ids double as
  checkpoint write targets and `LoggedNode` logger names; changing them risks
  breaking a mid-turn resumed resist interrupt and churns logs. Move code, keep ids.
- **LangGraph reducers are per top-level key.** `message_history`,
  `intent_alignment_history`, `pending_threats` use `Annotated[list, operator.add]`.
  Nesting these into sub-models would silently break the merge — so state grouping
  can only collapse *non-reducer* clusters (see Step 6).
- **One shared `GraphState` today.** Subgraphs (intent, resolution) compile against
  it. Per-subgraph state scoping (Step 6) is the only way to truly shrink it, and
  only works where a phase is a clean subgraph.
- **Pure refactor.** No behavior change in any step. The proof is the unchanged
  test suite, run after every commit.

## 5. The structural steps (low risk — mostly moves)

> Run after every step (the repo has no `testpaths`, so pass files explicitly):
> `uv run python -m pytest $(find test -name "*.py" -not -name "__init__.py") -q`

**Step 1 — phase-group the nodes.** Create `src/node/<phase>/` packages and move
each node file in. Update imports in `resolution_graph.py`,
`intent_alignment_graph.py`, and the ~5 test files. No class/id changes.
*Risk: trivial (imports). Green check: full suite.*

**Step 2 — co-locate signatures into their node modules.** Merge each
`signature/X.py` into the matching `node/<phase>/X.py` (signature class above the
node class). Update the ~12 node imports; delete `src/signature/`. Grep first for
any other importer (tests, future DSPy compile).
*Risk: low (imports + file merges). Green check: full suite + `grep -r src.signature`.*

**Step 3 — extract routers.** Move every conditional-edge function
(`_route_by_roll_gate`, `_fan_out_threats`, `_route_by_significance`,
`_route_after_narrator`, `_route_after_resolution`, `_fan_out_ambush`,
`_route_after_gather`) into `src/graph/routers.py`, named and documented as the
control-flow contract. `resolution_graph.py` imports them.
*Risk: trivial (moves). Green check: full suite + graph builds.*

**Step 4 — block the builder by phase.** Inside `ResolutionGraphBuilder.build`,
split the wall of `add_node`/`add_edge` into private `_add_frame()`,
`_add_threat()`, `_add_effect()`, `_add_resolve()`, `_add_resist()` methods, each
adding its own nodes + internal edges, with the *cross-phase* edges (the routers)
collected in one final `_wire_phases()` block. Same graph, readable construction.
*Risk: low (reorganized construction; ids unchanged). Green check: full suite +
compare compiled graph node/edge sets before/after.*

After Step 4 the tree and the topology are legible; the remaining steps are the
deeper, more careful state work.

## 6. The state steps (careful — do last, conservatively)

State can only be decomposed where it doesn't fight LangGraph's channel model.
Bucket the 45 fields by what's *safe* to collapse:

- **Reducer channels — leave top-level, untouched:** `message_history`,
  `intent_alignment_history`, `pending_threats`.
- **Read-only, set-once-by-coordinator — safe to group into one value object:**
  the character sheet (`character_name`, `character_description`,
  `corpus_rating`, `mens_rating`, `anima_rating`) → a frozen `CharacterSheet`
  under a single `sheet` key; location (`location_name`, `location_description`,
  `entities_at_location`) → a `SceneInfo` under one `scene_info` key. These are
  never mutated inside the graph, so no reducer concern.
- **Mutable but cohesive — optional group, replaced wholesale:** economy
  (`stress`, `trauma`, `trauma_gained`, `character_lost`). Could become an
  `Economy` object that nodes read and return whole; mild ergonomic cost.
- **Transient per-iteration carriers — keep flat but mark explicitly:**
  `classify_source`, `classify_entity`, `resist_response`, `resist_action`,
  `resist_flavor`, `question`. Group under a clearly-named `# transient` section
  (they don't survive a phase).

**Step 5 — group the read-only clusters** (`sheet`, `scene_info`). Touch only the
coordinator (which builds them) and the handful of nodes that read them
(narrator, attribute_selector, dice_scale). Smallest real state shrink, near-zero
risk. *Green check: full suite.*

**Step 6 — scope state to subgraphs where boundaries are clean.** `intent` is
already a subgraph and only touches intent fields — give it an `IntentState`
input/output schema so the god-object stops leaking into it. `frame` and
`threat-enumeration` are candidates next. **Explicitly out of scope:** forcing
`resolve`+`resist` into subgraphs — they're entangled by the significance gate
(threat→resolve) and the resist cycle's `interrupt()` loop; flattening that into
clean subgraph I/O is high-risk for little gain. Leave them as well-organized
sections in the resolution builder (Step 4 already makes them readable).
*Green check: full suite + a live resist-interrupt smoke test.*

## 7. Sequencing & stopping points

```
Step 1  nodes → phase packages          (legible tree)        ← high value, trivial
Step 2  signatures co-located           (contract by node)    ← high value, low risk
Step 3  routers extracted               (control flow named)
Step 4  builder blocked by phase        (topology readable)   ← topology now clear
─────────────────────────────────────── good stopping point ───
Step 5  read-only state grouped         (first state shrink)
Step 6  intent/frame subgraph state     (god-object shrinks)  ← deepest, most care
```

Steps 1–4 deliver ~80% of the comprehensibility for ~20% of the risk and are all
mechanical. 5–6 are the genuine architecture improvement and are gated behind the
now-visible seams. We can stop after Step 4 and reassess.

## 8. Risks & mitigations

- **Hidden importers** (DSPy compile, scripts) → grep `src.node` / `src.signature`
  before each move; the survey shows only graphs + tests today.
- **Checkpoint/resume breakage** → keep node *id strings* stable (§4); a mid-turn
  resist interrupt spanning the refactor is the only fragile case (dev-only).
- **Silent graph-shape change in Step 4** → assert the compiled graph's node and
  edge sets are identical before/after (one-off script), beyond the test suite.
- **State reducer breakage in Step 6** → only group non-reducer fields; never nest
  `*_history` / `pending_threats`.

## 9. Out of scope (not this refactor)

- Renaming the misleadingly-named `apply_effect` (it now does de-threat + push) —
  cosmetic; fold into Step 1 only if free.
- `coordinator.py` (250 lines) decomposition — it's the integration boundary, a
  separate concern from the graph rats-nest; its own later pass.
- Any behavior, balance, or prompt change.
