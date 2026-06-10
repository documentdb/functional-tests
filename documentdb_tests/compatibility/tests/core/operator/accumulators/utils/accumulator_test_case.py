"""Shared test case and helpers for accumulator tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AccumulatorTestCase(BaseTestCase):
    """Test case for accumulator tests."""

    docs: list[dict] | None = None
    pipeline: list[dict[str, Any]] = field(default_factory=list)


def sort_array_project(
    *fields: str,
    include_id: bool = False,
) -> dict[str, Any]:
    """Build a $project stage that sorts one or more array fields via $sortArray.

    Args:
        *fields: Field names to sort (e.g. ``"result"``, ``"all_tags"``).
        include_id: If ``False`` (default), ``_id`` is suppressed with ``0``.
            If ``True``, ``_id`` is included with ``1``.

    Returns:
        A ``{"$project": {...}}`` stage dict.
    """
    proj: dict[str, Any] = {"_id": 1 if include_id else 0}
    for f in fields:
        proj[f] = {"$sortArray": {"input": f"${f}", "sortBy": 1}}
    return {"$project": proj}
