import logging

from src.database.repository.world import WorldRepository


class TimeService:
    """The world clock as a domain operation. Storage is a scalar on the WORLD
    vertex (owned by WorldRepository); this service owns *behaviour* — reading
    "now" and advancing time. Time is world-global, so it lives here rather than
    on CharacterService; the coordinator composes the two when a turn closes."""

    def __init__(self, worlds: WorldRepository) -> None:
        self._logger = logging.getLogger("engine.service.time")
        self._worlds = worlds

    def now(self) -> int:
        """Current world time, in ticks (1 tick = 6 seconds)."""
        return self._worlds.get_elapsed_ticks()

    def advance(self, delta_ticks: int) -> int:
        """Advance the world clock by `delta_ticks` and return the new total.
        A non-positive delta is a no-op."""
        total = self._worlds.advance_elapsed_ticks(delta_ticks)
        self._logger.debug("advance delta=%s now=%s", delta_ticks, total)
        return total
