"""Tests for collation effects on the $geoNear aggregation stage query filter."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [GeoNear Query Filter with Collation]: the $geoNear stage's query
# filter uses command-level collation for string comparisons, enabling
# case-insensitive and accent-insensitive filtering of geospatial results.
COLLATION_GEONEAR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "geonear_query_case_insensitive",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "cat": "Apple"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "cat": "apple"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "cat": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                        "query": {"cat": "apple"},
                    }
                },
                {"$project": {"_id": 1, "cat": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "cat": "Apple"},
            {"_id": 2, "cat": "apple"},
        ],
        msg="$geoNear query filter should use collation for case-insensitive matching",
    ),
    CommandTestCase(
        "geonear_query_no_collation_binary",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "cat": "Apple"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "cat": "apple"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "cat": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                        "query": {"cat": "apple"},
                    }
                },
                {"$project": {"_id": 1, "cat": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 2, "cat": "apple"}],
        msg="$geoNear query filter without collation should use binary comparison",
    ),
    CommandTestCase(
        "geonear_query_comparison_operator_collation",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "cat": "Apple"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "cat": "banana"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "cat": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                        "query": {"cat": {"$gt": "apple"}},
                    }
                },
                {"$project": {"_id": 1, "cat": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "cat": "banana"},
            {"_id": 3, "cat": "cherry"},
        ],
        msg="$geoNear query $gt should use collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_GEONEAR_TESTS))
def test_collation_aggregate_geonear(database_client, collection, test):
    """Test collation affects $geoNear query filter."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
