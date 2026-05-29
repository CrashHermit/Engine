# Blades in the Dark — Resolution Integration Design

> **Status:** Living design doc. The decisions in §3 are locked; §6 is the open agenda.
> **Branch:** `claude/bitd-integration-design-ujx7Z`
> **Scope:** Replacing the current "decompose intent into an action list" step with a
> proper Blades-in-the-Dark (BitD) action-resolution loop, decomposed into small
> DSPy modules suited to smaller models.

---

## 1. Why

The engine today turns a player's stated intent into an **ordered list of discrete
actions** (`action_generator`) and hands that list to the narrator, which depicts all
of them. Nothing gates whether a roll is needed, nothing scopes how much one message
can accomplish, and there are no dice, positions, effects, consequences, or stress. A
player can type "I cross the courtyard, kill all twelve guards, and steal the crown" and
the narrator will simply narrate it.

This design replaces that pass-through with a faithful BitD resolution loop, while
keeping every LLM step **narrow enough for a small model** to do reliably.

---

## 2. Current architecture (as built)

Linear main graph (`src/graph/main_graph.py`):

```
START → intent_alignment → action_generator → narrator → END
```

- **`intent_alignment`** (subgraph, `src/graph/intent_alignment_graph.py`):
  loops with the player until intent is clear. Its router
  (`src/signatures/intent_alignment_router.py`) already returns `false` when intent is
  *ambiguous, physically impossible for the character, contradicts context, or references
  an entity not present*. This is **layer 1 of over-reach defense** and is reused as-is.
- **`action_generator`** (`src/nodes/action_generator.py`): decomposes intent into
  `action_list: list[str]`. **This is the node we replace.**
- **`narrator`** (`src/nodes/narrator.py`): writes prose from the action list. Already
  framed "in the spirit of Blades in the Dark", but has **no notion of effect-bounded
  reach, position, or consequence** — this is the anti-chaining gap.

Relevant existing facts that shape the design:

- `CharacterData` (`src/core/model/character.py`) **already has `corpus`, `mens`,
  `anima`** integer fields (plus Big Five personality traits). The three resolution
  attributes already exist in the data model.
- `GraphState` (`src/state.py`) uses the `Annotated[list[...], operator.add]` reducer
  pattern for accumulating fields — relevant for parallel fan-out (concurrent nodes must
  write distinct keys or use a reducer).
- Convention: each LLM step is a **DSPy `Signature`** (`src/signatures/`) wrapped by a
  thin **Node** (`src/nodes/`). New modules follow this 1 signature + 1 node pattern.

---

