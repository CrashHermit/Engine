# Code Style & Conventions

> **Status:** Living document. Architectural game-design decisions live in
> [`bitd_integration-design.md`](bitd_integration-design.md); this doc covers
> how we structure and write code day to day.

---

## 1. Principles

1. **Pure mechanics, narrow LLM steps.** Balance-critical math lives in
   `src/core/mechanic/` as deterministic functions. Each LLM judgment is one
   small DSPy signature wrapped by one thin node.
2. **Single write path.** The TUI (or Textual-free helpers it calls) persists
   changes via services → repositories. Graph nodes never touch the database.
3. **Input control over prompt trust.** When behavior must be guaranteed (e.g.
   anti-chaining), constrain what the narrator receives in `GraphState` rather
   than asking the model to self-limit.
4. **Tunables in code.** Magic numbers enter as module constants or defaulted
   parameters so playtest tuning never blocks implementation.
5. **Minimize scope.** Match surrounding conventions; do not refactor unrelated
   code in the same change.

---

## 2. Layer boundaries

```
TUI / integration  →  services  →  repositories  →  ArcadeDB
Graph nodes        →  GraphState + DSPy only
core/mechanic      →  pure functions (no I/O, DB, LLM)
```

| Layer | Location | May import | Must not import |
|-------|----------|------------|-----------------|
| Display | `src/tui/` | `session.*`, `service.*`, `state`, `core/model` | `database.repository.*` |
| Coordination | `src/session/` | `service.*`, `state`, `core/model` | `textual`, `tui/*`, `database.repository.*` |
| Graph | `src/graph/`, `src/node/` | `state`, `core/mechanic`, `core/model`, `lm` | `service/*`, `database/*`, `tui/*` |
| LLM steps | `src/node/{frame,intent,threat,resolve,resist,effect}/` | DSPy `Signature` + `{Name}Node` co-located | services, database |
| Services | `src/service/` | `database.repository.*`, `core/model`, `core/mechanic` | `tui/*`, `node/*` |
| Persistence | `src/database/` | `core/model`, ArcadeDB | TUI, graph nodes |
| Mechanics | `src/core/mechanic/` | other mechanic modules, `core/model` | everything else |

### Side effects at the integration boundary (decision #21)

Graph nodes read `GraphState` and return **partial state updates** — including
*intended* effects such as `stress_delta`, `landed_magnitude`, or `harm_part`.
They do **not** receive a `ServiceContainer` and do **not** call services or
repositories.

