"""Tests for $bucketAuto aggregation stage — 'groupBy' expression types and null/missing."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BUCKET_AUTO_GROUPBY_NOT_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [GroupBy Expression Types]: 'groupBy' accepts a $-prefixed field
# path, a dotted nested path, an expression operator, or a $literal constant.
BUCKET_AUTO_GROUPBY_EXPR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "groupBy_field_path",
        docs=[
            {"_id": 1, "x": 5},
            {"_id": 2, "x": 15},
            {"_id": 3, "x": 25},
            {"_id": 4, "x": 35},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": 5, "max": 25}, "count": 2},
            {"_id": {"min": 25, "max": 35}, "count": 2},
        ],
        msg="$bucketAuto should group by a $-prefixed field path",
    ),
    StageTestCase(
        "groupBy_dotted_path",
        docs=[
            {"_id": 1, "a": {"b": 5}},
            {"_id": 2, "a": {"b": 15}},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$a.b", "buckets": 2}}],
        expected=[
            {"_id": {"min": 5, "max": 15}, "count": 1},
            {"_id": {"min": 15, "max": 15}, "count": 1},
        ],
        msg="$bucketAuto should group by a dotted nested field path",
    ),
    StageTestCase(
        "groupBy_expression_operator",
        docs=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 3, "b": 4},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": {"$add": ["$a", "$b"]}, "buckets": 2}}],
        expected=[
            {"_id": {"min": 3, "max": 7}, "count": 1},
            {"_id": {"min": 7, "max": 7}, "count": 1},
        ],
        msg="$bucketAuto should group by an expression operator over fields",
    ),
    StageTestCase(
        "groupBy_literal_constant",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[{"$bucketAuto": {"groupBy": {"$literal": "c"}, "buckets": 2}}],
        expected=[{"_id": {"min": "c", "max": "c"}, "count": 2}],
        msg="$bucketAuto with a $literal constant groupBy should produce a single bucket",
    ),
]

# Property [Null and Missing Grouping]: documents whose groupBy resolves to
# null or a missing field are grouped together into a null-valued bucket.
BUCKET_AUTO_GROUPBY_NULL_TESTS: list[StageTestCase] = [
    StageTestCase(
        "groupBy_null_and_missing_grouped",
        docs=[
            {"_id": 1, "x": None},
            {"_id": 2},
            {"_id": 3, "x": 5},
            {"_id": 4, "x": 10},
        ],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
        expected=[
            {"_id": {"min": None, "max": 5}, "count": 2},
            {"_id": {"min": 5, "max": 10}, "count": 2},
        ],
        msg="$bucketAuto should group null and missing groupBy values together",
    ),
    StageTestCase(
        "groupBy_all_missing",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$bucketAuto": {"groupBy": "$nope", "buckets": 2}}],
        expected=[{"_id": {"min": None, "max": None}, "count": 3}],
        msg="$bucketAuto should place all documents with a missing groupBy field in one bucket",
    ),
]

# Property [GroupBy Expression Rejection]: a non-$-prefixed constant string is
# rejected because groupBy must be a $-prefixed path or an expression.
BUCKET_AUTO_GROUPBY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "groupBy_non_dollar_string",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[{"$bucketAuto": {"groupBy": "literalval", "buckets": 2}}],
        error_code=BUCKET_AUTO_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucketAuto should reject a non-$-prefixed string groupBy",
    ),
]

BUCKET_AUTO_GROUPBY_TESTS = (
    BUCKET_AUTO_GROUPBY_EXPR_TESTS
    + BUCKET_AUTO_GROUPBY_NULL_TESTS
    + BUCKET_AUTO_GROUPBY_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_GROUPBY_TESTS))
def test_bucketAuto_groupby(collection, test_case: StageTestCase):
    """Test $bucketAuto 'groupBy' expression types and null/missing handling."""
    populate_collection(collection, test_case)
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
