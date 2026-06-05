# Graph Flow Review & State Model Migration

Audit of the turn pipeline (intent → frame → threat → effect → resolve ⇄ resist)
for flow bugs, plus migration of the graph state off Pydantic. Anchored on a
reported symptom: a vague `'str' object has no attribute …` error during chat.

## Findings & fixes

### 1. Broken imports crash the session (definite bug) — FIXED
`src/session/coordinator.py` imported `from core.model.character import
CharacterData` and `from service.container import ServiceContainer` (missing the
`src.` prefix) — leftover duplicates of the correct imports below them. Since the
app runs as the `src` package, importing the coordinator raised
`ModuleNotFoundError`, so **no game session could start** and the whole test
suite failed to collect. Removed the two bad lines.

### 2. State model migrated to TypedDict + dataclasses — DONE
The graph state was a Pydantic `BaseModel` (`GraphState`) wrapping dataclass
`EntityData`, copied through `Send` via `model_copy` and round-tripped through
the checkpoint serializer on every interrupt resume. That mixed-type setup is the
most likely source of the `'str'`/coercion error on the resume path. Migrated to
the native LangGraph shape:

- `GraphState` → `TypedDict(total=False)`. Channels are read with `state.get(...)`
  (an unwritten channel is simply absent — `total=False` reflects that). The two
  `*_history` lists and `pending_threats` stay `Annotated[list, operator.add]`
  reducers.
- The four derived views (`action_intent`, `pool_for`, `landed_threats`,
  `current_threat`) became module-level **free functions** in `src/state.py`
  (a TypedDict carries no behavior).
- `Message`, `HeldScaffold`, `FinalScaffold` → `@dataclass` (Pydantic removed
  from our model layer; it remains only as a transitive dependency).
- `Send` payloads are now plain dict copies (`{**state, ...}` / `dict(state)`) —
  the native channel payload. This **removes** the old `model_copy` hazard the
  `routers.py` docstrings warned about (those comments were updated/inverted).
- `LoggedNode` logs `dict(state)` instead of `state.model_dump()`.

### Verification
- Full suite green (`115 passed`); tests asserting the old Pydantic Send contract
  were updated to the dict contract.
- `GraphState` with `Message`/`EntityData`/`Threat`/`HeldScaffold` round-trips
  through the real `JsonPlusSerializer` checkpoint serde with every object
  surviving as its proper type (not a bare `str`/`dict`).
- The compiled main graph runs a full mundane turn end-to-end, and a clarification
  **interrupt + resume** completes through the real SQLite checkpointer — the
  exact chat path — with no `str` error.

## Open items (flagged, not changed)

- **DSPy signature kwarg mismatch.** `alignment_router`, `question_generator`,
  and `synthesizer` pass `character_name=` / `location_name=` to `aforward(...)`,
  but neither field is declared on their `Signature`s. Harmless if DSPy ignores
  unknown inputs; worth either declaring the fields or dropping the kwargs. Left
  untouched because it touches prompt inputs (out of scope for this pass).
- The original `'str'` traceback was never captured verbatim, so the fix above is
  the most-probable cause (the Pydantic-state + `Send`/checkpoint coercion path),
  now demonstrably eliminated. If it recurs, capture the exact traceback line.
