from __future__ import annotations

from arcadedb_embedded.graph import Vertex

from src.core.model.time import WorldDateTime
from src.database.repository.time import TimeRepository


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

    def update_elapsed_ticks(self, elapsed_ticks: int) -> int:
        """
        Update the elapsed ticks to the given value.
        """
        time_vertex: Vertex = self._time.update_elapsed_ticks(elapsed_ticks)
        return time_vertex.get(name="elapsed_ticks")

    def create_time_vertex(self, elapsed_ticks: int) -> Vertex:
        """
        Create a new time vertex.
        """
        return self._time.create_time_vertex(elapsed_ticks)

    def get_current_world_time(self) -> WorldDateTime:
        """Return the current world time as a WorldDateTime object."""
        elapsed_ticks: int = self.get_elapsed_ticks()
        seconds: int = elapsed_ticks * 6
        minutes: int = seconds // 60
        hours: int = minutes // 60
        days: int = hours // 24
        weeks: int = days // 7
        months: int = weeks // 4
        years: int = months // 12

        return WorldDateTime(
            year=years,
            month=months,
            day=days,
            hour=hours,
            minute=minutes,
            second=seconds,
        )
