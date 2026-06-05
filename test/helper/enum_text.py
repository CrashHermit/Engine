"""Enum description helpers."""

from __future__ import annotations

from src.core.helper.enum_text import describe, labeled
from src.core.model.biome import BIOME, Biome
from src.core.model.weather import WIND_SPEED, WindSpeed


def test_describe() -> None:
    assert describe(WindSpeed.BREEZY, WIND_SPEED) == WIND_SPEED[WindSpeed.BREEZY]


def test_labeled() -> None:
    assert labeled(Biome.TAIGA, BIOME) == f"taiga — {BIOME[Biome.TAIGA]}"
