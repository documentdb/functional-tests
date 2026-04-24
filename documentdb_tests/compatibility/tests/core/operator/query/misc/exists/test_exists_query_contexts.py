"""
Tests for $exists in find query contexts and algebraic properties.

Covers find filter, cursor operations (sort, limit, projection),
complementarity, idempotency, and contradiction.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

DOCS: list[dict] = [
    {"_id": 1, "a": 10},
    {"_id": 2, "a": 5},
    {"_id": 3, "b": 1},
]

ALGEBRAIC_DOCS: list[dict] = [
    {"_id": 1, "a": 1},
    {"_id": 2, "a": None},
    {"_id": 3, "b": 1},
    {"_id": 4},
]


@dataclass(frozen=True)
class FindTestCase(BaseTestCase):
    """Test case for find with optional sort/limit/projection."""

    filter: Any = None
    doc: Any = None
    sort: Optional[dict] = None
    limit: Optional[int] = None
    projection: Optional[dict] = None


FIND_TESTS: list[FindTestCase] = [
    FindTestCase(
        id="find_with_sort",
        filter={"a": {"$exists": True}},
        doc=DOCS,
        sort={"a": 1},
        expected=[{"_id": 2, "a": 5}, {"_id": 1, "a": 10}],
        msg="$exists: true with sort",
    ),
    FindTestCase(
        id="find_with_limit",
        filter={"a": {"$exists": True}},
        doc=DOCS,
        sort={"_id": 1},
        limit=1,
        expected=[{"_id": 1, "a": 10}],
        msg="$exists: true with limit",
    ),
    FindTestCase(
        id="find_with_projection",
        filter={"a": {"$exists": True}},
        doc=DOCS,
        projection={"a": 1, "_id": 0},
        expected=[{"a": 10}, {"a": 5}],
        msg="$exists: true with projection",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_TESTS))
def test_exists_query_contexts(collection, test):
    """Parametrized test for $exists in find query contexts."""
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter}
    if test.sort:
        cmd["sort"] = test.sort
    if test.limit:
        cmd["limit"] = test.limit
    if test.projection:
        cmd["projection"] = test.projection
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, ignore_doc_order=test.sort is None)


ALGEBRAIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="partition_true",
        filter={"a": {"$exists": True}},
        doc=ALGEBRAIC_DOCS,
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": None}],
        msg="$exists: true returns docs with field (partition half)",
    ),
    QueryTestCase(
        id="partition_false",
        filter={"a": {"$exists": False}},
        doc=ALGEBRAIC_DOCS,
        expected=[{"_id": 3, "b": 1}, {"_id": 4}],
        msg="$exists: false returns docs without field (partition half)",
    ),
    QueryTestCase(
        id="no_overlap",
        filter={"$and": [{"a": {"$exists": True}}, {"a": {"$exists": False}}]},
        doc=ALGEBRAIC_DOCS,
        expected=[],
        msg="$exists: true AND false is empty (no overlap)",
    ),
    QueryTestCase(
        id="idempotency_true",
        filter={"$and": [{"a": {"$exists": True}}, {"a": {"$exists": True}}]},
        doc=ALGEBRAIC_DOCS,
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": None}],
        msg="Duplicate $exists: true is same as single",
    ),
    QueryTestCase(
        id="idempotency_false",
        filter={"$and": [{"a": {"$exists": False}}, {"a": {"$exists": False}}]},
        doc=ALGEBRAIC_DOCS,
        expected=[{"_id": 3, "b": 1}, {"_id": 4}],
        msg="Duplicate $exists: false is same as single",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALGEBRAIC_TESTS))
def test_exists_algebraic_properties(collection, test):
    """Parametrized test for $exists algebraic properties."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
