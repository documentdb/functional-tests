"""Tests for $centerSphere valid argument handling — valid types, null/missing fields."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

VALID_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10, 20], 0.5]}}},
        doc=[{"_id": 1, "loc": [10, 20]}],
        expected=[{"_id": 1, "loc": [10, 20]}],
        msg="Should accept int coordinates",
    ),
    QueryTestCase(
        id="int64_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[Int64(10), Int64(20)], 0.5]}}},
        doc=[{"_id": 1, "loc": [10, 20]}],
        expected=[{"_id": 1, "loc": [10, 20]}],
        msg="Should accept Int64 coordinates",
    ),
    QueryTestCase(
        id="float_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[10.5, 20.5], 0.5]}}},
        doc=[{"_id": 1, "loc": [10.5, 20.5]}],
        expected=[{"_id": 1, "loc": [10.5, 20.5]}],
        msg="Should accept float coordinates",
    ),
    QueryTestCase(
        id="decimal128_coordinates",
        filter={
            "loc": {"$geoWithin": {"$centerSphere": [[Decimal128("10"), Decimal128("20")], 0.5]}}
        },
        doc=[{"_id": 1, "loc": [10, 20]}],
        expected=[{"_id": 1, "loc": [10, 20]}],
        msg="Should accept Decimal128 coordinates",
    ),
    QueryTestCase(
        id="mixed_int_int64_coordinates",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, Int64(0)], 0.5]}}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept mixed int and Int64 coordinates",
    ),
    QueryTestCase(
        id="int_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept int radius",
    ),
    QueryTestCase(
        id="int64_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], Int64(1)]}}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept Int64 radius",
    ),
    QueryTestCase(
        id="decimal128_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], Decimal128("0.5")]}}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept Decimal128 radius",
    ),
    QueryTestCase(
        id="boundary_longitude_minus_180",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[-180, 0], 0.1]}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        msg="Should accept longitude = -180",
    ),
    QueryTestCase(
        id="boundary_longitude_180",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[180, 0], 0.1]}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        msg="Should accept longitude = 180",
    ),
    QueryTestCase(
        id="boundary_latitude_minus_90",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, -90], 0.1]}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        msg="Should accept latitude = -90",
    ),
    QueryTestCase(
        id="boundary_latitude_90",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 90], 0.1]}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        msg="Should accept latitude = 90",
    ),
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_field_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[{"_id": 1, "loc": None}, {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should not match document with null location field",
    ),
    QueryTestCase(
        id="missing_field_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "other": "value"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should not match document with missing location field",
    ),
    QueryTestCase(
        id="mixed_valid_null_missing",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": None},
            {"_id": 3, "other": "x"},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should only match documents with valid location among mixed null/missing",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_TYPE_TESTS))
def test_centerSphere_valid_types(collection, test):
    """Verifies $centerSphere accepts valid numeric types for coordinates and radius."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


@pytest.mark.parametrize("test", pytest_params(NULL_MISSING_TESTS))
def test_centerSphere_null_missing_fields(collection, test):
    """Verifies $centerSphere does not match documents with null or missing location fields."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