## 3. Locked decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Three attributes — Corpus / Mens / Anima** replace BitD's 12 action ratings; an LLM `attribute-selector` maps a freeform action onto one of the three. | Already present in `CharacterData`. Freeform actions need a small, broad taxonomy, not a fixed 12. |
| 2 | **One gated roll per turn.** A `roll gate` decides if the intent involves both **danger and uncertainty**; only then do we roll. Mundane intent skips straight to narration. | Faithful to BitD ("if there's no risk and no doubt, just say yes"). Keeps non-dramatic turns frictionless. |
| 3 | `action_generator` is replaced by a **decomposed Intent Interpreter pipeline** (not one signature). | Small models can't reliably emit {needs-roll?, attribute, position, effect, stakes} in one shot. |
| 4 | **Over-reach → scope-to-first-contested-beat.** The interpreter rolls only the *first* action carrying danger+uncertainty; mundane lead-up is narrated, everything past the beat is deferred to later turns. | The narrowest, most small-model-friendly mechanism (single extraction), and the most BitD-faithful (GM scopes the roll to the immediate contested beat). |
| 5 | **Fully decomposed + parallelised.** Each judgment is its own tiny module; independent ones fan out concurrently via **parallel edges** (framing) and **`Send`** (dynamic consequence fan-out). | Smaller, more reliable LLM calls; latency clawed back by concurrency. `Send` is reserved for *variable-length* lists (stacked consequences), not the fixed framing fan-out. |
| 6 | **Resistance = weighty reactive follow-up turn.** The consequence lands in the fiction first; the turn ends offering resistance; the player's **typed** reply drives a resistance-resolution path on the next invocation (mirrors the existing `intent_alignment` re-invoke loop). | Most tabletop-faithful feel; cheapest to build (no checkpointer); keeps every turn atomic. Typed (not buttons) so the player can **flavor how they resist** ("I twist so it catches my pauldron") — that flavor feeds narration. |
| 7 | **Native BitD dice.** Ratings **0–4**; pool = the attribute's rating (0 = roll **2d6 take the worst**). Take highest die: **6 = success**, **4–5 = success-with-consequence**, **1–3 = bad outcome**, **two+ 6s = critical**. Bonus dice come only from **push-yourself (+1d, +2 stress)**, **assist (+1d)**, **devil's bargain (+1d)**. Position/effect **never** change the pool. | Proven curve; maps cleanly onto the three attributes. Keeps a clean separation: pool = capability, position/effect = consequence severity & narration reach. |
| 8 | **Lean ~4-dot starting budget** (e.g. `{2,1,1}` or `{2,2,0}`), ratings grow toward the 4 cap via advancement. | Three broad attributes inflate pools vs BitD's 12 thin actions; a lean budget keeps typical pools at **1–2 dice**, preserving the gritty, swingy "competence is earned" tone. Consequence: 4–5 and 1–3 are the *common* results, so the consequence/resistance pipeline is the engine's **hot path**. |
| 9 | **Anti-chaining is enforced by input-starvation, not by the narrator.** The narrator is *not* trusted to "stop at the edge of effect". Instead the **scoper segments the message into `{lead_up, contested_beat, deferred_tail}`**, and the narrator only ever receives `lead_up + contested_beat + outcome + effect + consequence` — never the tail or the raw full chain. It cannot run ahead because the rest isn't in its context. The gate (decision #2) and scoper merge into one judgment: *"find the first beat needing a roll; if none, it's all lead-up → no roll."* | Asking a generative model to self-limit mid-prose is a soft constraint that fails exactly when needed (worse on small models). Robustness comes from controlling the narrator's **input**, guaranteed by the graph. |
| 10 | **Deferred tail is held as a passive *suggestion*, never an execution queue.** It is stored (`pending_intent`) and surfaced next turn via a **dedicated hint widget** (a dim line above the input that persists while typing, with a styled `continue:` prefix; empty-enter accepts it, typing overrides it). Re-affirming the tail sends it back through the **whole pipeline** as a fresh message, so it is **re-scoped against the updated fiction**; it is never auto-rolled from storage. | After a consequence the fiction has changed, so a stale queued action shouldn't auto-execute — the player should re-decide. Reusing the full pipeline means no special resume code, no stale actions, and natural recursion (a multi-beat plan peels one contested beat per turn). |
| 11 | **Stress is the survival currency; resistance always works, dice only set the price.** Resisting a consequence *always* reduces/avoids it — there is **no fail branch**. Cost = `6 − highest die` of a roll of the consequence's channel attribute; a crit (2+ sixes) **clears 1 stress** instead. Push-yourself costs **2 stress**. Default track **9 stress / 4 trauma** (tunable). | Faithful to BitD and keeps the resistance flow a single clean line (roll → pay → mitigate → maybe overflow). With lean 1–2 dice pools, players reach for resistance constantly — stress is the hot resource. |
| 12 | **Relief is vice-only, continuous and fiction-gated** (rest was considered and cut). Indulging in the fiction (right place/moment) routes to a vice-resolution: **roll your lowest attribute, clear that many stress**; if the roll **exceeds current stress you overindulge** → a complication. No formal downtime phase. | Canonical BitD relief. The overindulgence rule *is* the anti-spam gate (safe when strung-out, risky when nearly fresh), so vice-only + permadeath stays balanced without cooldown state. Continuous/fiction-gated fits the engine (no mission/downtime structure exists). Designed to be downtime-slottable later. |
| 13 | **Permadeath at max trauma.** Stress overflow → reset to 0, gain **1 trauma + a trauma condition**; at **4 trauma the character is lost** (retired/dead/broken) and a new one begins. | Failure has real teeth; stories get endings. The lean, resistance-heavy economy means trauma genuinely accrues. |
| 14 | **Vices are freeform descriptors that accumulate, trauma-linked.** Characters start with one freeform vice; **each trauma grants a new one** — a coping mechanism born from the wound, building a *scar-record*. More vices broadens *access* (more fictions qualify as relief), **not power** (clear is still roll-lowest + overindulgence gate). | Marries relief and permadeath into one grim bargain — every step toward being lost hands you a new way to cope. Freeform matches the engine's LLM-driven, broad-category ethos. |
| 15 | **Consequence = severity (code) + type & fiction (LLM).** A code table maps **position × tier → a severity rung** on the ladder `None → Minor → Standard → Severe → Fatal`. The consequence-selector LLM then picks the **type** (harm / complication / worse-position / lost-opportunity / reduced-effect), writes the fiction at that rung, and tags the **channel** (corpus/mens/anima). **Resistance steps severity down one rung.** | Keeps the balance-critical magnitude in code (safe on small models), leaves flavor to the LLM. Unifies BitD's harm levels and all consequence types under one magnitude axis, and answers "how much does a resist mitigate" = one rung. |
| 16 | **Severity is position-only; the tier decides success, not severity.** `controlled→Minor, risky→Standard, desperate→Severe`. A **6** = success, no consequence; **4–5** = success **+** position-severity consequence; **1–3** = fail **+** the *same* position-severity consequence; **crit** = success + benefit. **Fatal is not a normal cell** — reserved for explicitly lethal fiction (selector may escalate Desperate→Fatal). | With lean pools, 1–3 is common; a tier-bump would route most failures to Severe → runaway lethality. Position-only pins danger to how exposed the player chose to be (the dial the system actually set), which stays gritty without a death spiral. |

