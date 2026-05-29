import asyncio

from evals import datasets
from evals.run import SPECS, exact_match
from src.core.model.resolution import Attribute, Effect, ThreatType


def test_exact_match_metric():
    assert exact_match("corpus", Attribute.CORPUS) is True
    assert exact_match(2, 2) is True
    assert exact_match("corpus", Attribute.MENS) is False


def test_every_spec_has_cases_with_valid_labels():
    # Each classifier has a non-empty seed set, and every expected label is in the
    # classifier's actual vocabulary (so a baseline run can't silently mis-score).
    label_space = {
        "attribute": {a.value for a in Attribute},
        "effect": {e.value for e in Effect},
        "threat_type": {t.value for t in ThreatType},
        "threat_channel": {a.value for a in Attribute},
        "threat_magnitude": {1, 2, 3, 4},
    }
    for spec in SPECS:
        assert spec.cases, f"{spec.name} has no eval cases"
        valid = label_space[spec.name]
        for _inputs, expected in spec.cases:
            key = str(expected) if spec.name != "threat_magnitude" else int(expected)
            assert key in valid or expected in valid, f"{spec.name}: bad label {expected!r}"


def test_dataset_inputs_carry_a_contested_beat():
    all_sets = [
        datasets.ATTRIBUTE_CASES,
        datasets.EFFECT_CASES,
        datasets.THREAT_TYPE_CASES,
        datasets.THREAT_MAGNITUDE_CASES,
        datasets.THREAT_CHANNEL_CASES,
    ]
    for case_set in all_sets:
        for inputs, _expected in case_set:
            assert inputs.get("contested_beat", "").strip(), "every case needs a contested_beat"


class _FakeProgram:
    def __init__(self, **fields):
        self._fields = fields

    async def aforward(self, **_kwargs):
        return type("Prediction", (), self._fields)()


def test_runner_scores_a_perfect_classifier():
    # With a node that always returns the first case's expected label, the runner
    # should score exactly the cases that share that label — proving the harness
    # plumbs inputs -> node -> metric correctly, offline.
    from evals.run import _evaluate

    spec = SPECS[0]  # attribute
    node = spec.node_factory()
    first_expected = spec.cases[0][1]
    node._program = _FakeProgram(attribute=str(first_expected))
    correct, total = asyncio.run(_evaluate(spec, node=node))
    expected_correct = sum(1 for _i, e in spec.cases if str(e) == str(first_expected))
    assert total == len(spec.cases)
    assert correct == expected_correct
