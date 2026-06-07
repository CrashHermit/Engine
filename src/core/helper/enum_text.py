from __future__ import annotations

from enum import Enum


def describe[E: Enum](member: E, descriptions: dict[E, str]) -> str:
    return descriptions[member]


def labeled[E: Enum](member: E, descriptions: dict[E, str]) -> str:
    return f"{member.name.lower()} — {descriptions[member]}"