### Consequence-severity table (decisions #15–16)

| roll ↓ / position → | Controlled | Risky | Desperate |
|---|---|---|---|
| **6** | success, no consequence | success, no consequence | success, no consequence |
| **4–5** | success **+ Minor** | success **+ Standard** | success **+ Severe** |
| **1–3** | fail **+ Minor** | fail **+ Standard** | fail **+ Severe** |
| **crit (2+ 6s)** | success **+ benefit** | success **+ benefit** | success **+ benefit** |

Code reads the cell → severity rung; LLM fills type + fiction + channel. Resist = −1 rung;
`None` = no consequence. (`benefit` content = open node "crit & success benefits".)

### Over-reach defense, in layers
1. **Intent alignment** (exists) rejects impossible / nonexistent-target reaches. Also catches a re-affirmed tail that the changed fiction has made impossible.
2. **Scoper segmentation** peels off `lead_up` and `deferred_tail`; only the single `contested_beat` is rolled. The tail is *held*, not passed downstream.
3. **Input-starvation (structural).** The narrator receives only `lead_up + contested_beat + outcome + effect + consequence`. It physically cannot narrate the chain because the chain isn't in its context. **This — not a narrator prompt — is the enforcement.** Effect still governs *how far one success carries within the resolved beat*, but that's a quality dial, not the anti-chaining mechanism.

---

## 4. Target graph topology

Replace the single `action_generator` node with the resolution subgraph:

```
START → intent_alignment → [ RESOLUTION ] → narrator → END

RESOLUTION:
  scoper ──(no contested beat)──────────────────────────────────► narrator(lead_up only)
    │  segments → {lead_up, contested_beat, deferred_tail}
    │  deferred_tail ──► held in state (pending_intent), NOT passed downstream
    └──(contested beat)──► ┌─ attribute ─┐
                           ├─ position ──┤─► join ─► [dice: code] ─► consequence ─► (offer/resolve)
                           ├─ effect ────┤
                           └─ stakes ────┘
                                                                         │
  narrator receives ONLY: lead_up + contested_beat + outcome + effect + consequence
```

