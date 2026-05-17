"""Visible display-key grouping for Claude Code entrypoints."""

from __future__ import annotations

from dataclasses import dataclass

from claude_translator.core.models import Record


@dataclass(frozen=True)
class DisplayKey:
    kind: str
    name: str


@dataclass(frozen=True)
class DuplicateGroup:
    display_key: DisplayKey
    records: tuple[Record, ...]


def _name_from_canonical_id(canonical_id: str) -> str:
    return canonical_id.split(":", 1)[1] if ":" in canonical_id else canonical_id


def display_key_for_record(record: Record) -> DisplayKey:
    return DisplayKey(kind=record.kind, name=_name_from_canonical_id(record.canonical_id))


def group_by_display_key(records: tuple[Record, ...]) -> dict[DisplayKey, tuple[Record, ...]]:
    groups: dict[DisplayKey, tuple[Record, ...]] = {}
    for record in records:
        key = display_key_for_record(record)
        groups[key] = (*groups.get(key, ()), record)
    return groups


def find_duplicate_display_groups(records: tuple[Record, ...]) -> tuple[DuplicateGroup, ...]:
    return tuple(
        DuplicateGroup(display_key=key, records=group)
        for key, group in group_by_display_key(records).items()
        if len(group) > 1
    )
