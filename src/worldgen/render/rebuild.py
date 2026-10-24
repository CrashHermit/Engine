"""Full-world rebuild orchestration independent of the window toolkit."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from time import perf_counter

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.model import GeneratedWorld


@dataclass(frozen=True, slots=True)
class RebuildTiming:
    generation_seconds: float
    display_seconds: float
    total_seconds: float


class WorldRebuilder:
    """Generate and replace a world while measuring generation and display work."""

    def __init__(
        self,
        config: WorldgenConfig,
        replace_world: Callable[[GeneratedWorld], None],
    ) -> None:
        self.config = config
        self.replace_world = replace_world
        self.last_timing: RebuildTiming | None = None

    def rebuild(self, plate_count: int) -> RebuildTiming:
        config = replace(
            self.config,
            geology=replace(
                self.config.geology,
                plates=replace(self.config.geology.plates, plate_count=plate_count),
            ),
        )
        started = perf_counter()
        world = generate_world(config)
        generated = perf_counter()
        self.replace_world(world)
        displayed = perf_counter()
        self.config = config
        self.last_timing = RebuildTiming(
            generated - started, displayed - generated, displayed - started
        )
        return self.last_timing
