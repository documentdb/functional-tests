"""Tests for $center error cases — argument structure, context, and numeric edge cases."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array",
        filter={"loc": {"$geoWithin": {"$center": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty array argument",
    ),
    QueryTestCase(
        id="missing_radius",
        filter={"loc": {"$geoWithin": {"$center": [[-74, 40.74]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject missing radius",
    ),
    QueryTestCase(
        id="extra_elements",
        filter={"loc": {"$geoWithin": {"$center": [[-74, 40.74], 10, "extra"]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject extra elements",
    ),
    QueryTestCase(
        id="non_array_string",
        filter={"loc": {"$geoWithin": {"$center": "invalid"}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-array string argument",
    ),
    QueryTestCase(
        id="non_array_number",
        filter={"loc": {"$geoWithin": {"$center": 123}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-array number argument",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"loc": {"$geoWithin": {"$center": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null argument",
    ),
    QueryTestCase(
        id="center_one_coordinate",
        filter={"loc": {"$geoWithin": {"$center": [[-74], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject center with only 1 coordinate",
    ),
    QueryTestCase(
        id="center_three_coordinates",
        filter={"loc": {"$geoWithin": {"$center": [[-74, 40.74, 0], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject center with 3 coordinates",
    ),
    QueryTestCase(
        id="center_empty_array",
        filter={"loc": {"$geoWithin": {"$center": [[], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject center with 0 coordinates",
    ),
    QueryTestCase(
        id="without_geoWithin_wrapper",
        filter={"loc": {"$center": [[0, 0], 10]}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error when $center used without $geoWithin",
    ),
    QueryTestCase(
        id="with_geoIntersects",
        filter={"loc": {"$geoIntersects": {"$center": [[0, 0], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error when $center used with $geoIntersects",
    ),
    QueryTestCase(
        id="with_near",
        filter={"loc": {"$near": {"$center": [[0, 0], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error when $center used with $near",
    ),
    QueryTestCase(
        id="negative_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], -1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative radius",
    ),
    QueryTestCase(
        id="nan_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], FLOAT_NAN]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN radius",
    ),
    QueryTestCase(
        id="negative_infinity_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], FLOAT_NEGATIVE_INFINITY]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity radius",
    ),
    QueryTestCase(
        id="nan_x_coordinate",
        filter={"loc": {"$geoWithin": {"$center": [[FLOAT_NAN, 0], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN x-coordinate",
    ),
    QueryTestCase(
        id="infinity_x_coordinate",
        filter={"loc": {"$geoWithin": {"$center": [[FLOAT_INFINITY, 0], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity x-coordinate",
    ),
    QueryTestCase(
        id="string_in_center_coordinates",
        filter={"loc": {"$geoWithin": {"$center": [["a", 0], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string in center coordinates",
    ),
    QueryTestCase(
        id="string_as_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], "10"]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string as radius",
    ),
    QueryTestCase(
        id="nan_y_coordinate",
        filter={"loc": {"$geoWithin": {"$center": [[0, FLOAT_NAN], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN y-coordinate",
    ),
    QueryTestCase(
        id="infinity_y_coordinate",
        filter={"loc": {"$geoWithin": {"$center": [[0, FLOAT_INFINITY], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity y-coordinate",
    ),
    QueryTestCase(
        id="negative_infinity_x_coordinate",
        filter={"loc": {"$geoWithin": {"$center": [[FLOAT_NEGATIVE_INFINITY, 0], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity x-coordinate",
    ),
    QueryTestCase(
        id="negative_infinity_y_coordinate",
        filter={"loc": {"$geoWithin": {"$center": [[0, FLOAT_NEGATIVE_INFINITY], 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity y-coordinate",
    ),
    QueryTestCase(
        id="boolean_as_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], True]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject boolean as radius",
    ),
    QueryTestCase(
        id="object_as_center",
        filter={"loc": {"$geoWithin": {"$center": [{"x": 0}, 10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject object as center",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_center_errors(collection, test):
    """Verifies $center rejects invalid arguments with appropriate error codes."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
