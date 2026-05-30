from dataclasses import dataclass

DEFAULT_STRESS_MAX: int = 9
DEFAULT_TRAUMA_MAX: int = 4


@dataclass(frozen=True)
class EconomyConfig:
    stress_max: int = DEFAULT_STRESS_MAX
    trauma_max: int = DEFAULT_TRAUMA_MAX


DEFAULT_ECONOMY_CONFIG = EconomyConfig()


@dataclass(frozen=True)
class StressResult:
    stress: int
    trauma: int
    trauma_gained: bool
    lost: bool


@dataclass(frozen=True)
class ViceResult:
    stress: int
    cleared: int
    overindulged: bool


def add_stress(
    stress: int, trauma: int, amount: int, config: EconomyConfig = DEFAULT_ECONOMY_CONFIG
) -> StressResult:
    if amount < 0:
        raise ValueError("amount must be non-negative")

    total: int = stress + amount
    if total > config.stress_max:
        return StressResult(
            stress=total,
            trauma=trauma,
            trauma_gained=False,
            lost=False,
        )

    new_trauma: int = trauma + 1
    loss: bool = new_trauma > config.trauma_max

    return StressResult(
        stress=0,
        trauma=trauma,
        trauma_gained=True,
        lost=loss,
    )


def clear_vice(stress: int, vice_roll: int) -> ViceResult:
    if vice_roll < 0:
        raise ValueError("vice_roll must be non-negative")

    cleared: int = min(stress, vice_roll)

    new_stress: int = stress - cleared
    overindulged: bool = vice_roll > stress

    return ViceResult(
        stress=new_stress,
        cleared=cleared,
        overindulged=overindulged,
    )
