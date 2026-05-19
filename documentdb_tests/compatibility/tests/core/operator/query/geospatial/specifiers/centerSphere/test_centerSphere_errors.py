"""Tests for $centerSphere error cases — argument structure, invalid types,
and boundary violations."""

from datetime import datetime

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

STRUCTURE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array",
        filter={"loc": {"$geoWithin": {"$centerSphere": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty array argument",
    ),
    QueryTestCase(
        id="missing_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10, 20]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject missing radius (single argument)",
    ),
    QueryTestCase(
        id="extra_elements",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10, 20], 1, "extra"]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject extra elements beyond center and radius",
    ),
    QueryTestCase(
        id="non_array_string",
        filter={"loc": {"$geoWithin": {"$centerSphere": "invalid"}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-array string argument",
    ),
    QueryTestCase(
        id="non_array_number",
        filter={"loc": {"$geoWithin": {"$centerSphere": 123}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-array number argument",
    ),
    QueryTestCase(
        id="non_array_object",
        filter={"loc": {"$geoWithin": {"$centerSphere": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-array object argument",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"loc": {"$geoWithin": {"$centerSphere": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null argument",
    ),
    QueryTestCase(
        id="center_empty_array",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[], 1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty array as center",
    ),
    QueryTestCase(
        id="center_single_element",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10], 1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject center with only 1 coordinate",
    ),
    QueryTestCase(
        id="center_three_elements",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10, 20, 30], 1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject center with 3 coordinates",
    ),
    QueryTestCase(
        id="null_center",
        filter={"loc": {"$geoWithin": {"$centerSphere": [None, 1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null as center",
    ),
    QueryTestCase(
        id="null_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10, 20], None]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null as radius",
    ),
    QueryTestCase(
        id="without_geoWithin_wrapper",
        filter={"loc": {"$centerSphere": [[0, 0], 0.1]}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error when $centerSphere used without $geoWithin",
    ),
]

RADIUS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negative_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], -1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative radius",
    ),
    QueryTestCase(
        id="nan_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], FLOAT_NAN]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN radius",
    ),
    QueryTestCase(
        id="negative_infinity_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], FLOAT_NEGATIVE_INFINITY]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity radius",
    ),
    QueryTestCase(
        id="string_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], "1"]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string as radius",
    ),
    QueryTestCase(
        id="boolean_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], True]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject boolean as radius",
    ),
    QueryTestCase(
        id="object_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], {}]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject object as radius",
    ),
    QueryTestCase(
        id="array_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], [1]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject array as radius",
    ),
]

COORDINATE_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [["10", "20"], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string coordinates",
    ),
    QueryTestCase(
        id="boolean_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[True, False], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject boolean coordinates",
    ),
    QueryTestCase(
        id="object_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[{}, {}], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject object coordinates",
    ),
    QueryTestCase(
        id="null_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[None, None], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null coordinates",
    ),
    QueryTestCase(
        id="array_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[[1], [2]], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject array coordinates",
    ),
    QueryTestCase(
        id="objectid_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[ObjectId(), ObjectId()], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject ObjectId coordinates",
    ),
    QueryTestCase(
        id="regex_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[Regex("a"), Regex("b")], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject regex coordinates",
    ),
    QueryTestCase(
        id="timestamp_coordinates",
        filter={
            "loc": {"$geoWithin": {"$centerSphere": [[Timestamp(0, 0), Timestamp(0, 0)], 0.1]}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject timestamp coordinates",
    ),
    QueryTestCase(
        id="minkey_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[MinKey(), MinKey()], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject MinKey coordinates",
    ),
    QueryTestCase(
        id="maxkey_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[MaxKey(), MaxKey()], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject MaxKey coordinates",
    ),
    QueryTestCase(
        id="date_coordinates",
        filter={
            "loc": {
                "$geoWithin": {"$centerSphere": [[datetime(2024, 1, 1), datetime(2024, 1, 1)], 0.1]}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject date coordinates",
    ),
    QueryTestCase(
        id="bindata_coordinates",
        filter={
            "loc": {"$geoWithin": {"$centerSphere": [[Binary(b"\x00"), Binary(b"\x00")], 0.1]}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject BinData coordinates",
    ),
    QueryTestCase(
        id="javascript_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[Code(""), Code("")], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject JavaScript Code coordinates",
    ),
    QueryTestCase(
        id="nan_longitude",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[FLOAT_NAN, 0], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN as longitude",
    ),
    QueryTestCase(
        id="nan_latitude",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, FLOAT_NAN], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN as latitude",
    ),
    QueryTestCase(
        id="infinity_longitude",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[FLOAT_INFINITY, 0], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity as longitude",
    ),
    QueryTestCase(
        id="negative_infinity_latitude",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, FLOAT_NEGATIVE_INFINITY], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity as latitude",
    ),
]

BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_below_minus_180",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[-181, 0], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude < -180",
    ),
    QueryTestCase(
        id="longitude_above_180",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[181, 0], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude > 180",
    ),
    QueryTestCase(
        id="latitude_below_minus_90",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, -91], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude < -90",
    ),
    QueryTestCase(
        id="latitude_above_90",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 91], 0.1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude > 90",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STRUCTURE_TESTS))
def test_centerSphere_structure_errors(collection, test):
    """Verifies $centerSphere rejects invalid argument structures."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(RADIUS_TESTS))
def test_centerSphere_radius_errors(collection, test):
    """Verifies $centerSphere rejects invalid radius values."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(COORDINATE_TYPE_TESTS))
def test_centerSphere_coordinate_type_errors(collection, test):
    """Verifies $centerSphere rejects non-numeric coordinate types."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(BOUNDARY_TESTS))
def test_centerSphere_boundary_errors(collection, test):
    """Verifies $centerSphere rejects out-of-range coordinates."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
