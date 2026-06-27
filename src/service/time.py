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
        if time_vertex is None:
            raise ValueError("Time vertex not found.")
        current_ticks: int = time_vertex.get(name="elapsed_ticks")
        return current_ticks

    def update_elapsed_ticks(self, delta_elapsed_ticks: int) -> Vertex:
        time_vertex: Vertex = self._time.get_time_vertex()
        if time_vertex is None:
            raise ValueError("Time vertex not found.")
        current_elapsed_ticks: int = time_vertex.get(name="elapsed_ticks")
        new_elapsed_ticks: int = current_elapsed_ticks + delta_elapsed_ticks
        if new_elapsed_ticks < 0:
            raise ValueError("World clock can't be negative.")
        updated_time_vertex: Vertex = self._time.update_vertex(
            vertex=time_vertex, elapsed_ticks=new_elapsed_ticks
        )
        return updated_time_vertex

    def create_time_vertex(self, elapsed_ticks: int) -> None:
        """Create a new time vertex."""
        time_vertex: Vertex = self._time.create_time_vertex(elapsed_ticks)
        return None

    def get_current_world_time(self) -> WorldDateTime:
        """Return the current world time as a WorldDateTime object."""
        elapsed_ticks: int = self.get_elapsed_ticks()
        seconds: int = elapsed_ticks * 6

        second: int = seconds % 60
        minute: int = (seconds // 60) % 60
        hour: int = (seconds // 3600) % 24
        day: int = (seconds // 86400) % 7
        week: int = (seconds // 604800) % 4
        month: int = (seconds // 2419200) % 12
        year: int = seconds // 29030400

        return WorldDateTime(
            year=year,
            month=month,
            week=week,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
        )
