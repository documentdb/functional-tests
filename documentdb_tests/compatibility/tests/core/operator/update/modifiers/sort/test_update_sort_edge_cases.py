"""Tests for $sort update modifier edge case and behavioral behavior.

Covers: missing/empty/single-element arrays, sort stability, null/missing
field handling, NaN/Infinity positioning, BSON type distinction
(false ≠ 0, true ≠ 1), mixed BSON type ordering, date sorting, and
behavioral cases that succeed ($sort without $each pushes a literal,
sort by a containing array field path leaves order unchanged).
"""

import math
from datetime import datetime, timezone

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

CORE_EDGE_CASE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="target_field_missing",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3, 1, 2], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$sort on missing field should create sorted array",
    ),
    UpdateTestCase(
        id="empty_array_sort",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": []}],
        msg="$sort on empty array with empty $each should remain empty",
    ),
    UpdateTestCase(
        id="single_element_sort",
        setup_docs=[{"_id": 1, "arr": [5]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [5]}],
        msg="$sort on single element array should not change it",
    ),
    UpdateTestCase(
        id="stability_equal_scores",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"a": 1, "score": 5},
                    {"a": 2, "score": 5},
                    {"a": 3, "score": 5},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"score": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"a": 1, "score": 5},
                    {"a": 2, "score": 5},
                    {"a": 3, "score": 5},
                ],
            }
        ],
        msg="$sort should be stable — equal elements preserve original order",
    ),
]

NULL_MISSING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="null_elements_sort_first",
        setup_docs=[{"_id": 1, "arr": [3, None, 1, None, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [None, None, 1, 2, 3]}],
        msg="Null values should sort before numbers per BSON order",
    ),
    UpdateTestCase(
        id="missing_field_sorts_first",
        setup_docs=[
            {
                "_id": 1,
                "arr": [{"field": 3}, {"name": "no field"}, {"field": 1}],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"field": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [{"name": "no field"}, {"field": 1}, {"field": 3}],
            }
        ],
        msg="Documents with missing sort field should sort first (treated as null)",
    ),
]

NAN_INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="nan_sorts_before_numbers",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_NAN, 2, -1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [pytest.approx(math.nan, nan_ok=True), -1, 1, 2]}],
        msg="NaN should sort before all finite numbers",
    ),
    UpdateTestCase(
        id="infinity_sort_order",
        setup_docs=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY]}],
        msg="-Infinity < finite numbers < Infinity",
    ),
    UpdateTestCase(
        id="nan_infinity_combined",
        setup_docs=[
            {
                "_id": 1,
                "arr": [1, FLOAT_NAN, FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY, 0],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    pytest.approx(math.nan, nan_ok=True),
                    FLOAT_NEGATIVE_INFINITY,
                    0,
                    1,
                    FLOAT_INFINITY,
                ],
            }
        ],
        msg="NaN < -Infinity < finite numbers < Infinity",
    ),
    UpdateTestCase(
        id="nan_descending",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_NAN, FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": -1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    FLOAT_INFINITY,
                    1,
                    FLOAT_NEGATIVE_INFINITY,
                    pytest.approx(math.nan, nan_ok=True),
                ],
            }
        ],
        msg="Descending: Infinity > finite > -Infinity > NaN",
    ),
    UpdateTestCase(
        id="decimal128_nan_groups_with_float_nan",
        setup_docs=[{"_id": 1, "arr": [DECIMAL128_NAN, 1, FLOAT_NAN, Decimal128("2")]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    DECIMAL128_NAN,
                    pytest.approx(math.nan, nan_ok=True),
                    1,
                    Decimal128("2"),
                ],
            }
        ],
        msg="Decimal128 NaN and float NaN should group together before numbers",
    ),
]

BSON_TYPE_DISTINCTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="bool_distinct_from_numbers",
        setup_docs=[{"_id": 1, "arr": [False, 0, True, 1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [0, 1, False, True]}],
        msg="Numbers should sort before booleans per BSON type order",
    ),
    UpdateTestCase(
        id="distinct_types_document_sort",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"field": None},
                    {"field": 0},
                    {"field": False},
                    {"field": ""},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"field": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"field": None},
                    {"field": 0},
                    {"field": ""},
                    {"field": False},
                ],
            }
        ],
        msg="Distinct BSON types should sort by BSON type order: null < number < string < bool",
    ),
]

MIXED_BSON_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="mixed_bson_types_sort",
        setup_docs=[{"_id": 1, "arr": [1, "string", None, True, {"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [None, 1, "string", {"a": 1}, True]}],
        msg="Mixed BSON types should sort by BSON comparison order",
    ),
    UpdateTestCase(
        id="non_document_elements_with_document_sort",
        setup_docs=[{"_id": 1, "arr": [{"score": 5}, 3, {"score": 1}, "text"]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"score": 1}}}},
        expected=[{"_id": 1, "arr": [3, "text", {"score": 1}, {"score": 5}]}],
        msg="Non-document elements with document sort should sort by BSON type",
    ),
    UpdateTestCase(
        id="sort_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[3, 1], [1, 2], [2, 3]]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [[1, 2], [2, 3], [3, 1]]}],
        msg="Array of arrays should sort by array comparison rules",
    ),
]

DATE_SORT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="dates_sort_chronologically",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                ],
            }
        ],
        msg="Dates should sort chronologically (earliest first)",
    ),
    UpdateTestCase(
        id="dates_sort_descending",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": -1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                ],
            }
        ],
        msg="Dates should sort reverse chronologically (latest first)",
    ),
]


# ---------------------------------------------------------------------------
# Behavioral cases: $sort interactions that succeed (no error)
# ---------------------------------------------------------------------------

MISSING_EACH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_without_each_pushes_literal",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$sort": 1}}},
        expected=[{"_id": 1, "arr": [3, 1, 2, {"$sort": 1}]}],
        msg="$push with $sort but no $each should push literal document",
    ),
]

CONTAINING_ARRAY_FIELD_PATH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_by_containing_array_field_path",
        setup_docs=[
            {
                "_id": 1,
                "arr": [{"score": 3}, {"score": 1}, {"score": 2}],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"arr.score": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [{"score": 3}, {"score": 1}, {"score": 2}],
            }
        ],
        msg="Sort by containing array field path has no matching fields, order unchanged",
    ),
]

BEHAVIOR_TESTS = MISSING_EACH_TESTS + CONTAINING_ARRAY_FIELD_PATH_TESTS


ALL_EDGE_CASE_TESTS = (
    CORE_EDGE_CASE_TESTS
    + NULL_MISSING_TESTS
    + NAN_INFINITY_TESTS
    + BSON_TYPE_DISTINCTION_TESTS
    + MIXED_BSON_TYPE_TESTS
    + DATE_SORT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ALL_EDGE_CASE_TESTS))
def test_update_sort_edge_cases(collection, test_case):
    """Test $sort edge case data type behavior."""
    collection.insert_many(test_case.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test_case.query})
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(BEHAVIOR_TESTS))
def test_update_sort_behaviors(collection, test_case):
    """Test $sort modifier behavioral cases that succeed (no error)."""
    collection.insert_many(test_case.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test_case.query})
    assertSuccess(result, test_case.expected, msg=test_case.msg)
