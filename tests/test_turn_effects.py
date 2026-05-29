from dataclasses import dataclass

from src.core.model.character import CharacterData
from src.core.model.part import Status
from src.tui.formatting import format_condition
from src.tui.turn_effects import apply_turn_effects, next_turn_carry


# --- fakes for the service layer (decision #21 boundary) ------------------

@dataclass
class _HarmResult:
    part_name: str
    filled: int
    status: Status
    destroyed: bool
    overflow: int
    severed_parts: list


class _FakeHarm:
    def __init__(self):
        self.calls = []

    def apply_harm(self, character_id, part_name, magnitude):
        self.calls.append((character_id, part_name, magnitude))
        return _HarmResult(part_name, magnitude, Status.COMPROMISED, False, 0, [])


@dataclass
class _StressResult:
    stress: int
    trauma: int
    trauma_gained: bool
    lost: bool


class _FakeEconomy:
    def __init__(self):
        self.calls = []

    def add_stress(self, character_id, amount):
        self.calls.append((character_id, amount))
        return _StressResult(stress=amount, trauma=0, trauma_gained=False, lost=False)


class _FakeServices:
    def __init__(self):
        self.harm = _FakeHarm()
        self.economy = _FakeEconomy()


# --- harm application -----------------------------------------------------

def test_landed_harm_is_applied_to_the_part():
    services = _FakeServices()
    result = {
        "threat_type": "harm",
        "harm_part": "left_hand",
        "landed_magnitude": 2,
        "outcome_avoided": False,
    }
    notes = apply_turn_effects(result, services, "c1")
    assert services.harm.calls == [("c1", "left_hand", 2)]
    assert any("left_hand" in n for n in notes)


def test_avoided_harm_is_not_applied():
    services = _FakeServices()
    result = {"threat_type": "harm", "harm_part": "head", "landed_magnitude": 3, "outcome_avoided": True}
    apply_turn_effects(result, services, "c1")
    assert services.harm.calls == []


def test_harm_without_part_is_not_applied():
    # harm-location selection is still an open design node; no part -> no write.
    services = _FakeServices()
    result = {"threat_type": "harm", "landed_magnitude": 3, "outcome_avoided": False}
    apply_turn_effects(result, services, "c1")
    assert services.harm.calls == []


def test_nonharm_threat_does_not_apply_harm():
    services = _FakeServices()
    result = {"threat_type": "complication", "harm_part": "head", "landed_magnitude": 3, "outcome_avoided": False}
    apply_turn_effects(result, services, "c1")
    assert services.harm.calls == []


# --- stress application ---------------------------------------------------

def test_stress_delta_is_applied():
    services = _FakeServices()
    notes = apply_turn_effects({"stress_delta": 2}, services, "c1")
    assert services.economy.calls == [("c1", 2)]
    assert any("stress" in n for n in notes)


def test_zero_stress_delta_is_skipped():
    services = _FakeServices()
    apply_turn_effects({"stress_delta": 0}, services, "c1")
    assert services.economy.calls == []


def test_missing_part_is_reported_not_raised():
    class _Raises:
        def apply_harm(self, *a):
            raise ValueError("Part not found on character: tail")

    class _S:
        harm = _Raises()
        economy = None

    notes = apply_turn_effects(
        {"threat_type": "harm", "harm_part": "tail", "landed_magnitude": 2, "outcome_avoided": False},
        _S(), "c1",
    )
    assert any("not applied" in n for n in notes)


# --- cross-turn carry (#10, #6) -------------------------------------------

def test_deferred_tail_becomes_pending_intent():
    carry = next_turn_carry({"deferred_tail": "grab the crown", "landed_magnitude": 0})
    assert carry.pending_intent == "grab the crown"


def test_empty_tail_yields_no_hint():
    carry = next_turn_carry({"deferred_tail": "   ", "landed_magnitude": 0})
    assert carry.pending_intent == ""


def test_significant_consequence_is_offered_for_resistance():
    carry = next_turn_carry({"landed_magnitude": 3, "threat_type": "harm", "outcome_avoided": False})
    assert carry.resistance_consequence is not None


def test_minor_consequence_is_not_offered():
    carry = next_turn_carry({"landed_magnitude": 1, "outcome_avoided": False})
    assert carry.resistance_consequence is None


def test_avoided_consequence_is_not_offered():
    carry = next_turn_carry({"landed_magnitude": 4, "outcome_avoided": True})
    assert carry.resistance_consequence is None


# --- sheet condition line -------------------------------------------------

def _char(**kw) -> CharacterData:
    base = dict(
        id="c1", name="N", description="", corpus=2, mens=1, anima=1,
        extraversion=2, openness=2, agreeableness=2, neuroticism=2, conscientiousness=2,
    )
    base.update(kw)
    return CharacterData(**base)


def test_condition_line_shows_economy():
    line = format_condition(_char(stress=4, trauma=1, vices=["wine", "grudges"]))
    assert "Stress: 4 / 9" in line
    assert "Trauma: 1 / 4" in line
    assert "wine, grudges" in line


def test_condition_line_handles_no_vices():
    assert "Vices: —" in format_condition(_char())
