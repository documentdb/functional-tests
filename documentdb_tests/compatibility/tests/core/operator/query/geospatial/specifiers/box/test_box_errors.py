"""
Tests for $box error conditions.

Validates errors for invalid contexts, invalid argument structures,
invalid point formats, and special numeric values.

Note: BSON type rejection/acceptance is covered in test_box_bson_comparison.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ERROR_TESTS: list[QueryTestCase] = [
    # Invalid context
    QueryTestCase(
        id="box_without_geoWithin",
        filter={"loc": {"$box": [[0, 0], [10, 10]]}},
        error_code=BAD_VALUE_ERROR,
        msg="$box without $geoWithin wrapper should error",
    ),
    QueryTestCase(
        id="box_with_geoIntersects",
        filter={"loc": {"$geoIntersects": {"$box": [[0, 0], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$box with $geoIntersects should error",
    ),
    QueryTestCase(
        id="box_with_near",
        filter={"loc": {"$near": {"$box": [[0, 0], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$box with $near should error",
    ),
    # Invalid argument structure
    QueryTestCase(
        id="empty_array",
        filter={"loc": {"$geoWithin": {"$box": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty array should error",
    ),
    QueryTestCase(
        id="single_point",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Single point should error",
    ),
    QueryTestCase(
        id="string_argument",
        filter={"loc": {"$geoWithin": {"$box": "invalid"}}},
        error_code=BAD_VALUE_ERROR,
        msg="String argument should error",
    ),
    QueryTestCase(
        id="int_argument",
        filter={"loc": {"$geoWithin": {"$box": 123}}},
        error_code=BAD_VALUE_ERROR,
        msg="Integer argument should error",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"loc": {"$geoWithin": {"$box": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="Null argument should error",
    ),
    # Invalid point formats
    QueryTestCase(
        id="point_with_1_coordinate",
        filter={"loc": {"$geoWithin": {"$box": [[0], [100]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Point with 1 coordinate should error",
    ),
    QueryTestCase(
        id="point_with_3_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0, 0], [100, 100, 100]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Point with 3 coordinates should error",
    ),
    QueryTestCase(
        id="empty_point_arrays",
        filter={"loc": {"$geoWithin": {"$box": [[], []]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty point arrays should error",
    ),
    QueryTestCase(
        id="point_as_non_array",
        filter={"loc": {"$geoWithin": {"$box": [0, [100, 100]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Point as non-array should error",
    ),
    # Special numeric values
    QueryTestCase(
        id="nan_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[float("nan"), float("nan")], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="NaN coordinates in first point (bottomLeft) should error",
    ),
    QueryTestCase(
        id="nan_coordinates_second_point",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [float("nan"), float("nan")]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="NaN coordinates in second point (topRight) should error",
    ),
    QueryTestCase(
        id="infinity_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [float("inf"), float("inf")]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Infinity coordinates in second point (topRight) should error",
    ),
    QueryTestCase(
        id="infinity_coordinates_first_point",
        filter={"loc": {"$geoWithin": {"$box": [[float("inf"), float("inf")], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Infinity coordinates in first point (bottomLeft) should error",
    ),
    QueryTestCase(
        id="negative_infinity_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[float("-inf"), float("-inf")], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Negative infinity coordinates in first point (bottomLeft) should error",
    ),
    QueryTestCase(
        id="negative_infinity_coordinates_second_point",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [float("-inf"), float("-inf")]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Negative infinity coordinates in second point (topRight) should error",
    ),
    # Mixed valid/invalid
    QueryTestCase(
        id="mixed_valid_invalid_in_point",
        filter={"loc": {"$geoWithin": {"$box": [[0, "bad"], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Mixed valid and invalid coordinate in same point should error",
    ),
    QueryTestCase(
        id="partial_null_in_point",
        filter={"loc": {"$geoWithin": {"$box": [[0, None], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="One valid coordinate and one null in same point should error",
    ),
    QueryTestCase(
        id="second_point_as_non_array",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], "bad"]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Second point as non-array should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_box_errors(collection, test):
    """Test $box error conditions."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, error_code=test.error_code, msg=test.msg)
