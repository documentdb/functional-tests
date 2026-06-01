"""Tests for $maxDistance error cases — invalid context, values, types, and missing index."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, NO_QUERY_EXECUTION_PLANS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

ORIGIN = {"type": "Point", "coordinates": [0, 0]}


ERROR_TESTS: list[QueryTestCase] = [
    # Invalid context
    QueryTestCase(
        id="without_near_context",
        filter={"loc": {"$maxDistance": 1000}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $maxDistance without $near or $nearSphere context",
    ),
    QueryTestCase(
        id="with_geoWithin",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                    }
                },
                "$maxDistance": 1000,
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $maxDistance with $geoWithin",
    ),
    QueryTestCase(
        id="nearSphere_without_geometry",
        filter={"loc": {"$nearSphere": {"$maxDistance": 5000, "$minDistance": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $nearSphere with $maxDistance but no $geometry",
    ),
    # Invalid values
    QueryTestCase(
        id="negative",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": -1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative $maxDistance",
    ),
    QueryTestCase(
        id="negative_double",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": -0.5}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative double $maxDistance",
    ),
    QueryTestCase(
        id="negative_int64",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": Int64(-1)}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative Int64 $maxDistance",
    ),
    QueryTestCase(
        id="negative_decimal128",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": Decimal128("-1")}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject negative Decimal128 $maxDistance",
    ),
    QueryTestCase(
        id="nan",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": FLOAT_NAN}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN $maxDistance",
    ),
    QueryTestCase(
        id="infinity",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": FLOAT_INFINITY}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity $maxDistance",
    ),
    QueryTestCase(
        id="negative_infinity",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": FLOAT_NEGATIVE_INFINITY}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity $maxDistance",
    ),
    QueryTestCase(
        id="decimal128_max",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": DECIMAL128_MAX}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $maxDistance=DECIMAL128_MAX as non-negative overflow",
    ),
    QueryTestCase(
        id="decimal128_nan",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": DECIMAL128_NAN}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Decimal128 NaN $maxDistance",
    ),
    QueryTestCase(
        id="decimal128_infinity",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": DECIMAL128_INFINITY}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Decimal128 Infinity $maxDistance",
    ),
    QueryTestCase(
        id="decimal128_negative_infinity",
        filter={
            "loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": DECIMAL128_NEGATIVE_INFINITY}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Decimal128 -Infinity $maxDistance",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_maxDistance_errors(collection, test):
    """Verifies $maxDistance rejects invalid contexts, values, and types."""
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


NO_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_without_index",
        filter={"loc": {"$near": {"$geometry": ORIGIN, "$maxDistance": 1000}}},
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should error when no geospatial index exists",
    ),
    QueryTestCase(
        id="nearSphere_without_index",
        filter={"loc": {"$nearSphere": {"$geometry": ORIGIN, "$maxDistance": 1000}}},
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should error when no geospatial index for $nearSphere",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NO_INDEX_TESTS))
def test_maxDistance_no_index_errors(collection, test):
    """Verifies $maxDistance fails without geospatial index."""
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
