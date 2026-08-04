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
    window: dict[str, Any] | None = None,
    sort_by: dict[str, Any] | None = None,
    partition_by: str | None = "$partition",
    extra_stages: list[dict[str, Any]] | None = None,
    expression: str | dict = "$value",
) -> Any:
    """Build and execute a $setWindowFields pipeline.

    Args:
        collection: The collection to operate on.
        operator: The window operator string (e.g. "$stdDevPop").
        docs: Documents to insert into the collection.
        window: The window specification (e.g. {"documents": ["unbounded", "current"]}).
            Omitted from the output field when None, as frameless operators require.
        sort_by: The sortBy specification. Defaults to {"_id": 1}.
        partition_by: The partitionBy expression. Defaults to "$partition". Omitted
            from the stage when None, making the whole collection one partition.
        extra_stages: Additional pipeline stages to append after $setWindowFields.
        expression: The operator expression. Defaults to "$value".

    The assembled stage, with every argument at its default, looks like:

        {"$setWindowFields": {
            "partitionBy": "$partition",
            "sortBy": {"_id": 1},
            "output": {"result": {"$stdDevPop": "$value",
                                  "window": {"documents": ["unbounded", "current"]}}},
        }}

    A frameless operator (window=None, partition_by=None) collapses to:

        {"$setWindowFields": {
            "sortBy": {"_id": 1},
            "output": {"result": {"$documentNumber": {}}},
        }}

    Returns:
        The result from execute_command (result dict or Exception).
    """
    if sort_by is None:
        sort_by = {"_id": 1}

    if docs:
        collection.insert_many(docs)

    output_spec: dict[str, Any] = {operator: expression}
    if window is not None:
        output_spec["window"] = window

    stage: dict[str, Any] = {}
    if partition_by is not None:
        stage["partitionBy"] = partition_by
    stage["sortBy"] = sort_by
    stage["output"] = {"result": output_spec}

    pipeline: list[dict[str, Any]] = [{"$setWindowFields": stage}]

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