- **Scoper = gate + segmenter** (one judgment): finds the first beat needing a roll; if
  none, the whole message is `lead_up` → no roll → narrate it. Everything after the first
  contested beat is `deferred_tail`, peeled off and **held** (see decision #10), never
  passed to the narrator.
- **Framing fan-out** (`attribute`, `position`, `effect`, `stakes`) = parallel edges off
  the scoped beat; they read the `contested_beat` + context and are mutually independent.
- **Dice** are rolled in **deterministic code**, not by an LLM (real probability; the
  random draw stays out of the model's hands).
- **`consequence`** stage tags each consequence with its **resistance channel**
  (`{type, channel: corpus|mens|anima, severity}`) so resistance needs no re-classification.
  If consequences can stack, fan out with **`Send`**.
- **Narrator is bounded by construction** — it only ever sees the single resolved beat and
  its outcome, so it cannot chain (decision #9).
- **Resistance** is a *separate turn*: if a consequence is significant + resistible, the
  turn ends with the consequence narrated and an offer; the player's typed reply
  re-enters via a `resistance_history` carry (mirrors `intent_alignment_history`).

### Tail lifecycle (worked)
1. Player: *"cross the courtyard, cut down the guard, then grab the crown."*
2. Scoper → `lead_up`: cross courtyard · `contested_beat`: cut down guard · `deferred_tail`: grab the crown.
3. Beat rolled + narrated; narrator never sees "grab the crown". Tail stored as `pending_intent`.
4. Next turn the hint widget shows `continue: grab the crown`. Empty-enter accepts; typing overrides.
5. If accepted, "grab the crown" enters the **whole pipeline fresh** and is re-scoped against
   the now-changed fiction (guard dead, alarm maybe raised) — peeling the next contested beat.
   The tail shrinks one beat per turn until empty.

---

## 5. DSPy module inventory (1 signature + 1 node each)

| Module | Task | Output |
|--------|------|--------|
| **intent-type router** | is this a *contested action* or a *vice / relief act*? (extensible: gather-info, etc.) | enum → routes to action path or vice path |
| **scoper** (gate + segmenter) | segment the message; find the first beat needing a roll | `{lead_up, contested_beat \| none, deferred_tail}` — `none` ⇒ no roll |
| **attribute selector** | which of Corpus / Mens / Anima | 3-way |
| **position judge** | controlled / risky / desperate | 3-way |
| **effect judge** | limited / standard / great | 3-way |
| **stakes namer** | what's at risk if it goes bad | short text |
| *dice* | take-highest resolution | numbers (code, no LLM) |
| **consequence selector** | given result + position, pick consequence | enum + text + `channel` |
| **resist parser** | resist vs endure (typed reply) | binary; raw text passed through as flavor |
| **vice matcher** | does this indulgence match one of the character's vices? | bool + which vice (gates the relief path) |
| *vice clear* | roll lowest attribute, clear stress; overindulge if roll > current stress | numbers (code, no LLM) |
| **narrator** | prose of the resolved beat | prose — **bounded by construction**: receives only `lead_up + contested_beat + outcome + effect + consequence`, never the tail |

> The gate and scoper are **merged** (decision #9): one segmentation judgment that emits
> `contested_beat = none` to mean "no roll needed". Whether splitting them back out helps a
> given small model is a playtest question.

---

## 6. Stress, vice & trauma (decisions #11–14)

The survival economy. Two intent paths share one stress track.

### Stress out (it rises)
- **Resistance** (hot path). Always works — no fail branch. The player chooses to resist a
  consequence; we roll the consequence's **channel attribute** (pool = that rating, take
  highest) and charge **`6 − highest die`** stress (6 → 0, 1 → 5). A **crit (2+ sixes)
  clears 1 stress** instead. The consequence is then reduced/avoided (how much it mitigates
  ties into the position→severity table — open node).
- **Push-yourself**: 2 stress for +1d or bumped effect.

### Stress in (it falls) — vice only
- **Continuous, fiction-gated.** No downtime phase. The intent-type router detects a
  vice/relief act and routes it to the vice path (not the action fan-out).
- **vice matcher** checks the indulgence against the character's freeform vice descriptor(s).
- **Clear** = roll **lowest attribute**, clear that many stress. If the roll **> current
  stress → overindulge** → a complication. The overindulgence rule *is* the anti-spam gate:
  safe when strung-out, risky when nearly fresh.

### Overflow → trauma → permadeath
- Stress overflow ⇒ reset to 0, **+1 trauma + a trauma condition**.
- **4 trauma ⇒ the character is lost** (retired/dead/broken); a new one begins.

### Vices accumulate (trauma-linked scar-record)
- Start with **one** freeform vice; **each trauma grants a new one** — a coping mechanism
  born from the wound. More vices broadens *access* (more fictions qualify as relief), not
  *power* (clear is still roll-lowest + overindulgence gate). A veteran near max trauma has
  several crutches and almost no margin.

### State home (note)
Stress, trauma, and the accumulating vice list are **mutable per-run state**, not part of the
static `CharacterData` dataclass — they live with persisted character/run state. (Exact home
is an open node; `CharacterData` only needs the *starting* vice + attributes.)

---

## 7. Open nodes (agenda)

Tackle these next, against this saved foundation:

- [x] ~~**Stress & trauma track**~~ — done (§6, decisions #11–14).
- [ ] **Overindulgence & trauma specifics** — overindulgence complication (likely reuse the
      consequence machinery / narrated complication); trauma-condition representation
      (freeform vs list); the **"character lost" endgame flow** (new character in same world?
      game-over? campaign continuity — touches world/character services + TUI).
- [x] ~~**Position → consequence-severity mapping**~~ — done (decisions #15–16, table above).
- [ ] **Persistent harm model** — when a consequence's type is `harm`, what does the wound
      *do* afterward? Own harm track (BitD-style, with mechanical penalties) vs folded into
      stress/trauma/conditions. Note: rest was cut, so a separate harm track needs a healing
      path or it becomes a death spiral. Also: where Fatal enters (lethal fiction vs harm stacking).
- [ ] **Effect → reach-within-beat spec** — effect no longer enforces anti-chaining
      (decision #9 does, structurally). Remaining question: how `effect` shapes *how much
      of the single resolved beat* a success accomplishes (limited/standard/great) as a
      narration quality dial.
- [ ] **Crit & success benefits** — what a critical (2+ sixes) and a clean 6 grant beyond
      "it works".
- [ ] **Character creation flow** — how the ~4 dots get assigned (UI already has
      `value_stepper` / `pip_selector` widgets and a `create_character` modal).
- [ ] **Advancement / XP** — triggers, raising attributes toward the 4 cap.
- [ ] **Clocks** — adopt BitD progress/danger clocks? Where stored, who advances them.
- [ ] **Other roll types** — fortune rolls, gather-information, flashbacks: in or out of
      initial scope.
- [ ] **State additions** — `GraphState` fields for: `intent_type`, `lead_up`,
      `contested_beat`, `deferred_tail`, attribute/position/effect, dice result + tier,
      pending consequence (+channel), `resistance_history`, pending offer. Per-run character
      state: `stress`, `trauma`, accumulating `vices`. Mind the parallel-write reducer pattern.
- [ ] **TUI: hint widget** — dedicated dim label above the input (persists while typing,
      styled `continue:` prefix), `pending_intent` on `GameScreen`, empty-enter-accepts
      wiring in `ChatPanel` (decision #10).

---

## 8. Open questions deferred to playtest
- Exact lean budget (`{2,1,1}` vs `{2,2,0}` vs tunable).
- Exact stress/trauma track size (default 9/4; lean resistance-heavy economy may want shorter).
- Whether `gate`+`scoper` merge is safe on the target small model.
- Resistance attribute when the player's flavor implies a *different* channel than the
  consequence's tag (current rule: consequence channel wins; flavor colors prose only).
- How much a resistance roll mitigates (full avoid vs reduce-by-one-level) — ties to the
  position→severity table.
