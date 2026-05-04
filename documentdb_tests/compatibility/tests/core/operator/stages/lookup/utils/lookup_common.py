"""Shared infrastructure for $lookup stage tests."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)

FOREIGN = object()


@dataclass(frozen=True)
class LookupTestCase(StageTestCase):
    """Test case for $lookup stage tests with a foreign collection."""

    foreign_docs: list[dict[str, Any]] | None = None


@contextmanager
def setup_lookup(
    collection: Any,
    test_case: LookupTestCase,
) -> Generator[str, None, None]:
    """Set up local and foreign collections for a $lookup test.

    Yields the foreign collection name and drops it on exit.
    """
    foreign_name = f"{collection.name}_foreign"
    db = collection.database

    # Set up local collection
    if test_case.docs is not None:
        db.create_collection(collection.name)
        if test_case.docs:
            collection.insert_many(test_case.docs)

    # Set up foreign collection
    if test_case.foreign_docs is not None:
        db.create_collection(foreign_name)
        if test_case.foreign_docs:
            db[foreign_name].insert_many(test_case.foreign_docs)

    try:
        yield foreign_name
    finally:
        db.drop_collection(foreign_name)


def _substitute_foreign(
    pipeline: list[dict[str, Any]],
    foreign_name: str,
) -> list[dict[str, Any]]:
    """Replace FOREIGN sentinel in $lookup 'from' fields, including nested pipelines."""
    result = list(pipeline)
    for i, stage in enumerate(result):
        if not isinstance(stage, dict) or "$lookup" not in stage:
            continue
        spec = stage["$lookup"]
        if not isinstance(spec, dict):
            continue
        changed = False
        spec = dict(spec)
        if spec.get("from") is FOREIGN:
            spec["from"] = foreign_name
            changed = True
        if isinstance(spec.get("pipeline"), list):
            spec["pipeline"] = _substitute_foreign(spec["pipeline"], foreign_name)
            changed = True
        if changed:
            result[i] = {"$lookup": spec}
    return result


def build_lookup_pipeline(
    test_case: LookupTestCase,
    foreign_name: str,
) -> list[dict[str, Any]]:
    """Build the $lookup pipeline, substituting the foreign collection name."""
    pipeline = test_case.pipeline
    assert pipeline, "test case pipeline must not be empty"
    return _substitute_foreign(pipeline, foreign_name)


def build_lookup_command(
    collection: Any,
    test_case: LookupTestCase,
    foreign_name: str,
) -> dict[str, Any]:
    """Build the aggregate command for a $lookup test case."""
    return {
        "aggregate": collection.name,
        "pipeline": build_lookup_pipeline(test_case, foreign_name),
        "cursor": {},
    }
