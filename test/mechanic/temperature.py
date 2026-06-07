"""Shared temperature enum."""

from __future__ import annotations

from core.model.temperature import Temperature


def test_temperature_has_seven_ordinal_bands() -> None:
    assert len(Temperature) == 7
    assert [member.value for member in Temperature] == list(range(7))
