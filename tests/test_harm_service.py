from contextlib import contextmanager

from src.core.model.part import Status
from src.services.harm import HarmService


class _FakeBase:
    @contextmanager
    def transaction(self):
        yield


class _FakePart:
    def __init__(self, name, attached=None, boxes=0, capacity=4):
        self.name = name
        self.attached = attached or []      # distal parts
        self.boxes = boxes
        self.capacity = capacity
        self.status = Status.NORMAL.value
        self.removed = False


class _FakeCharRepo:
    def get_character(self, character_id):
        return object() if character_id == "c1" else None


class _FakePartRepo:
    def __init__(self, parts):
        self._parts = {p.name: p for p in parts}

    def list_parts(self, _character):
        return [p for p in self._parts.values() if not p.removed]

    def get_part(self, _character, name):
        p = self._parts.get(name)
        return p if p and not p.removed else None

    def attached_parts(self, part):
        return [self._parts[n] for n in part.attached if not self._parts[n].removed]

    def get_wound_boxes(self, part):
        return part.boxes

    def get_capacity(self, part, default):
        return part.capacity or default

    def set_wound_state(self, part, *, filled, status):
        part.boxes, part.status = filled, status

    def remove_part(self, part):
        part.removed = True


def _service(parts):
    return HarmService(_FakeBase(), _FakePartRepo(parts), _FakeCharRepo())


def test_apply_harm_fills_boxes_and_derives_status():
    parts = [_FakePart("left_hand")]
    svc = _service(parts)
    result = svc.apply_harm("c1", "left_hand", 2)  # Standard
    assert result.filled == 2
    assert result.status is Status.COMPROMISED
    assert result.destroyed is False
    assert parts[0].boxes == 2 and parts[0].status == Status.COMPROMISED.value


def test_harm_accumulates_across_calls():
    parts = [_FakePart("left_hand")]
    svc = _service(parts)
    svc.apply_harm("c1", "left_hand", 1)  # GRAZED
    result = svc.apply_harm("c1", "left_hand", 1)  # accumulates -> COMPROMISED
    assert result.filled == 2 and result.status is Status.COMPROMISED


def test_destroyed_part_severs_whole_limb_distal():
    # thigh -> shin -> foot; destroying the thigh removes all three.
    parts = [
        _FakePart("left_thigh", attached=["left_shin"]),
        _FakePart("left_shin", attached=["left_foot"]),
        _FakePart("left_foot"),
        _FakePart("right_thigh", attached=["right_shin"]),
        _FakePart("right_shin"),
    ]
    svc = _service(parts)
    result = svc.apply_harm("c1", "left_thigh", 4)  # Fatal -> DESTROYED
    assert result.destroyed is True
    assert set(result.severed_parts) == {"left_thigh", "left_shin", "left_foot"}
    by_name = {p.name: p for p in parts}
    assert by_name["left_thigh"].removed and by_name["left_foot"].removed
    assert not by_name["right_thigh"].removed  # unrelated limb untouched


def test_overflow_reported_for_death_signal():
    parts = [_FakePart("head", boxes=3)]  # one box from cap
    svc = _service(parts)
    result = svc.apply_harm("c1", "head", 4)  # would be 7 -> cap 4, overflow 3
    assert result.destroyed is True
    assert result.overflow == 3  # caller decides death on a vital part (#13)


def test_unknown_part_raises():
    svc = _service([_FakePart("head")])
    try:
        svc.apply_harm("c1", "tail", 1)
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown part")
