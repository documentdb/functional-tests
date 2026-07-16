"""Shared test case and helpers for window operator tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class WindowTestCase(BaseTestCase):
    """Test case for window operator tests."""

    docs: list[dict] | None = None
    window: dict[str, Any] | None = None
    sort_by: dict[str, Any] = field(default_factory=lambda: {"_id": 1})
    partition_by: str = "$partition"
    extra_stages: list[dict[str, Any]] | None = None


BASIC_DOCS: list[dict[str, Any]] = [
    {"_id": 1, "partition": "A", "value": 10},
    {"_id": 2, "partition": "A", "value": 20},
    {"_id": 3, "partition": "A", "value": 30},
    {"_id": 4, "partition": "A", "value": 40},
    {"_id": 5, "partition": "A", "value": 50},
]


def run_window_operator(
    collection,
    operator: str,
    docs: list[dict],
    window: dict[str, Any],
    sort_by: dict[str, Any] | None = None,
    partition_by: str = "$partition",
    extra_stages: list[dict[str, Any]] | None = None,
) -> Any:
    """Build and execute a $setWindowFields pipeline.

    Args:
        collection: The collection to operate on.
        operator: The window operator string (e.g. "$stdDevPop").
        docs: Documents to insert into the collection.
        window: The window specification (e.g. {"documents": ["unbounded", "current"]}).
        sort_by: The sortBy specification. Defaults to {"_id": 1}.
        partition_by: The partitionBy expression. Defaults to "$partition".
        extra_stages: Additional pipeline stages to append after $setWindowFields.

    Returns:
        The result from execute_command (result dict or Exception).
    """
    if sort_by is None:
        sort_by = {"_id": 1}

    collection.insert_many(docs)

    pipeline: list[dict[str, Any]] = [
        {
            "$setWindowFields": {
                "partitionBy": partition_by,
                "sortBy": sort_by,
                "output": {
                    "result": {
                        operator: "$value",
                        "window": window,
                    }
                },
            }
        },
    ]

    if extra_stages:
        pipeline.extend(extra_stages)

    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        },
    )
