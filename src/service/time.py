from __future__ import annotations

from database.repository.time import TimeRepository
from arcadedb_embedded.graph import Vertex


class TimeService:
    """Encapsulate the world clock as a domain operation.

    Storage is a scalar on the WORLD vertex (owned by WorldRepository); this
    service owns *behaviour* — reading "now" and advancing time. Time is
    world-global, so it lives here rather than on CharacterService; the
    coordinator composes the two when a turn closes.
    """

    def __init__(self, time: TimeRepository) -> None:
        self._time = time

    def get_elapsed_ticks(self) -> int:
        """Return the current world time, in ticks (1 tick = 6 seconds)."""
        time_vertex: Vertex | None = self._time.get_time_vertex()
        current_ticks: int = time_vertex.get(name="elapsed_ticks")
        return current_ticks

    def advance_elapsed_ticks(self, delta_ticks: int) -> int:
        """Advance the world clock by `delta_ticks` and return the new elapsed ticks.

        A non-positive delta is a no-op.
        """
        time_vertex: Vertex = self._time.advance_elapsed_ticks(delta_ticks)
        return time_vertex.get(name="elapsed_ticks")

    def get_current_world_time(self) -> datetime:
        """Return the current world time as a datetime object."""
        elapsed_ticks: int = self.get_elapsed_ticks()
        return datetime.fromtimestamp(elapsed_ticks * 6)
