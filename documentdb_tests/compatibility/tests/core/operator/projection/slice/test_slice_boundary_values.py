"""Tests for $slice projection: boundary values and numeric type coercion.

Tests $slice with INT32/INT64 boundaries, fractional doubles, Decimal128, Infinity, NaN,
and positional operator interaction.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX, INT32_MIN, INT64_MAX, INT64_MIN

POSITIONAL_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "positional_on_different_field",
        projection={"arr1": {"$slice": 2}, "arr2.$": 1},
        doc=[
            {"_id": 1, "arr1": [1, 2, 3], "arr2": [10, 20, 30]},
            {"_id": 2, "arr1": [4, 5, 6], "arr2": [40, 50, 60]},
        ],
        expected=[{"_id": 1, "arr1": [1, 2], "arr2": [20]}],
        msg="$slice with $ positional on different field should work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_TESTS))
def test_slice_with_positional(collection, test: ProjectionTestCase):
    """Test $slice with $ positional on different field."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr2": 20},
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


BOUNDARY_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "int32_max",
        projection={"arr": {"$slice": INT32_MAX}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: INT32_MAX should return all elements",
    ),
    ProjectionTestCase(
        "int32_min",
        projection={"arr": {"$slice": INT32_MIN}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: INT32_MIN should return all elements (abs exceeds length)",
    ),
    ProjectionTestCase(
        "int64_value",
        projection={"arr": {"$slice": Int64(1)}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1]}],
        msg="$slice: NumberLong(1) should be valid and return first element",
    ),
    ProjectionTestCase(
        "int64_max",
        projection={"arr": {"$slice": INT64_MAX}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: INT64_MAX should return all elements (exceeds length)",
    ),
    ProjectionTestCase(
        "int64_min",
        projection={"arr": {"$slice": INT64_MIN}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: INT64_MIN should return all elements (abs exceeds length)",
    ),
    ProjectionTestCase(
        "whole_number_double",
        projection={"arr": {"$slice": 1.0}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1]}],
        msg="$slice: 1.0 (whole-number double) should be valid",
    ),
    ProjectionTestCase(
        "fractional_double_truncates",
        projection={"arr": {"$slice": 1.5}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1]}],
        msg="$slice: 1.5 (fractional double) should truncate to 1 (server truncates toward zero)",
    ),
    ProjectionTestCase(
        "skip_return_int32_max_skip",
        projection={"arr": {"$slice": [INT32_MAX, 1]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: [INT32_MAX, 1] should return empty (skip exceeds length)",
    ),
    ProjectionTestCase(
        "skip_return_int32_max_limit",
        projection={"arr": {"$slice": [0, INT32_MAX]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: [0, INT32_MAX] should return all elements",
    ),
    ProjectionTestCase(
        "skip_return_int32_min_skip",
        projection={"arr": {"$slice": [INT32_MIN, 1]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1]}],
        msg="$slice: [INT32_MIN, 1] should start from beginning and return first",
    ),
    ProjectionTestCase(
        "fractional_limit_in_array_form",
        projection={"arr": {"$slice": [0, 1.5]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1]}],
        msg="$slice: [0, 1.5] fractional limit should truncate to 1",
    ),
    ProjectionTestCase(
        "fractional_skip_in_array_form",
        projection={"arr": {"$slice": [1.5, 1]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [2]}],
        msg="$slice: [1.5, 1] fractional skip should truncate to 1",
    ),
    ProjectionTestCase(
        "zero_as_double",
        projection={"arr": {"$slice": 0.0}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: 0.0 (double) should behave same as int 0 → empty array",
    ),
    ProjectionTestCase(
        "negative_skip_exceeds_limit_exceeds",
        projection={"arr": {"$slice": [-10, 100]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: [-10, 100] on small array — both skip and limit exceed → all elements",
    ),
    ProjectionTestCase(
        "int64_skip_and_limit",
        projection={"arr": {"$slice": [Int64(0), Int64(2)]}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$slice: [Int64(0), Int64(2)] should accept Int64 in array form",
    ),
    ProjectionTestCase(
        "decimal128_single_value",
        projection={"arr": {"$slice": Decimal128("2")}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$slice: Decimal128('2') should return first 2 elements",
    ),
    ProjectionTestCase(
        "decimal128_in_array_form",
        projection={"arr": {"$slice": [Decimal128("1"), Decimal128("2")]}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        expected=[{"_id": 1, "arr": [2, 3]}],
        msg="$slice: [Decimal128('1'), Decimal128('2')] should work in array form",
    ),
    ProjectionTestCase(
        "negative_fractional_skip_in_array_form",
        projection={"arr": {"$slice": [-1.5, 2]}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        expected=[{"_id": 1, "arr": [4]}],
        msg="$slice: [-1.5, 2] negative fractional skip truncates to -1, returns from last",
    ),
    ProjectionTestCase(
        "infinity_returns_all",
        projection={"arr": {"$slice": float("inf")}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: Infinity should return all elements",
    ),
    ProjectionTestCase(
        "nan_returns_empty",
        projection={"arr": {"$slice": float("nan")}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: NaN should return empty array (server coerces NaN to 0)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BOUNDARY_TESTS))
def test_slice_boundary_values(collection, test: ProjectionTestCase):
    """Test $slice projection with boundary values."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "projection": test.projection},
    )
    assertSuccess(result, test.expected, msg=test.msg)
