"""Tests for $match query operator categories."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Query Operator Categories]: one representative per query operator
# category functions correctly inside $match as a container.
MATCH_QUERY_OPERATOR_TESTS: list[StageTestCase] = [
    # Comparison operators.
    StageTestCase(
        "query_comparison_gt",
        docs=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 10},
        ],
        pipeline=[{"$match": {"a": {"$gt": 5}}}],
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        msg="$match should support comparison query operators",
    ),
    # Logical operators.
    StageTestCase(
        "query_logical_or",
        docs=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 2, "b": 20},
            {"_id": 3, "a": 3, "b": 30},
        ],
        pipeline=[{"$match": {"$or": [{"a": 1}, {"b": 30}]}}],
        expected=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 3, "a": 3, "b": 30},
        ],
        msg="$match should support logical query operators",
    ),
    # Element operators.
    StageTestCase(
        "query_element_exists",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "b": 20}, {"_id": 3, "a": 30}],
        pipeline=[{"$match": {"a": {"$exists": True}}}],
        expected=[{"_id": 1, "a": 10}, {"_id": 3, "a": 30}],
        msg="$match should support element query operators",
    ),
    # Evaluation operators.
    StageTestCase(
        "query_eval_expr",
        docs=[
            {"_id": 1, "a": 10, "b": 10},
            {"_id": 2, "a": 20, "b": 30},
            {"_id": 3, "a": 5, "b": 5},
        ],
        pipeline=[{"$match": {"$expr": {"$eq": ["$a", "$b"]}}}],
        expected=[
            {"_id": 1, "a": 10, "b": 10},
            {"_id": 3, "a": 5, "b": 5},
        ],
        msg="$match should support evaluation query operators",
    ),
    # Array operators.
    StageTestCase(
        "query_array_elemmatch",
        docs=[
            {"_id": 1, "arr": [0.5, 0.8, 0.95]},
            {"_id": 2, "arr": [0.1, 0.3]},
            {"_id": 3, "arr": [0.9, 1.0]},
        ],
        pipeline=[{"$match": {"arr": {"$elemMatch": {"$gte": 0.9}}}}],
        expected=[
            {"_id": 1, "arr": [0.5, 0.8, 0.95]},
            {"_id": 3, "arr": [0.9, 1.0]},
        ],
        msg="$match should support array query operators",
    ),
    # Bitwise operators.
    StageTestCase(
        "query_bitwise_bitsallset",
        docs=[
            {"_id": 1, "flags": 7},
            {"_id": 2, "flags": 3},
            {"_id": 3, "flags": 15},
        ],
        # Bitmask 5 (binary 0101): flags 7 (0111) and 15 (1111) match.
        pipeline=[{"$match": {"flags": {"$bitsAllSet": 5}}}],
        expected=[{"_id": 1, "flags": 7}, {"_id": 3, "flags": 15}],
        msg="$match should support bitwise query operators",
    ),
    # Geospatial operators.
    StageTestCase(
        "query_geo_geowithin",
        docs=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
            {"_id": 3, "loc": [1, 1]},
        ],
        pipeline=[{"$match": {"loc": {"$geoWithin": {"$center": [[0, 0], 10]}}}}],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 3, "loc": [1, 1]}],
        msg="$match should support geospatial query operators",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MATCH_QUERY_OPERATOR_TESTS))
def test_match_query_operator_cases(collection, test_case: StageTestCase):
    """Test $match query operator categories."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
