from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

E = TypeVar("E", bound=StrEnum)


def describe(member: E, descriptions: dict[E, str]) -> str:
    return descriptions[member]


def labeled(member: E, descriptions: dict[E, str]) -> str:
    return f"{member.value} — {descriptions[member]}"
