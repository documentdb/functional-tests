"""Tests for $centerSphere query interaction — combined with other operators."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="combined_with_field_predicate",
        filter={
            "loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}},
            "status": "active",
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "inactive"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
        ],
        msg="Should filter by both $centerSphere and non-geospatial predicate",
    ),
    QueryTestCase(
        id="with_and_combining_two_geo",
        filter={
            "$and": [
                {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 500 / 6371]}}},
                {"loc": {"$geoWithin": {"$centerSphere": [[5, 0], 500 / 6371]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [2.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [2.5, 0]}}],
        msg="Should support $and combining two $centerSphere queries (intersection)",
    ),
]


def _run_test(collection, test, extra_cmd=None):
    """Helper to run a query test with optional extra command fields."""
    cmd = {"find": collection.name, "filter": test.filter}
    if extra_cmd:
        cmd.update(extra_cmd)
    return execute_command(collection, cmd)


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_centerSphere_query_interaction(collection, test):
    """Verifies $centerSphere works with other query operators and $and."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


def test_centerSphere_with_projection(collection):
    """Verifies $centerSphere works with field projection."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "name": "B"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
            "projection": {"name": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "name": "A"}], msg="Should work with projection")


def test_centerSphere_with_limit(collection):
    """Verifies $centerSphere respects limit parameter."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
            "limit": 1,
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should return exactly 1 document with limit=1",
    )


def test_centerSphere_with_skip(collection):
    """Verifies $centerSphere respects skip parameter."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
            "skip": 1,
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}}],
        msg="Should return remaining results after skipping 1",
    )
