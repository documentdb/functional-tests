"""Tests for $minDistance error cases — invalid context, values, types, and missing index."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

ORIGIN = {"type": "Point", "coordinates": [0, 0]}


ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="without_near_context",
        filter={"loc": {"$minDistance": 1000}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $minDistance without $near or $nearSphere context",
    ),
    QueryTestCase(
        id="minDistance_with_geoWithin",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                    },
                    "$minDistance": 1000,
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $minDistance with $geoWithin (invalid context)",
    ),
    QueryTestCase(
        id="nearSphere_minDistance_without_geometry",
        filter={
            "loc": {
                "$nearSphere": {"$minDistance": 1000, "$maxDistance": 5000},
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $nearSphere with $minDistance but no $geometry or coordinates",
    ),
]


INVALID_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negative_int",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": -1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative int $minDistance",
    ),
    QueryTestCase(
        id="negative_double",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": -1.5}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative double $minDistance",
    ),
    QueryTestCase(
        id="negative_int64",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": Int64(-1)}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative Int64 $minDistance",
    ),
    QueryTestCase(
        id="negative_decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": Decimal128("-1")}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative Decimal128 $minDistance",
    ),
    QueryTestCase(
        id="nan_double",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": FLOAT_NAN}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN $minDistance",
    ),
    QueryTestCase(
        id="negative_nan_double",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": FLOAT_NEGATIVE_NAN}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -NaN $minDistance",
    ),
    QueryTestCase(
        id="infinity",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": FLOAT_INFINITY}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity $minDistance",
    ),
    QueryTestCase(
        id="negative_infinity",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": FLOAT_NEGATIVE_INFINITY}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity $minDistance",
    ),
    QueryTestCase(
        id="nan_decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": DECIMAL128_NAN}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Decimal128 NaN $minDistance",
    ),
    QueryTestCase(
        id="negative_nan_decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": DECIMAL128_NEGATIVE_NAN}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Decimal128 -NaN $minDistance",
    ),
    QueryTestCase(
        id="infinity_decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": DECIMAL128_INFINITY}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Decimal128 Infinity $minDistance",
    ),
    QueryTestCase(
        id="negative_infinity_decimal128",
        filter={
            "loc": {"$near": {"$geometry": ORIGIN, "$minDistance": DECIMAL128_NEGATIVE_INFINITY}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Decimal128 -Infinity $minDistance",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS + INVALID_VALUE_TESTS))
def test_minDistance_errors(collection, test):
    """Verifies $minDistance rejects invalid contexts and values."""
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


# --- Legacy (2d) path invalid values ---

LEGACY_INVALID_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="legacy_negative_int",
        filter={"loc": {"$near": [0, 0], "$minDistance": -1}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject negative int $minDistance with legacy 2d",
    ),
    QueryTestCase(
        id="legacy_negative_double",
        filter={"loc": {"$near": [0, 0], "$minDistance": -1.5}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject negative double $minDistance with legacy 2d",
    ),
    QueryTestCase(
        id="legacy_nan_double",
        filter={"loc": {"$near": [0, 0], "$minDistance": FLOAT_NAN}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject NaN $minDistance with legacy 2d",
    ),
    QueryTestCase(
        id="legacy_negative_nan_double",
        filter={"loc": {"$near": [0, 0], "$minDistance": FLOAT_NEGATIVE_NAN}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject -NaN $minDistance with legacy 2d",
    ),
    QueryTestCase(
        id="legacy_negative_infinity",
        filter={"loc": {"$near": [0, 0], "$minDistance": FLOAT_NEGATIVE_INFINITY}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject -Infinity $minDistance with legacy 2d",
    ),
    QueryTestCase(
        id="legacy_nan_decimal128",
        filter={"loc": {"$near": [0, 0], "$minDistance": DECIMAL128_NAN}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject Decimal128 NaN $minDistance with legacy 2d",
    ),
    QueryTestCase(
        id="legacy_negative_nan_decimal128",
        filter={"loc": {"$near": [0, 0], "$minDistance": DECIMAL128_NEGATIVE_NAN}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject Decimal128 -NaN $minDistance with legacy 2d",
    ),
    QueryTestCase(
        id="legacy_negative_infinity_decimal128",
        filter={"loc": {"$near": [0, 0], "$minDistance": DECIMAL128_NEGATIVE_INFINITY}},
        error_code=LEGACY_MIN_DISTANCE_NON_NEGATIVE_ERROR,
        msg="Should reject Decimal128 -Infinity $minDistance with legacy 2d",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LEGACY_INVALID_VALUE_TESTS))
def test_minDistance_legacy_errors(collection, test):
    """Verifies $minDistance rejects invalid values with legacy 2d index."""
    collection.create_index([("loc", "2d")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


NO_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_without_index",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$minDistance": 1000}}},
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should error when no geospatial index exists",
    ),
    QueryTestCase(
        id="nearSphere_without_index",
        filter={"loc": {"$nearSphere": {"$geometry": ORIGIN, "$minDistance": 1000}}},
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should error when no geospatial index for $nearSphere",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NO_INDEX_TESTS))
def test_minDistance_no_index_errors(collection, test):
    """Verifies $minDistance fails without geospatial index."""
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
