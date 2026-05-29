from contextlib import contextmanager

from src.core.mechanics.economy import EconomyConfig
from src.services.economy import EconomyService


class _FakeBase:
    @contextmanager
    def transaction(self):
        yield


class _FakeCharVertex:
    """Stands in for the CHARACTER vertex's stored economy properties."""

    def __init__(self, stress=0, trauma=0, vices=None):
        self.stress = stress
        self.trauma = trauma
        self.vices = list(vices or [])


class _FakeCharRepo:
    def __init__(self, vertex):
        self._vertex = vertex

    def get_character(self, character_id):
        return self._vertex if character_id == "c1" else None

    def get_stress(self, v):
        return v.stress

    def get_trauma(self, v):
        return v.trauma

    def get_vices(self, v):
        return list(v.vices)

    def set_economy(self, v, *, stress, trauma, vices):
        v.stress, v.trauma, v.vices = stress, trauma, list(vices)


def _service(vertex, config=EconomyConfig()):
    return EconomyService(_FakeBase(), _FakeCharRepo(vertex), config), vertex


def test_add_stress_persists_below_track():
    svc, v = _service(_FakeCharVertex(stress=3))
    result = svc.add_stress("c1", 2)
    assert result.stress == 5 and result.trauma_gained is False
    assert v.stress == 5 and v.trauma == 0


def test_overflow_grants_trauma_and_coping_vice():
    svc, v = _service(_FakeCharVertex(stress=8, trauma=0, vices=["drink"]))
    result = svc.add_stress("c1", 2)  # 10 > 9
    assert result.trauma_gained is True and result.trauma == 1
    assert v.stress == 0 and v.trauma == 1
    assert len(v.vices) == 2  # a coping vice was added (decision #14)


def test_reaching_trauma_cap_is_lost():
    svc, v = _service(_FakeCharVertex(stress=9, trauma=3))
    result = svc.add_stress("c1", 1)
    assert result.lost is True and v.trauma == 4


def test_clear_stress_via_vice():
    svc, v = _service(_FakeCharVertex(stress=5))
    result = svc.clear_stress("c1", vice_roll=4)
    assert result.cleared == 4 and v.stress == 1 and result.overindulged is False


def test_clear_stress_overindulge():
    svc, v = _service(_FakeCharVertex(stress=2))
    result = svc.clear_stress("c1", vice_roll=5)
    assert v.stress == 0 and result.overindulged is True


def test_add_vice():
    svc, v = _service(_FakeCharVertex(vices=["gambling"]))
    svc.add_vice("c1", "obsession")
    assert v.vices == ["gambling", "obsession"]


def test_unknown_character_raises():
    svc, _ = _service(_FakeCharVertex())
    try:
        svc.add_stress("nope", 1)
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown character")
