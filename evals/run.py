"""Run the framing-classifier eval sets and report accuracy (Phase 2).

This is the "metric before optimising" harness. It runs each classifier node
over its seed set (`evals/datasets.py`) and reports exact-match accuracy — a
baseline to improve against with DSPy optimisers later.

Requires a live LM (LM_API_KEY in the environment); with no key it can't call
the model. Run:  `python -m evals.run`
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from evals import datasets
from src.nodes.framing import (
    AttributeSelectorNode,
    EffectClassifierNode,
    ThreatChannelClassifierNode,
    ThreatMagnitudeClassifierNode,
    ThreatTypeClassifierNode,
)
from src.state import GraphState


@dataclass(frozen=True)
class EvalSpec:
    name: str
    node_factory: type
    cases: list
    output_key: str  # the GraphState key the node writes


# One spec per framing classifier. `output_key` is what the node returns and what
# we compare to the expected label (exact match).
SPECS = [
    EvalSpec("attribute", AttributeSelectorNode, datasets.ATTRIBUTE_CASES, "attribute"),
    EvalSpec("effect", EffectClassifierNode, datasets.EFFECT_CASES, "effect"),
    EvalSpec("threat_type", ThreatTypeClassifierNode, datasets.THREAT_TYPE_CASES, "threat_type"),
    EvalSpec("threat_magnitude", ThreatMagnitudeClassifierNode, datasets.THREAT_MAGNITUDE_CASES, "base_magnitude"),
    EvalSpec("threat_channel", ThreatChannelClassifierNode, datasets.THREAT_CHANNEL_CASES, "threat_channel"),
]


def exact_match(predicted, expected) -> bool:
    """Shared metric: string-insensitive exact match on the label."""
    return str(predicted) == str(expected)


async def _evaluate(spec: EvalSpec, node=None) -> tuple[int, int]:
    node = node if node is not None else spec.node_factory()
    correct = 0
    for inputs, expected in spec.cases:
        state = GraphState(contested_beat=inputs.get("contested_beat", ""))
        # Map dataset inputs onto state fields the node reads.
        for field in ("character_description", "location_description"):
            if field in inputs:
                setattr(state, field, inputs[field])
        if inputs.get("entities_at_location"):
            state.entities_at_location = [inputs["entities_at_location"]]
        out = await node(state)
        if exact_match(out[spec.output_key], expected):
            correct += 1
    return correct, len(spec.cases)


async def main() -> None:
    print("Framing classifier baselines (exact match):")
    for spec in SPECS:
        correct, total = await _evaluate(spec)
        print(f"  {spec.name:18s} {correct}/{total}  ({correct / total:.0%})")


if __name__ == "__main__":
    asyncio.run(main())
