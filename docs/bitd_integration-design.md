# Blades in the Dark — Resolution Integration Design

> **Status:** Living design doc. The decisions in §3 are locked; §8 is the open agenda.
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
  attributes already exist in the data model. *(They are stored as implied 0–100 ints
  today; **decision #20** moves the whole sheet to a unified **0–4** dot scale.)*
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
| 7 | **Dice: take-highest, outcome *scales the threat*** *(revised under #17)*. Ratings **0–4**; pool = the attribute's rating (0 = roll **2d6 take the worst**). Take highest die → **6 = avoid** the threat · **4–5 = reduced** (magnitude −1) · **1–3 = full** threat · **two+ 6s = crit** (avoid + benefit). **No pre-roll push** (Deep Cuts removes it); bonus dice only from **assist / devil's bargain** (TBD). `failure-of-goal` is itself a threat type, so the roll can still fail the action (see #16). | Keeps the lean take-highest curve on the three attributes, but adopts Deep Cuts' graceful **avoid / reduced / full** scaling instead of classic's success/partial/fail. |
| 8 | **Lean ~4-dot starting budget** (e.g. `{2,1,1}` or `{2,2,0}`), ratings grow toward the 4 cap via advancement. | Three broad attributes inflate pools vs BitD's 12 thin actions; a lean budget keeps typical pools at **1–2 dice**, preserving the gritty, swingy "competence is earned" tone. Consequence: 4–5 and 1–3 are the *common* results, so the consequence/resistance pipeline is the engine's **hot path**. |
| 9 | **Anti-chaining is enforced by input-starvation, not by the narrator.** The narrator is *not* trusted to "stop at the edge of effect". Instead the **scoper segments the message into `{lead_up, contested_beat, deferred_tail}`**, and the narrator only ever receives `lead_up + contested_beat + outcome + effect + consequence` — never the tail or the raw full chain. It cannot run ahead because the rest isn't in its context. *(Per #18, the gate and segmenter are **split**: a binary `roll-gate` runs first; the `segmenter` runs only on gate=true.)* | Asking a generative model to self-limit mid-prose is a soft constraint that fails exactly when needed (worse on small models). Robustness comes from controlling the narrator's **input**, guaranteed by the graph. |
| 10 | **Deferred tail is held as a passive *suggestion*, never an execution queue.** It is stored (`pending_intent`) and surfaced next turn via a **dedicated hint widget** (a dim line above the input that persists while typing, with a styled `continue:` prefix; empty-enter accepts it, typing overrides it). Re-affirming the tail sends it back through the **whole pipeline** as a fresh message, so it is **re-scoped against the updated fiction**; it is never auto-rolled from storage. | After a consequence the fiction has changed, so a stale queued action shouldn't auto-execute — the player should re-decide. Reusing the full pipeline means no special resume code, no stale actions, and natural recursion (a multi-beat plan peels one contested beat per turn). |
| 11 | **Unified push/resist; flat stress cost; always works** *(revised under #17)*. Pre-roll push is gone. *After* a roll, spend stress (roll the relevant attribute, take highest) to **bump the outcome one step** (1–3→4–5→6, i.e. reduce a consequence one magnitude) **or** gain more effect. Cost is **flat** by the push roll's highest die: **crit 0 · 6→1 · 4–5→2 · 1–3→3**. The improvement always lands; dice only set the price. Default track **9 stress / 4 trauma** (tunable). | Deep Cuts' cleaner 0–3 scale and push/resist unification (one mechanic, not two). Still "always works, dice set price"; still the **hot path** with lean pools. |
| 12 | **Relief is vice-only, continuous and fiction-gated** (rest was considered and cut). Indulging in the fiction (right place/moment) routes to a vice-resolution: **roll your lowest attribute, clear that many stress**; if the roll **exceeds current stress you overindulge** → a complication. No formal downtime phase. | Canonical BitD relief. The overindulgence rule *is* the anti-spam gate (safe when strung-out, risky when nearly fresh), so vice-only + permadeath stays balanced without cooldown state. Continuous/fiction-gated fits the engine (no mission/downtime structure exists). Designed to be downtime-slottable later. |
| 13 | **Permadeath at max trauma.** Stress overflow → reset to 0, gain **1 trauma + a trauma condition**; at **4 trauma the character is lost** (retired/dead/broken) and a new one begins. | Failure has real teeth; stories get endings. The lean, resistance-heavy economy means trauma genuinely accrues. |
| 14 | **Vices are freeform descriptors that accumulate, trauma-linked.** Characters start with one freeform vice; **each trauma grants a new one** — a coping mechanism born from the wound, building a *scar-record*. More vices broadens *access* (more fictions qualify as relief), **not power** (clear is still roll-lowest + overindulgence gate). | Marries relief and permadeath into one grim bargain — every step toward being lost hands you a new way to cope. Freeform matches the engine's LLM-driven, broad-category ethos. |
| 15 | **Consequence = structured threat (classifiers) *scaled by outcome*** *(revised under #17, split under #18)*. Three classifiers fix the threat **before the roll**: **type** (harm / complication / worse-position / lost-opportunity / **failure-of-goal**), **channel** (corpus/mens/anima), **magnitude** on `Minor(1) / Standard(2) / Severe(3) / Fatal(4)`. **Code scales by the roll** (6 avoid · 4–5 mag−1 · 1–3 full); push/resist reduces one more step. The **narrator** writes all fiction, post-roll, from the landed threat. | Keeps the balance-critical magnitude structured (safe on small models), isolates generation to the narrator, and unifies harm levels + all consequence types under one 1–4 ladder that also feeds body-part status. |
| 16 | **Position collapsed; failure stays real** *(replaces position-only)*. **No per-roll position judge**: **risky is the default**; a lightweight fiction flag escalates to **desperate** (4–5 counts as full; only a 6 avoids) or relaxes to **controlled** (rare). **`failure-of-goal` is a common, first-class threat type** — not auto-success. | Deep Cuts de-emphasises position → one fewer module for small models. Keeping failure-as-threat preserves the gritty "you might not pull it off" feel *and* keeps the model **classifying**, not open-authoring. |
| 17 | **Resolution = Deep Cuts cherry-pick (hybrid).** Keep a lightweight **action-roll frame** (you attempt X; failure is possible), but adopt Deep Cuts' mechanical upgrades: **avoid/reduced/full** scaling (#7), **unified push/resist + flat 0/1/2/3 cost** (#11), one **1–4 magnitude ladder** (#15), **collapsed position** (#16). **Rejected:** the *full* threat roll (effect fully decoupled / always-accomplish) — it leans hardest on the model's weakest skill (open threat authoring) and softens real failure. | Best-of-both: Deep Cuts' clean math + fewer structural judgments, without its agency-softening or heavier authoring burden. Better fit for small models, the gritty tone, and the model's far stronger familiarity with *classic* Blades. |
| 18 | **Prefer maximal module splitting for trainability.** Where a step would emit several outputs, split it into **one narrow single-judgment module per output** (separate classifiers for each label); isolate generation to the narrator. Concretely: gate split from segmenter (revises #9); `threat-namer` split into `threat-type` + `threat-magnitude` + `threat-channel`, with its fiction folded into the narrator. | Pure classifiers get **crisp metrics**, cheap bootstrapped datasets, and far better DSPy optimisation (`BootstrapFewShot`/`MIPROv2`), and each can run on the **cheapest adequate model**. Independent classifiers fan out in parallel, so splitting rarely costs latency. |
| 19 | **Persistent harm = a tunable damage pool per body part; `Status` is derived** *(model "C")*. Each part on the body graph carries a small **wound-box pool**; a `harm` threat fills **`magnitude` boxes** on a fiction-chosen part (boxes **accumulate** — small wounds add up). The `Status` enum becomes a five-rung ladder — **NORMAL / GRAZED / COMPROMISED / CRITICAL / DESTROYED**, 1:1 with the magnitude scale — and is **computed from box-fill thresholds**, not stored, so the rest of the engine still reads a clean word. **DESTROYED** detaches the part (and everything distal) from the graph; **Fatal / overflow on a vital part = death** (#13). Mechanical bite feeds back via the part's **`PartFunction` + derived status** into the effect / threat-magnitude classifiers. **Healing removes boxes** (fiction-gated treatment → granular partial recovery). Box count + thresholds are **code-side dials** (default gritty, tuned at playtest). | Accumulates like BitD harm while keeping a legible status as a *derived* view and full tuning latitude — the knob-in-code ethos used throughout. Costs one integer per part (the graph already stores parts), and healing-by-box falls out naturally. **Rejected:** absolute "worst-wound" mapping (no accumulation, fixed lethality) and fixed additive steps (untunable). |
| 20 | **Unified 0–4 "dot" scale for the whole character sheet.** **Corpus / Mens / Anima are the dice ratings** (pool = rating; 0 = 2d6-take-worst, #7) on **0–4**, allocated from the lean dot budget (#8) and advanced toward the 4 cap. The **Big-Five traits move to the same 0–4 scale** — *not* dice pools but flavor/steering signal for the narrator + intent classifiers, dot-allocated at creation. **Replaces the implied 0–100 ints** in `CharacterData` and the ArcadeDB attribute/personality value nodes. | One coherent dot-allocation model for character building — the player just spends dots — matching the locked budget/advancement decisions (#8). A 0–4 personality band (with a label) is **more legible signal for a small LLM** than an arbitrary 0–100, and far simpler to author. Cost: a data-model + DB-value migration and a char-creation tweak (`value_stepper` / `pip_selector` already exist). |
| 27 | **All parts (corpus, mens, anima) are generated at character creation — no fixed canonical lists.** `PartFunction` tags are fixed enums (the typed signal classifiers reason on); surface names are character-authored/generated. Applies uniformly to body, mind, and spirit. | Consistent with the engine's broad-category, LLM-driven ethos. Gives players immediate narrative ownership of what their character's body, psyche, and soul *are*, while keeping classifier signal clean via fixed function tags. |
| 26 | **Mind parts (mens) and spirit parts (anima) are first-class parts.** The wound-box model (#19) applies uniformly across all three channels. A `harm` threat on any channel lands on a part from that channel's pool (body / mind / spirit). `Status`, `PartFunction`, and the `threat-part` classifier all span all three. Amends #25: `threat-part` is active for corpus, mens, and anima. | Extends a proven model rather than adding a second system. Stress remains the *shared* economy (push/resist cost); part damage is *localized* impairment on top of it. |
| 29 | **Harm targets functional capability pools, not individual parts. Amends #19, #25, #27.** Each character has a slottable budget of functional pool slots allocated at creation — a pool slot is typed by `PartFunction` category and stacking is allowed (e.g. 3× MANIPULATOR + 1× MOVEMENT = a three-armed snake). Each slot is an independent wound pool. The `threat-function` classifier (replaces `threat-part`, #25) selects a `PartFunction` category; if multiple slots share that type, the most contextually appropriate one takes the damage. DESTROYED on a slot = that slot non-functional (#28); all slots of a type destroyed = that function fully lost. **Slot budgets are per-channel** (#30): each of corpus / mens / anima has its own fixed allocation. Budget sizes and whether they tie to attribute ratings are deferred to playtest/character-creation design. `PartFunction` enum left unchanged for now — to be revisited. | Stacking lets creatures/characters express anatomy naturally (three arms, two minds, etc.) while keeping the damage model uniform. Each slot failing independently gives granular attrition. Per-channel budgets ensure every character has presence in all three domains. |
| 32 | **Crit benefit is narrator-authored freeform.** On 2+ sixes the threat is avoided and the narrator invents a contextually appropriate benefit from the fiction (positional advantage, information, resource, unexpected opening, etc.). No classifier. | Benefits are additive and have no balance risk, so narrator creative latitude is safe here. A classifier can't improve on a narrator that already knows the full scene. |
| 31 | **Effect classifier dropped.** The narrator derives success quality directly from `{outcome tier + threat-as-landed}`. Anti-chaining is structural (#9); roll outcome (avoided/reduced/full) already encodes how well the beat went. Framing fan-out is 4 parallel classifiers: attribute, threat-type, threat-magnitude, threat-channel + threat-function. | Eliminates the weakest module in the inventory. No information lost — the narrator has everything it needs from outcome tier and threat. |
| 30 | **Functional pool slot budgets are per-channel.** Corpus, mens, and anima each have their own fixed slot allocation at creation. Guarantees minimum presence in all three domains; cleaner for balance than a unified pool. Whether the per-channel budget ties to the attribute dot rating is deferred to playtest. | A character with zero mental or spiritual pools is an unhandled edge case; per-channel budgets prevent it structurally. |
| 28 | **DESTROYED = non-functional, uniformly across all three channels. Amends #19.** A DESTROYED part (corpus, mens, or anima) cannot perform its `PartFunction` but still exists. Healing (fiction-gated box removal) can recover even from DESTROYED. The detachment/distal-cascade rule from #19 is removed. Vital parts: DESTROYED triggers the permadeath path (#13) regardless of channel. | Makes the status ladder identical across body, mind, and spirit — simpler implementation, no channel-special-casing, and recovery is always possible in principle. Severance was body-only physics with no clean mental/spiritual equivalent. |
| 25 | **Harm-location = `threat-part` classifier in the framing fan-out.** Runs in parallel with `threat-type` / `threat-magnitude` / `threat-channel`; takes `{contested_beat, threat description, body state}` and returns a part ID. Active only when `threat-channel = corpus`. The part is known before the roll and before the narrator writes, giving the harm machinery a clean typed target. | Parallel timing costs no latency; one narrow judgment per module (#18); avoids fragile narrator-to-extractor round-trips. |
| 24 | **Overindulgence complication reuses the consequence machinery.** Overindulgence generates a structured `{type, magnitude, channel}` threat via the same classifiers and narrator as combat consequences. Magnitude is capped at Standard (2) — a setback, not a death sentence. | No new code paths; mechanically legible to the player; classifiers already fan out in parallel so overhead is minimal. |
| 23 | **"Character lost" endgame = new character, same world, continuity.** At 4 trauma the old `CharacterData` is flagged `retired/lost` and persists in the world (available as NPC or memory). The TUI transitions to the character-creation flow; the run continues in the same world with the replacement. World state (location, entities) carries over. No data is destroyed. | Matches BitD's legacy-game ethos; costs only a status flag + a TUI transition. The replacement flow (dot-allocation UI) is already partially built. Clean slate (option B) loses narrative continuity; silent removal (option C) loses the NPC echo. |
| 22 | **Trauma conditions = structured tag + freeform display label.** Each trauma condition carries a typed `TraumaCategory` enum tag (for classifier reasoning) and a narrator-generated freeform label (what the player sees). Taxonomy is content-mode-aware — a clean set now, adult set added when adult mechanics land. Conditions accumulate alongside vices as a scar-record. | Freeform alone can't support future mechanical hooks; a full fixed list is too rigid for adult content extensibility. The hybrid gives classifiers a clean type while keeping the surface feel organic. |
| 21 | **Effects are applied at the integration boundary, not inside graph nodes.** Graph nodes stay **pure** — they read `GraphState` and emit *intended* effects (the resolved roll, harm to apply, a stress delta) back into state; they never touch repositories or services. After `ainvoke`, the **TUI applies those effects via services** (which own the transactions over the repos), exactly as it already post-processes the result and owns the `ServiceContainer`. The Phase-0 mechanics core returns plain data precisely so a service can persist it. | Matches the locked layering (`ServiceContainer`: screens/nodes talk to services, **never repos**) and the engine's current shape (graph built once, `GraphState` rebuilt per turn, no DB session injected into nodes). Keeps nodes **unit-testable offline** (no DB/LLM), keeps services the **single write path**, and avoids coupling the graph to a live ArcadeDB session. **Rejected:** injecting `ServiceContainer` into nodes — preserves the rule but couples the graph to the DB and hurts node testability. |

### Resolution model — Deep Cuts cherry-pick (#15–18)

Per contested beat: establish **effect** (what success looks like) and have the three threat
classifiers (`threat-type`, `threat-magnitude`, `threat-channel`) produce the structured threat
= `{type, magnitude 1–4, channel}` (its **fiction is written by the narrator**, post-roll). Roll
the attribute pool, take highest:

| highest die | how the threat lands |
|---|---|
| **crit (2+ 6s)** | avoided **+ a benefit** |
| **6** | avoided (magnitude → 0) |
| **4–5** | **reduced** — magnitude −1 |
| **1–3** | **full** magnitude |
| *(desperate flag)* | 4–5 counts as **full**; only a 6 avoids |

Magnitude ladder: `0 none · 1 Minor · 2 Standard · 3 Severe · 4 Fatal`. **Push/resist** (post-roll,
unified) bumps the result one step / reduces magnitude one more, at flat cost
**crit 0 · 6→1 · 4–5→2 · 1–3→3** stress. Because `failure-of-goal` is a valid threat type, a
full (or reduced) result can mean you don't accomplish the beat. **Code owns magnitude + scaling;
the classifiers own type / magnitude / channel; the narrator owns all fiction.**

### Over-reach defense, in layers
1. **Intent alignment** (exists) rejects impossible / nonexistent-target reaches. Also catches a re-affirmed tail that the changed fiction has made impossible.
2. **Segmenter** peels off `lead_up` and `deferred_tail`; only the single `contested_beat` is rolled. The tail is *held*, not passed downstream.
3. **Input-starvation (structural).** The narrator receives only `lead_up + contested_beat + outcome + effect + consequence`. It physically cannot narrate the chain because the chain isn't in its context. **This — not a narrator prompt — is the enforcement.** Effect still governs *how far one success carries within the resolved beat*, but that's a quality dial, not the anti-chaining mechanism.

---

## 4. Target graph topology

Replace the single `action_generator` node with the resolution subgraph:

```
START → intent_alignment → [ RESOLUTION ] → narrator → END

RESOLUTION (Deep Cuts cherry-pick):
  gate ──(no roll)──────────────────────────────────────────────► narrator(lead_up only)
    └──(roll)──► segmenter ── {lead_up, contested_beat, deferred_tail}
                    │           deferred_tail ──► held (pending_intent), NOT downstream
                    └──► ┌─ attribute ────────┐
                         ├─ threat-type ──────┤─► join ─► [dice + scale: code] ─► (offer/resolve)
                         ├─ threat-magnitude ─┤            (6 avoid · 4-5 mag-1 · 1-3 full)
                         ├─ threat-channel ───┤
                         └─ threat-function ──┘                        │
  narrator receives ONLY: lead_up + contested_beat + outcome + threat-as-landed
```

- **Gate** (binary, #9 revised): does the beat carry **danger + uncertainty**? If not →
  `lead_up` → no roll → narrate. If yes → segmenter.
- **Segmenter** (runs only on gate=true): split into `{lead_up, contested_beat, deferred_tail}`;
  the tail is peeled off and **held** (decision #10), never passed to the narrator.
- **Framing fan-out** — five parallel classifiers off the scoped beat (`attribute`, `effect`,
  `threat-type`, `threat-magnitude`, `threat-channel`), mutually independent. **`position` is
  gone** (risky default + desperate flag, #16); the old `threat-namer` is **split into three
  classifiers** (#18) with its fiction folded into the narrator.
- **Dice + scaling** in **deterministic code** (roll take-highest → avoid/reduced/full per
  #15–17). If multiple threats stack, fan out with **`Send`**.
- **Narrator is bounded by construction** — it only ever sees the single resolved beat and
  its outcome, so it cannot chain (decision #9).
- **Resistance** is a *separate turn*: if a consequence is significant + resistible, the
  turn ends with the consequence narrated and an offer; the player's typed reply
  re-enters via a `resistance_history` carry (mirrors `intent_alignment_history`).
  Push/resist is unified (#11): the same offer also covers spending stress for more effect.

### Tail lifecycle (worked)
1. Player: *"cross the courtyard, cut down the guard, then grab the crown."*
2. Gate → roll needed; segmenter → `lead_up`: cross courtyard · `contested_beat`: cut down guard · `deferred_tail`: grab the crown.
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
| **roll-gate** | does the beat carry danger + uncertainty? | bool — `false` ⇒ no roll |
| **segmenter** (gate=true only) | split message around the first contested beat | `{lead_up, contested_beat, deferred_tail}` |
| **attribute selector** | which of Corpus / Mens / Anima | 3-way |
| ~~**effect judge**~~ | ~~what success accomplishes (limited / standard / great)~~ | *dropped — decision #31* |
| **threat-type** | kind of threat | 5-way (harm / complication / worse-position / lost-opportunity / failure-of-goal) |
| **threat-magnitude** | how bad | 1–4 (Minor / Standard / Severe / Fatal) |
| **threat-channel** | which attribute resists it | 3-way (corpus / mens / anima) |
| *dice + scale* | take-highest → avoid / reduced (mag−1) / full | numbers (code, no LLM) |
| **resist/push parser** | resist / endure / push-for-effect (typed reply) | enum; raw text passed through as flavor |
| **vice matcher** | does this indulgence match one of the character's vices? | bool + which vice (gates the relief path) |
| *vice clear* | roll lowest attribute, clear stress; overindulge if roll > current stress | numbers (code, no LLM) |
| **narrator** | prose of the resolved beat (incl. the threat's fiction) | prose — **bounded by construction**: receives only `lead_up + contested_beat + outcome + effect + threat-as-landed`, never the tail |

> Every LLM step above is a **single-judgment classifier** except the narrator (the lone
> generative module). This is decision **#18** (split for trainability): pure classifiers get
> crisp metrics + cheap datasets + better DSPy optimisation, and can be routed to the
> cheapest adequate model; the five framing classifiers fan out in parallel, so the split
> costs little latency.

---

## 6. Stress, vice & trauma (decisions #11–14)

The survival economy. Two intent paths share one stress track.

### Stress out (it rises) — unified push/resist (#11, #17)
- **Resist / push** (hot path). Always works — no fail branch. *After* a roll, spend stress
  to **bump the outcome one step** (reduce a consequence one magnitude) **or** gain more
  effect. Roll the relevant **attribute** (the threat's channel for resisting), take highest;
  charge a **flat** cost: **crit 0 · 6→1 · 4–5→2 · 1–3→3**. The improvement always lands;
  the dice only set the price.
- *(Pre-roll push for +1d is removed under Deep Cuts.)*

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

## 7. Harm & the body (decision #19)

Physical consequences live on the **existing body graph** (`core/model/part.py`), not on an
abstract harm track — Deep Cuts harm reimagined for an engine that already has anatomy.
Model **"C"**: each part is a small filling damage bar, and its status word is *read off* the bar.

### Wound boxes (the damage pool)
- Every part carries a small **wound-box pool** (default size is a code-side dial; sturdier
  parts may scale larger).
- A `harm` threat lands on a **fiction-chosen part** and **fills `magnitude` boxes**
  (Minor 1 · Standard 2 · Severe 3 · Fatal 4). Boxes **accumulate** — many small wounds
  eventually cripple a part.
- The magnitude that fills boxes is **already reduced** by the roll (4–5 → −1) and any
  push/resist (#11, #15) — the pool only ever sees what actually lands.

### Status is derived, not stored
- The `Status` enum becomes a five-rung ladder: **NORMAL → GRAZED → COMPROMISED → CRITICAL
  → DESTROYED**, **1:1 with the magnitude scale** so the narrator has a word for every level.
- Status is **computed from how full the pool is**, via thresholds (also code-side dials).
  Default tuning on a 4-box part maps the magnitude scale **1:1** onto the status scale for a
  single hit: `0 → NORMAL · 1 → GRAZED · 2 → COMPROMISED · 3 → CRITICAL · 4 → DESTROYED`
  (wounds still accumulate, so two Minors reach COMPROMISED). Every fill level has its own name.
- So the UI and every classifier still see a clean word; the bar lives underneath. This is
  why "C" beat storing the word directly (model "A"): **same legible read, but wounds
  accumulate and the curve is tunable** by moving the lines / adding boxes.

### Destruction & death
- **DESTROYED** = the part is lost: the body graph **detaches it and everything distal**
  (sever a thigh → the shin and foot go with it).
- **Fatal magnitude — or overflow — on a vital part = character death**, feeding the
  permadeath economy (a new character begins, #13).

### Feedback into framing (the mechanical bite)
- A wounded part bites through its **`PartFunction` + derived status**: when an intent leans
  on a function, the relevant classifiers see the impairment.
- A COMPROMISED/CRITICAL `MOVEMENT` part **worsens effect and/or raises threat-magnitude**
  on movement-leaning actions; a DESTROYED one removes that function outright. This loop is
  what makes harm *matter* turn-to-turn rather than being an inert number.

### Healing
- Treatment is **fiction-gated** and **removes boxes**, so recovery is **granular/partial**
  (good care drops a CRITICAL leg to COMPROMISED before it's whole). Exact rates/gates → playtest.

---

## 8. Open nodes (agenda)

Tackle these next, against this saved foundation:

- [x] ~~**Stress & trauma track**~~ — done (§6, decisions #11–14).
- [x] ~~**Overindulgence & trauma specifics**~~ — closed (decisions #22–24).
      - [x] **Overindulgence complication** — **Decision #24**: reuse the consequence machinery.
        Overindulgence produces a structured `{type, magnitude, channel}` threat, classified
        and narrated by the same pipeline. Magnitude capped at Standard (2) — a setback, not
        a death sentence.
      - [x] **Trauma-condition representation** — **Decision #22**: a structured **tag** (enum
        `TraumaCategory`) + a **freeform display label** generated by the narrator at overflow.
        The tag gives classifiers a clean type to reason on; the label is what the player sees.
        Taxonomy is content-mode-aware (clean set + adult set added later when adult mechanics
        are introduced). Conditions accumulate alongside vices as a scar-record.
      - [x] **"Character lost" endgame flow** — **Decision #23**: **new character, same world,
        continuity**. At 4 trauma the old `CharacterData` is flagged `retired/lost` and persists
        in the world (available as NPC/memory). The TUI transitions to the character-creation
        flow; the run continues in the same world with the replacement character. No data is
        destroyed. The world state (location, entities) carries over.
- [x] ~~**Position → consequence-severity mapping**~~ — superseded by the **Deep Cuts cherry-pick**
      (decisions #15–17): threat magnitude (1–4) scaled by outcome (avoid/reduced/full); position
      collapsed to risky-default + desperate flag; failure-of-goal is a threat type.
- [x] ~~**Persistent harm model**~~ — done (§7, decisions #19, #28–29): **functional pool model**
      (model "C"), `Status` gains **GRAZED + DESTROYED** (now 1:1 with the magnitude ladder)
      and is **derived from box-fill thresholds**,
      `PartFunction` + status feeds the effect/threat classifiers, healing removes boxes,
      DESTROYED severs via the graph, Fatal/overflow on a vital part = death. Box count +
      thresholds are code-side dials. **Remaining sub-details** below (part selection,
      non-corpus harm).
- [x] ~~**Harm-location selection**~~ — **Decision #25**: a **`threat-part` classifier** runs in
      the framing fan-out alongside `threat-type` / `threat-magnitude` / `threat-channel`.
      Takes `{contested_beat, threat description, body state}` → returns a part ID. Runs in
      parallel (no latency cost); gives the harm machinery a clean typed part before the roll
      and before the narrator writes anything. Consistent with decision #18.
- [x] ~~**Non-corpus harm routing**~~ — **Decision #26**: **mind parts (mens) and spirit parts
      (anima)** exist as first-class parts alongside body parts. A `harm` threat on any channel
      lands on a part from that channel's pool. The wound-box model (#19), `Status` ladder,
      `PartFunction`, and `threat-part` classifier (#25) all apply uniformly across corpus /
      mens / anima. Decision #25 amended: `threat-part` is active on **all three channels**,
      selecting from the appropriate part pool.
      - [x] **Canonical part lists** — **Decision #27**: **all parts (corpus, mens, anima) are
        generated at character creation** — no fixed canonical lists at engine level.
        `PartFunction` tags are fixed enums (classifiers reason on function); surface names
        are character-authored/generated. Part generation method is a **sub-node of the
        character creation flow** (§8) — deferred until the full description/creation system
        is designed (current description field is a placeholder).
      - [x] **DESTROYED semantics** — **Decision #28**: **DESTROYED = non-functional**, uniformly
        across corpus, mens, and anima. The part still exists but cannot perform its function.
        Healing (fiction-gated, removes boxes) can recover even from DESTROYED. **Amends #19**:
        the detachment/distal-cascade rule is removed — no part ever physically severs. Vital
        parts: DESTROYED on a vital part triggers the permadeath path (#13/#19) — the function
        loss is catastrophic regardless of channel.
- [x] ~~**Effect → reach-within-beat spec**~~ — **Decision #31**: **effect classifier dropped.**
      Anti-chaining is structural (#9); the roll outcome tier (avoided/reduced/full) already
      signals success quality to the narrator. The narrator derives narration quality from
      `{outcome tier + threat-as-landed}` directly. Framing fan-out reduced from 5 to 4
      parallel classifiers.
- [x] ~~**Crit & success benefits**~~ — **Decision #32**: crit benefit is **narrator-authored
      freeform**. The narrator reads the fiction and invents a contextually appropriate
      benefit (positional advantage, information, an unexpected opening, etc.). No classifier;
      the narrator owns it entirely. Safe to be generous — benefits are additive, not a gate
      or consequence.
- [ ] **Character creation flow** — how the ~4 dots get assigned (UI already has
      `value_stepper` / `pip_selector` widgets and a `create_character` modal). Also owns
      **part generation** (decision #27 sub-node): blocked on the full description system
      (current description field is a placeholder).
- [ ] **Advancement / XP** — deferred. Out of initial scope. Most natural trigger designs
      when we return: per-roll XP on 1–3 outcomes (learn from failure), or milestone/story-beat
      detection. Doesn't block Phase 0–3.
- [ ] **Clocks** — deferred. A **world clock** concept is under consideration that may
      subsume or reshape per-scene progress/danger clocks. Revisit once the world model is
      better defined. Don't design BitD-style clocks in isolation until the world clock
      design is settled.
- [ ] **Other roll types** — fortune rolls, gather-information, flashbacks: in or out of
      initial scope.
- [ ] **State additions** — `GraphState` fields for: `intent_type`, `lead_up`,
      `contested_beat`, `deferred_tail`, `attribute`, `effect`, `threat` (+type/channel/magnitude),
      `position_flag` (default risky), dice result + tier, scaled-threat, `resistance_history`,
      pending offer. Per-run character state: `stress`, `trauma`, accumulating `vices`, and
      **per-part wound-box counts** on the body graph. Mind the parallel-write reducer pattern.
- [ ] **TUI: hint widget** — dedicated dim label above the input (persists while typing,
      styled `continue:` prefix), `pending_intent` on `GameScreen`, empty-enter-accepts
      wiring in `ChatPanel` (decision #10).

---

## 9. Open questions deferred to playtest
- Exact lean budget (`{2,1,1}` vs `{2,2,0}` vs tunable).
- Exact stress/trauma track size (default 9/4; lean resistance-heavy economy may want shorter).
- Resistance attribute when the player's flavor implies a *different* channel than the
  threat's tag (current rule: threat channel wins; flavor colors prose only).
- Bonus-dice sources under Deep Cuts (assist / devil's bargain) — exact rules TBD.
- Per-module model routing: which classifiers run on the tiniest model vs the narrator's
  stronger one (enabled by the #18 split) — tune by eval.
- Wound-box tuning (#19): default pool size, per-part-size scaling, where the
  COMPROMISED/CRITICAL/DESTROYED threshold lines sit, and healing rates.

---

## 10. Build plan (implementation phases)

Two sequencing principles fall out of the design + the current codebase (§2):

- **Spine vs. systems.** The resolution **spine** — `gate → segmenter → framing fan-out →
  dice/scale → narrator` — produces a complete, narratable turn *on its own*. The **systems**
  (stress/vice/trauma economy #11–14, persistent harm #19, resistance #6) hang off the threat
  result and are **strictly additive** — so we never have to build a half-broken whole.
- **Code vs. model.** A large, balance-critical slice of §5 is marked *"code, no LLM"*
  (dice, scaling, push cost, magnitude ladder, vice-clear) plus #19's wound pool. These are
  **pure functions** with zero model/graph/DB coupling — the most testable, highest-confidence
  thing in the project, and the natural first slice. Unsettled numbers enter as **parameters**,
  so "deferred to playtest" never blocks building.

Current baseline (from the code survey): `START → intent_alignment → action_generator →
narrator → END`; `GraphState` is a Pydantic model with `Annotated[list, operator.add]`
reducers; DSPy is raw `Predict` on **one** global LM (no compilation/routing); **no test
suite exists**; persistence is ArcadeDB via a services→repos layer; the TUI rebuilds
`GraphState` each turn.

### Phase 0 — Mechanics core + first test suite *(pure code; no LLM/graph/DB)*
- New `src/core/mechanics/`: `dice` (pool from 0–4 rating, take-highest, rating-0 =
  2d6-take-worst, crit = 2+ sixes → result tier), `scaling` (tier + base magnitude +
  desperate flag → landed 0–4), `push` (cost table + one-step bump), `harm` (`WoundPool`:
  fill boxes, derive `Status`; **extend the enum with `DESTROYED`**; a pure "which parts
  detach" helper), `economy` (stress→overflow→trauma→lost; vice-clear).
- Migrate the character sheet to **0–4** (#20): narrow type/validation + DB-value
  reinterpretation.
- Stand up **pytest** + a `tests/` tree; the deterministic functions make near-exhaustive
  tests cheap. All tunables are defaulted params.
- **Deliverable:** a tested mechanics library + green suite. Unblocks everything; no risk.

### Phase 1 — Walking skeleton *(graph wired, minimal LLM)*
- Replace `action_generator` with a resolution subgraph: a real `roll-gate`, **stubbed**
  framing (hardcoded attribute/threat), the Phase-0 code dice/scale, and the existing
  `narrator` **re-bounded to its #9 input** (`lead_up + contested_beat + outcome + effect +
  threat-as-landed`).
- Extend `GraphState` with the resolution fields (see agenda §8 → State additions).
- **Deliverable:** one turn flows end-to-end and narrates a *scaled* outcome through the TUI.
  Proves wiring, state shape, and narrator-bounding before any classifier work.

### Phase 2 — Classifiers *(one at a time, replacing stubs)*
- `segmenter`, `attribute`, `effect`, `threat-type` / `threat-magnitude` / `threat-channel`
  — each **1 signature + 1 node** (the existing `action_generator`→`narrator` pattern).
- Wire the **parallel framing fan-out** (the five must write **disjoint** `GraphState` keys,
  or use reducers, to avoid lost concurrent writes).
- Stand up a **minimal DSPy eval set** per classifier (a metric *before* optimizing).
  Compilation (`BootstrapFewShot`/`MIPROv2`) and per-module model routing are **deferred** —
  classifiers ship zero-shot on the single LM first.

### Phase 3 — Systems
- Connect the threat result to **harm/body** (`WoundPool` persisted on PART vertices; sever
  via a service) and the **stress/trauma** economy (per-run state home on the CHARACTER).
- Add **resistance/push** as the reactive follow-up turn: a `resistance_history` carry
  mirroring `intent_alignment_history`, plus the `resist/push parser`.
- Add the **vice path**: `intent-type router` + `vice matcher` + code `vice-clear`.

### Phase 4 — TUI & polish *(largely done)*
- [x] **Integration boundary** (decision #21): `src/tui/turn_effects.py` — a Textual-free
  `apply_turn_effects` (persists harm/stress via services after `ainvoke`) + `next_turn_carry`
  (deferred tail + resistance offer). `GameScreen` calls it post-narration. Unit-tested.
- [x] Deferred-tail **hint widget** + `pending_intent` on `ChatPanel` (dim `continue:` line,
  toggled via `display`); **empty-enter-accepts**, typing overrides (#10).
- [x] Character-creation **dot allocation** on the unified **0–4** sheet (#20): attributes
  *and* the Big-Five traits are now 0–4; starting **vice** field (#14) threaded service-side.
- [x] Character sheet surfaces **condition** (stress / trauma / vices, `format_condition`),
  re-read on open so the session's accrued harm/stress shows.
- [ ] **Remaining:** wire the **resistance turn** into the graph + `GameScreen` re-entry (needs
  live TUI state), the **vice-path** router/matcher, and the **harm-location** step that sets
  `harm_part` (open design node, §8) — until it ships, `apply_turn_effects` simply skips harm.
- [ ] Surface intent-type routing in the UI.

### Cross-cutting unknowns (settle as we reach them)
- **Per-run state home** — `stress` / `trauma` / `vices` as CHARACTER properties, wound-box
  counts as PART properties: needs ArcadeDB schema + repo/service additions.
- **Cross-turn carry** — the TUI rebuilds `GraphState` each turn, so the deferred tail and
  resistance offer live on `GameScreen`, not in graph state (the #6/#10 design already assumes
  this; survey confirms it).
- **Reducer/fan-out concurrency** — the Phase-2 fan-out is the first place concurrent writes
  hit `GraphState`; get disjoint keys / reducers right here.
- **Model routing / DSPy optimization** — a parallel track that can lag the spine entirely.