After `graph_service.ainvoke` / `resume`, the coordination layer applies those
effects via services (`src/session/coordinator.py`, the `GameCoordinator`). The
coordinator is Textual-free, owns turn orchestration and all graph-shape
translation, and exposes a typed async event stream to the TUI — so the TUI only
displays. This keeps nodes unit-testable offline, keeps the coordinator
unit-testable without Textual, and gives services a single transactional write
path. (Effect persistence itself is not yet wired — see decision #21.)

---

## 3. Directory layout & naming

```
src/
  core/
    model/       # DTOs, enums, domain vocabulary
    mechanic/    # pure game rules (dice, harm, economy, …)
  node/          # LLM steps: Signature + Node co-located by phase
    frame/       # roll gate, segmenter, approach, pillar, target, …
    intent/      # alignment router, question generator, synthesizer
    threat/      # classify, gather, dice_scale, ambush
    resolve/     # narrator, planners, turn_close
    resist/      # offer, push_parser, roll
    effect/      # apply_effect
  graph/         # LangGraph builders and routing functions
  service/       # use-case orchestration, vertex → DTO mapping
  database/      # connection, schema, repositories
  session/       # turn coordination — the Textual-free integration boundary
  tui/           # Textual screens, modals, widgets
  worldgen/      # procedural world pipeline
  state.py       # GraphState
  lm.py          # single configured DSPy LM
tests/           # mirrors src/ where practical
```

| Kind | Pattern | Example |
|------|---------|---------|
| LLM contract | `{Name}Signature` | `RollGateSignature` |
| Graph step | `{Name}Node` | `RollGateNode` |
| Graph assembly | `{Name}GraphBuilder` | `MainGraphBuilder` |
| Use case | `{Entity}Service` | `CharacterService` |
| DB access | `{Entity}Repository` | `CharacterRepository` |
| Plain data | `{Entity}Data` | `CharacterData` |
| Domain enum | `StrEnum` / `IntEnum` | `Status`, `VertexType` |
| Session wiring | `{Name}Factory`, `{Name}Container` | `WorldSessionFactory` |
| Module constant | `UPPER_SNAKE` | `DEFAULT_STRESS_MAX` |
| Private module data | `_UPPER_SNAKE` | `_ATTRIBUTES` |
| Private member | leading `_` | `self._program` |

LangGraph node names use **snake_case** strings that match the node class stem
(e.g. `"roll_gate"` → `RollGateNode`).

---

## 4. Python language & typing

- **Target:** Python ≥ 3.13 (`pyproject.toml`).
- **Annotations** on all public functions and methods.
- Modern syntax: `str | None`, `list[str]`, `dict[str, Any]`.
- **Keyword arguments** when the call site would otherwise be ambiguous
  (`type_name=`, `character_id=`, `zero_pool=`).
- Graph nodes return **`dict`** partial updates keyed to `GraphState` fields.
- Append-only graph fields use **`Annotated[..., operator.add]`** reducers.

### Data model choice by layer

| Layer | Type |
|-------|------|
| Graph state | `TypedDict` (`GraphState`); LangGraph channels, read via `.get(...)`. Derived views are free functions (`action_intent`, `pool_for`, `landed_threats`, `current_threat`). |
| Service DTOs | `@dataclass` (mutable snapshots for display/persistence) |
| Mechanic configs & results | `@dataclass(frozen=True)` |
| Models carried in graph state | `@dataclass` (`Message`, `HeldScaffold`, `FinalScaffold`) — no Pydantic |
| DB enums exposed to schema/LLM | `StrEnum` / `IntEnum` in `core/model/` |

### Imports

Always use the **`src.`** prefix:

```python
from src.core.mechanic.dice import RollTier
from src.service.container import ServiceContainer
```

Import order: stdlib → third-party → `src.*`.

Do **not** use bare `from core...` or `from service...` paths.

---

## 5. Mechanics core (`src/core/mechanic/`)

Mechanics encode locked design decisions as **pure, deterministic code**. See
[`bitd_integration-design.md`](bitd_integration-design.md) §3 and §5 for the rules
they implement.

### Rules

- **No I/O** — no database, network, filesystem, LLM, or Textual.
- **State transitions return new values.** Use `@dataclass(frozen=True)` for
  configs and results. Callers pass primitives or frozen snapshots in; functions
  return updated snapshots out.
- **Randomness is injected.** Pass an optional `random.Random` to roll
  functions; expose fixed-dice helpers for tests (see `dice.result_from_dice`).
- **Validate inputs** with `ValueError` and an explicit message.
- **Reference design decisions** in module docstrings when behavior is
  non-obvious.
- **Code owns balance-critical math**; LLMs own classification and fiction only.

### Immutable update pattern

Prefer module-level functions over mutating methods:

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class WoundPool:
    filled: int = 0
    capacity: int = 4

@dataclass(frozen=True)
class WoundApplyResult:
    pool: WoundPool
    overflow: int

def apply_wounds(pool: WoundPool, magnitude: int) -> WoundApplyResult:
    total = pool.filled + magnitude
    return WoundApplyResult(
        pool=replace(pool, filled=min(pool.capacity, total)),
        overflow=max(0, total - pool.capacity),
    )
```

Same pattern elsewhere: `add_stress(...) → StressResult`, `scale_threat(...) → Outcome`.

### Default arguments

Do not call constructors in parameter defaults. Use a module-level
singleton instead:

```python
DEFAULT_ECONOMY_CONFIG = EconomyConfig()

def add_stress(..., config: EconomyConfig = DEFAULT_ECONOMY_CONFIG) -> StressResult:
    ...
```

---

## 6. LLM module pattern (1 signature + 1 node)

Every LLM step follows the same shape.

**Signature + Node** (co-located in `src/node/<phase>/`) — prompt + typed I/O in
the `Signature`; the `Node` wires it to `GraphState` and assigns shared `lm`:

```python
# src/node/frame/roll_gate.py
class RollGateSignature(Signature):
    """You are a roll gate…"""

    human_message: str = InputField(description="The player's intended action")
    needs_roll: bool = OutputField(description="Whether the beat needs a dice roll")


class RollGateNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=RollGateSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction = await self._program.aforward(
            human_message=state.get("human_message").content,
            ...
        )
        return {"needs_roll": prediction.needs_roll}
```

### Rules

- **One narrow judgment per signature** when possible (design #18).
- Signatures hold prompts and field descriptions; nodes hold state shaping only.
- Nodes are **async**; use `aforward` even when wrapping sync DSPy.
- Shared LM lives in `src/lm.py`; nodes assign `self._program.lm = lm`.
- No DB, no services, no side effects inside nodes.

---

## 7. Services & repositories

### Repositories (`src/database/repository/`)

- Compose or extend **`BaseRepository`**.
- Speak in **vertices, edges, Cypher** — not domain DTOs.
- Wrap writes in **`with self._base.transaction():`**.
- Rely on base helpers for `id`, `created_at`, `updated_at`.
- Prefer **soft invalidation** (`invalidated_at`) over hard delete where applicable.

### Services (`src/services/`)

- **Orchestrate** multi-step graph writes inside one transaction.
- **Map** vertices → DTOs via `_to_data(...)`.
- **Fail fast** via `_require(...)` → `ValueError` when an entity is missing.
- Larger services may use section dividers (`# Reads`, `# Writes`, `# Internals`).

### Special cases

- **`WorldService`** — bootstrap only; constructs its own repos (not via
  `ServiceContainer`).
- **`GraphService`** — owns the compiled graph and checkpointer thread config;
  no database access.
- **`ServiceContainer`** — built per open world; handed to TUI screens only.

---

## 8. Graph & turn lifecycle

- Graphs are built by `{Name}GraphBuilder.build()` → `CompiledStateGraph`.
- Subgraphs compile **without their own checkpointer**; they inherit the parent's.
- Routing functions are **plain module-level functions**
  (e.g. `route_by_intent_alignment_router`).
- **`GraphState` is rebuilt each turn** from session data. Cross-turn carry
  (`message_history`, `_run_id`, `pending_intent`, resistance offer) lives on the
  `GameCoordinator` (`src/session/`), not in graph state and not on the screen.
- Paused subgraphs use LangGraph **`interrupt()`**; resume via
  `Command(resume=...)`.

Concurrent fan-out nodes must write **disjoint** `GraphState` keys or use
reducers — never overwrite each other's fields in parallel.

---

## 9. TUI conventions (Textual)

- **Screens** = full views; **Modals** = `ModalScreen[T]` overlays;
  **Widgets** = reusable pieces under `src/tui/widgets/`.
- The game screen builds a **`GameCoordinator`** (`src/session/`) in its
  constructor and holds only that; other screens inject **`ServiceContainer`**
  and store it as `self._services`.
- Widget IDs are **kebab-case** strings (`"msg-input"`, `"left-panel"`).
- Use **`@work`** to drive the coordinator's async turn stream off the UI thread
  (`async for event in coordinator.submit(...)`).
- Turn coordination lives outside Textual in `src/session/coordinator.py` — the
  `GameCoordinator` has no Textual imports and is unit-tested with a faked
  `GraphService`. The TUI maps each `TurnEvent` to a styled write.
- Escape untrusted content before writing to Rich logs (`escape(...)`).

---

## 10. Comments & documentation

**Comment when:**

- Explaining architectural role (why a class exists).
- Documenting non-obvious graph behavior (interrupt/resume, checkpointer inheritance).
- Referencing a locked design decision in mechanic modules.
- Marking provisional code.

**Do not comment:**

- Obvious mapping, getters, or one-line wiring.

**Markers:**

- `# PROTOTYPE` — provisional schema or worldgen paths not yet generalized.
- `# TODO:` — known deferred work (use sparingly).

Class docstrings may use backticks and `` `Command(resume=...)` `` when behavior
is subtle (see `IntentClarificationNode`).

Game-mechanics design decisions belong in **`bitd_integration-design.md`**, not
duplicated here — cross-reference by decision number instead.

---

## 11. Aesthetics

Style (§§1–10) is *what* the code does and how it's organized; aesthetics is how
it **looks on the page**. The mechanical layer is enforced by Ruff (§14); the
taste-driven choices below are not fully tool-checkable and are upheld by
convention.

### Enforced by Ruff (mechanical)

- **Line length 88.** Drives all wrapping; the dominant factor in code silhouette.
- **Double quotes**, sorted imports (stdlib → third-party → `src`), modern syntax
  (`str | None`, `list[str]`), no unused imports, trailing commas where the
  formatter adds them.
- Run `ruff format` + `ruff check` — see §14.

### Vertical rhythm

- Short functions stay **tight** — no blank lines inside the body.
- In longer functions, a **single** blank line separates logical phases
  (validate → compute → return; build → persist → map). **Never more than one**
  blank line inside a body.
- Module level keeps the formatter's two-blank-line spacing between top-level
  defs and one between methods.

### Section dividers

Use a **plain single-line** comment, one blank line above, for in-file sections:

```python
    # Reads

    def list_characters(self) -> list[CharacterData]:
        ...

    # Writes
```

Do **not** use full-width `####…` hash bars — they shout and don't scale to small
files.

### Docstring voice

- **Imperative mood**, ending in a period: `"Own a single play session."`,
  `"Read the contested beat → which attribute it rolls."`, `"Return the value of
  the first interrupt, if any."` — not `"Owns…"`, `"Reads…"`, or a bare noun
  phrase. Enforced for detectable cases by Ruff's `D401`.
- Multi-line docstrings put **one blank line** between the summary and the body
  (`D205`).
- Docstrings are **not required** everywhere (`D1xx` is disabled) — write them
  where §10 says to, and when present they follow the shape above.

---

## 12. Error handling

- **`ValueError`** for invalid inputs and missing entities in domain code.
- No broad `except Exception` in services or mechanics.
- TUI surfaces user-facing errors via `self.app.notify(..., severity="error")`.
- Repositories assume valid vertex references; services validate IDs before mutating.

---

## 13. Testing

- **Framework:** pytest (dev dependency).
- **Layout:** `tests/` mirrors `src/` (e.g. `tests/core/mechanic/test_dice.py`).
- **`core/mechanic/`** — table-driven unit tests; pure functions make exhaustive
  coverage cheap.
- **Nodes** — testable with stubbed DSPy output; no DB or live LLM required.
- **Coordination** (`src/session/coordinator.py`) — Textual-free; fake `GraphService`
  (patch its async methods) and assert the yielded `TurnEvent`s + `run_id` rotation.
- **Layer boundaries** — optional AST test ensuring `nodes/` and `graph/` never
  import `services` or `database`.

Run the suite before merging mechanic or service changes:

```powershell
uv run pytest
```

---

## 14. Tooling

Configured in `pyproject.toml` (`[tool.ruff]`). Dev dependencies install with:

```powershell
uv sync --group dev
```

| Task | Command |
|------|---------|
| Format | `uv run ruff format src test` |
| Lint | `uv run ruff check src test` |
| Lint + autofix | `uv run ruff check --fix src test` |
| Test | `uv run pytest` |

CI runs `ruff format --check` and `ruff check` on every push/PR; nothing
non-conforming merges. A Claude Code SessionStart hook formats web/agent sessions
so branches arrive conforming.

Conventions at a glance:

- Line length: **88**
- Quote style: **double**
- First-party package: **`src`**
- Target: **Python 3.13**
- Lint families: `E, W, F, I, UP, Q, COM, TID, N, D` (docstrings imperative;
  `D1xx` off — see §11)

The big-bang reformat commit is recorded in `.git-blame-ignore-revs`; configure
git once with `git config blame.ignoreRevsFile .git-blame-ignore-revs` so it
doesn't pollute `git blame`.

---

## 15. Related documents

| Document | Scope |
|----------|-------|
| [`bitd_integration-design.md`](bitd_integration-design.md) | Game mechanics, graph topology, locked decisions |
| `pyproject.toml` | Dependencies |
| `src/services/container.py` | Session service wiring and layer-boundary note |
