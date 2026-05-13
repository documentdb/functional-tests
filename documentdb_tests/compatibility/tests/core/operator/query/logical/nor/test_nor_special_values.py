"""
Tests for $nor query operator with special values and edge cases.

Covers NaN, Infinity, -Infinity, negative zero, Decimal128 special values,
empty collections, non-existent fields, and deeply nested field paths.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SPECIAL_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_excluded_by_nan_match",
        filter={"$nor": [{"val": float("nan")}]},
        doc=[{"_id": 1, "val": float("nan")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$nor with NaN should exclude docs with NaN value",
    ),
    QueryTestCase(
        id="infinity_excluded_by_gt",
        filter={"$nor": [{"val": {"$gt": 1000000}}]},
        doc=[{"_id": 1, "val": float("inf")}, {"_id": 2, "val": 100}],
        expected=[{"_id": 2, "val": 100}],
        msg="$nor with $gt should exclude Infinity (Infinity > any number)",
    ),
    QueryTestCase(
        id="negative_infinity_excluded_by_lt",
        filter={"$nor": [{"val": {"$lt": -1000000}}]},
        doc=[{"_id": 1, "val": float("-inf")}, {"_id": 2, "val": -100}],
        expected=[{"_id": 2, "val": -100}],
        msg="$nor with $lt should exclude -Infinity (-Infinity < any number)",
    ),
    QueryTestCase(
        id="negative_zero",
        filter={"$nor": [{"val": 0}]},
        doc=[{"_id": 1, "val": -0.0}, {"_id": 2, "val": 1}],
        expected=[{"_id": 2, "val": 1}],
        msg="$nor with 0 should exclude docs with -0.0 (negative zero equals zero)",
    ),
    QueryTestCase(
        id="nan_included_when_filtering_numbers",
        filter={"$nor": [{"val": 5}, {"val": 10}]},
        doc=[
            {"_id": 1, "val": float("nan")},
            {"_id": 2, "val": 5},
            {"_id": 3, "val": 10},
            {"_id": 4, "val": 20},
        ],
        expected=[
            {"_id": 1, "val": pytest.approx(float("nan"), nan_ok=True)},
            {"_id": 4, "val": 20},
        ],
        msg="$nor filtering numeric values should include NaN doc (NaN != any number)",
    ),
    QueryTestCase(
        id="decimal128_nan",
        filter={"$nor": [{"val": Decimal128("NaN")}]},
        doc=[{"_id": 1, "val": Decimal128("NaN")}, {"_id": 2, "val": Decimal128("5")}],
        expected=[{"_id": 2, "val": Decimal128("5")}],
        msg="$nor with Decimal128 NaN should exclude matching docs",
    ),
    QueryTestCase(
        id="decimal128_infinity",
        filter={"$nor": [{"val": Decimal128("Infinity")}]},
        doc=[{"_id": 1, "val": Decimal128("Infinity")}, {"_id": 2, "val": Decimal128("5")}],
        expected=[{"_id": 2, "val": Decimal128("5")}],
        msg="$nor with Decimal128 Infinity should exclude matching docs",
    ),
]

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_collection",
        filter={"$nor": [{"a": 1}]},
        doc=[],
        expected=[],
        msg="$nor on empty collection should return empty result",
    ),
    QueryTestCase(
        id="all_non_existent_fields",
        filter={"$nor": [{"x": 1}, {"y": 2}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "b": 2}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "b": 2}],
        msg="$nor with all non-existent fields should return all documents",
    ),
    QueryTestCase(
        id="deeply_nested_field_path",
        filter={"$nor": [{"a.b.c.d": 1}]},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": 1}}}},
            {"_id": 2, "a": {"b": {"c": {"d": 2}}}},
        ],
        expected=[{"_id": 2, "a": {"b": {"c": {"d": 2}}}}],
        msg="$nor with deeply nested field path should work correctly",
    ),
    QueryTestCase(
        id="missing_dot_path",
        filter={"$nor": [{"x.y.z": 1}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        msg="$nor with non-existent dot path should return all docs (none match)",
    ),
    QueryTestCase(
        id="empty_string_field_name",
        filter={"$nor": [{"": 1}]},
        doc=[{"_id": 1, "": 1, "a": 2}, {"_id": 2, "": 2, "a": 1}],
        expected=[{"_id": 2, "": 2, "a": 1}],
        msg="$nor with empty string field name should match docs where '' field equals value",
    ),
    QueryTestCase(
        id="large_number_of_expressions",
        filter={"$nor": [{"a": i} for i in range(50)]},
        doc=[{"_id": 1, "a": 99}, {"_id": 2, "a": 5}],
        expected=[{"_id": 1, "a": 99}],
        msg="$nor with 50 expressions should work without error",
    ),
]

ALL_TESTS = SPECIAL_VALUE_TESTS + EDGE_CASE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_special_values(collection, test):
    """Test $nor query operator with special values and edge cases."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
