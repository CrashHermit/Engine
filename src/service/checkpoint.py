from pathlib import Path
from collections.abc import AsyncIterator
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.core.model.entity import Danger, EntityKind, EntityStatus, ThreatPillar
from src.core.mechanic.dice import RollResult, RollTier
from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.scaling import Outcome, Position
from src.core.model.message import Message
from src.core.model.location import EntityData
from src.core.model.resist import FinalScaffold, HeldScaffold, ResistAction
from src.core.model.threat import Channel, Threat, ThreatType

# Custom types that ride inside GraphState and so get persisted in the
# checkpoint. LangGraph's msgpack serializer warns (and a future version will
# *block*) on deserializing types outside its safe set unless they are
# explicitly allowlisted. Since resume-after-interrupt — the entire resist
# turn — round-trips these through the checkpoint, register them up front so an
# upgrade can't silently break the flow. Keep this in sync with GraphState.
_ALLOWED_CHECKPOINT_TYPES: tuple[type, ...] = (
    Message,
    Channel,
    ThreatType,
    Magnitude,
    Position,
    Outcome,
    RollResult,
    RollTier,
    HeldScaffold,
    FinalScaffold,
    ResistAction,
    EntityData,
    Danger,
    EntityKind,
    EntityStatus,
    ThreatPillar,
    Threat,
)


class CheckpointService:
    def __init__(self, db_path: str | Path = "data/checkpointers.sqlite") -> None:
        self._db_path: Path = Path(db_path)
        self._cm: AsyncIterator[AsyncSqliteSaver] | None = None
        self.saver: BaseCheckpointSaver | None = None

    async def start(self) -> BaseCheckpointSaver:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._cm = AsyncSqliteSaver.from_conn_string(str(self._db_path))
        self.saver = await self._cm.__aenter__()
        # from_conn_string gives no hook for serde, so swap in one that
        # allowlists our state types (see _ALLOWED_CHECKPOINT_TYPES).
        self.saver.serde = JsonPlusSerializer(
            allowed_msgpack_modules=_ALLOWED_CHECKPOINT_TYPES
        )
        return self.saver

    async def stop(self) -> None:
        if self._cm is not None:
            await self._cm.__aexit__(None, None, None)
        self._cm = None
        self.saver = None
