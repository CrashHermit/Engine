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

### Over-reach defense, in layers
1. **Intent alignment** (exists) rejects impossible / nonexistent-target reaches.
2. **Beat scoper** rolls only the first contested beat; the rest is deferred.
3. **Effect** sets how far one success carries; the **narrator is bound to stop at the
   edge of granted effect**, at the next point of uncertainty — which becomes the next
   prompt. (Narrator bound is an open spec item — see §6.)

---

## 4. Target graph topology

Replace the single `action_generator` node with the resolution subgraph:

```
START → intent_alignment → [ RESOLUTION ] → narrator → END

RESOLUTION:
  gate ──(no roll)─────────────────────────────────────────────► (mundane narration)
    └──(roll)──► scoper ──► ┌─ attribute ─┐
                            ├─ position ──┤─► join ─► [dice: code] ─► consequence ─► (offer/resolve)
                            ├─ effect ────┤
                            └─ stakes ────┘
```

- **Framing fan-out** (`attribute`, `position`, `effect`, `stakes`) = parallel edges off
  `scoper`; they read the scoped beat + context and are mutually independent.
- **Dice** are rolled in **deterministic code**, not by an LLM (real probability; the
  random draw stays out of the model's hands).
- **`consequence`** stage tags each consequence with its **resistance channel**
  (`{type, channel: corpus|mens|anima, severity}`) so resistance needs no re-classification.
  If consequences can stack, fan out with **`Send`**.
- **Resistance** is a *separate turn*: if a consequence is significant + resistible, the
  turn ends with the consequence narrated and an offer; the player's typed reply
  re-enters via a `resistance_history` carry (mirrors `intent_alignment_history`).

---

## 5. DSPy module inventory (1 signature + 1 node each)

| Module | Task | Output |
|--------|------|--------|
| **roll gate** | danger + uncertainty present? | `bool` |
| **beat scoper** | first contested action | one clause (or "none" → no roll) |
| **attribute selector** | which of Corpus / Mens / Anima | 3-way |
| **position judge** | controlled / risky / desperate | 3-way |
| **effect judge** | limited / standard / great | 3-way |
| **stakes namer** | what's at risk if it goes bad | short text |
| *dice* | take-highest resolution | numbers (code, no LLM) |
| **consequence selector** | given result + position, pick consequence | enum + text + `channel` |
| **resist parser** | resist vs endure (typed reply) | binary; raw text passed through as flavor |
| **narrator** | prose, **bounded by granted effect** | prose |

> Candidate merge to revisit by playtest: `gate` + `scoper` can be one module if the
> scoper emits "none" to mean "no contested beat" (= no roll), saving a call.

---

## 6. Open nodes (agenda)

Tackle these next, against this saved foundation:

- [ ] **Stress & trauma track** — track size, what happens at max stress (trauma), how
      resistance spends stress (roll the channel, take 6 − highest die as stress cost).
      Load-bearing because the lean tone makes resistance frequent.
- [ ] **Position → consequence-severity mapping** — the concrete table (controlled/risky/
      desperate × outcome tier → consequence magnitude).
- [ ] **Effect → narration-reach spec** — how the narrator is *bound* to stop at the edge
      of granted effect (the anti-chaining enforcement). Likely a narrator input + prompt
      constraint.
- [ ] **Crit & success benefits** — what a critical (2+ sixes) and a clean 6 grant beyond
      "it works".
- [ ] **Character creation flow** — how the ~4 dots get assigned (UI already has
      `value_stepper` / `pip_selector` widgets and a `create_character` modal).
- [ ] **Advancement / XP** — triggers, raising attributes toward the 4 cap.
- [ ] **Clocks** — adopt BitD progress/danger clocks? Where stored, who advances them.
- [ ] **Other roll types** — fortune rolls, gather-information, flashbacks: in or out of
      initial scope.
- [ ] **State additions** — `GraphState` fields for: scoped beat, attribute/position/
      effect, dice result + tier, pending consequence (+channel), `resistance_history`,
      pending offer, stress. Mind the parallel-write reducer pattern.

---

## 7. Open questions deferred to playtest
- Exact lean budget (`{2,1,1}` vs `{2,2,0}` vs tunable).
- Whether `gate`+`scoper` merge is safe on the target small model.
- Resistance attribute when the player's flavor implies a *different* channel than the
  consequence's tag (current rule: consequence channel wins; flavor colors prose only).
