"""
Tests for $polygon error handling.

Validates error codes for invalid operator usage, invalid polygon specifications,
invalid argument formats, invalid point formats, invalid coordinate types,
and special numeric values in coordinates.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

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

INVALID_OPERATOR_USAGE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="polygon_without_geoWithin",
        filter={"loc": {"$polygon": [[0, 0], [1, 1], [2, 0]]}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon without $geoWithin wrapper should error",
    ),
    QueryTestCase(
        id="polygon_with_geoIntersects",
        filter={"loc": {"$geoIntersects": {"$polygon": [[0, 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with $geoIntersects should error",
    ),
]


INVALID_POLYGON_SPEC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array",
        filter={"loc": {"$geoWithin": {"$polygon": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with empty array should error",
    ),
    QueryTestCase(
        id="one_point",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with 1 point should error",
    ),
    QueryTestCase(
        id="fewer_than_3_points",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [1, 1]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with fewer than 3 points should error",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"loc": {"$geoWithin": {"$polygon": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with null argument should error",
    ),
    QueryTestCase(
        id="non_array_argument",
        filter={"loc": {"$geoWithin": {"$polygon": "invalid"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with non-array argument should error",
    ),
]


INVALID_ARGUMENT_FORMAT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_arg",
        filter={"loc": {"$geoWithin": {"$polygon": 123}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with integer argument should error",
    ),
    QueryTestCase(
        id="object_arg",
        filter={"loc": {"$geoWithin": {"$polygon": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with object argument should error",
    ),
    QueryTestCase(
        id="bool_arg",
        filter={"loc": {"$geoWithin": {"$polygon": True}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with boolean argument should error",
    ),
]


INVALID_POINT_FORMAT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="flat_array_not_nested",
        filter={"loc": {"$geoWithin": {"$polygon": [1, 2, 3]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with flat array instead of nested coordinate pairs should error",
    ),
    QueryTestCase(
        id="point_as_string",
        filter={"loc": {"$geoWithin": {"$polygon": ["a", "b", "c"]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with string points should error",
    ),
    QueryTestCase(
        id="point_with_non_numeric_string",
        filter={"loc": {"$geoWithin": {"$polygon": [["x", "y"], ["a", "b"], ["c", "d"]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with string coordinate values should error",
    ),
    QueryTestCase(
        id="point_with_non_numeric",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], ["a", "b"], [1, 1]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with non-numeric coordinates should error",
    ),
    QueryTestCase(
        id="point_with_null",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [None, None], [1, 1]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with null coordinates should error",
    ),
    QueryTestCase(
        id="point_with_boolean",
        filter={"loc": {"$geoWithin": {"$polygon": [[True, False], [0, 0], [1, 1]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with boolean coordinates should error",
    ),
    QueryTestCase(
        id="single_coordinate_point",
        filter={"loc": {"$geoWithin": {"$polygon": [[0], [1], [2]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with single-coordinate points should error",
    ),
    QueryTestCase(
        id="three_element_points",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0, 0], [1, 1, 1], [2, 0, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with 3-element coordinate points should error",
    ),
    QueryTestCase(
        id="empty_sub_arrays_as_points",
        filter={"loc": {"$geoWithin": {"$polygon": [[], [], []]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with empty sub-arrays as points should error",
    ),
]


INVALID_COORDINATE_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="objectid_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[ObjectId(), 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="ObjectId in coordinate should error",
    ),
    QueryTestCase(
        id="regex_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[Regex("x"), 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Regex in coordinate should error",
    ),
    QueryTestCase(
        id="timestamp_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[Timestamp(0, 0), 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Timestamp in coordinate should error",
    ),
    QueryTestCase(
        id="minkey_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[MinKey(), 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="MinKey in coordinate should error",
    ),
    QueryTestCase(
        id="maxkey_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[MaxKey(), 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="MaxKey in coordinate should error",
    ),
    QueryTestCase(
        id="bindata_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[Binary(b"\x00"), 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="BinData in coordinate should error",
    ),
    QueryTestCase(
        id="javascript_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[Code("x"), 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="JavaScript in coordinate should error",
    ),
    QueryTestCase(
        id="date_in_coordinate",
        filter={
            "loc": {
                "$geoWithin": {
                    "$polygon": [[datetime(2024, 1, 1, tzinfo=timezone.utc), 0], [1, 1], [2, 0]]
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Date in coordinate should error",
    ),
    QueryTestCase(
        id="nan_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[FLOAT_NAN, 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="NaN in coordinate should error",
    ),
    QueryTestCase(
        id="infinity_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[FLOAT_INFINITY, 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Infinity in coordinate should error",
    ),
    QueryTestCase(
        id="negative_infinity_in_coordinate",
        filter={
            "loc": {
                "$geoWithin": {
                    "$polygon": [
                        [FLOAT_NEGATIVE_INFINITY, 0],
                        [1, 1],
                        [2, 0],
                    ]
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative infinity in coordinate should error",
    ),
    QueryTestCase(
        id="object_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[{"a": 1}, 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Object in coordinate should error",
    ),
    QueryTestCase(
        id="array_in_coordinate",
        filter={"loc": {"$geoWithin": {"$polygon": [[[1, 2], 0], [1, 1], [2, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Array in coordinate should error",
    ),
]


ERROR_TESTS: list[QueryTestCase] = (
    INVALID_OPERATOR_USAGE_TESTS
    + INVALID_POLYGON_SPEC_TESTS
    + INVALID_ARGUMENT_FORMAT_TESTS
    + INVALID_POINT_FORMAT_TESTS
    + INVALID_COORDINATE_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_polygon_errors(collection, test):
    """Test $polygon error handling."""
    collection.insert_many([{"_id": 1, "loc": [1, 1]}])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code)
