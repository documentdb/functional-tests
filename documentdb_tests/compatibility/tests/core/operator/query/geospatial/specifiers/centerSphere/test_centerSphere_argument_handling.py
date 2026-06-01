"""Tests for $centerSphere valid argument handling — valid types,
boundary values, embedded document coordinate formats, non-geospatial
field values, array location fields, and null/missing fields."""

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
        id="float_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.5]}}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept float radius",
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
    QueryTestCase(
        id="embedded_doc_non_xy_keys",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": {"a": 0, "b": 0}},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[
            {"_id": 1, "loc": {"a": 0, "b": 0}},
            {"_id": 2, "loc": [0, 0]},
        ],
        msg="Embedded doc with non-x/y keys uses first two fields as coordinates",
    ),
    QueryTestCase(
        id="embedded_doc_xy_keys",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": {"x": 0, "y": 0}},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[
            {"_id": 1, "loc": {"x": 0, "y": 0}},
            {"_id": 2, "loc": [0, 0]},
        ],
        msg="Embedded doc with canonical x/y keys as legacy coordinates",
    ),
]

NON_GEO_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="number_field_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": 42},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should silently skip document with number as location field",
    ),
    QueryTestCase(
        id="string_field_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": "hello"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should silently skip document with string as location field",
    ),
    QueryTestCase(
        id="boolean_field_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": True},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should silently skip document with boolean as location field",
    ),
    QueryTestCase(
        id="empty_array_field_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": []},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should silently skip document with empty array as location field",
    ),
    QueryTestCase(
        id="empty_object_field_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": {}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should silently skip document with empty object as location field",
    ),
    QueryTestCase(
        id="three_element_array_uses_first_two",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": [0, 0, 0]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [50, 50]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0, 0]},
            {"_id": 2, "loc": [0, 0]},
        ],
        msg="3-element array location uses first two elements as coordinates",
    ),
    QueryTestCase(
        id="single_element_array_not_matched",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
        doc=[
            {"_id": 1, "loc": [5]},
            {"_id": 2, "loc": [0, 0]},
        ],
        expected=[{"_id": 2, "loc": [0, 0]}],
        msg="Single-element array location should not match",
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
]

ALL_TESTS = VALID_TYPE_TESTS + NON_GEO_FIELD_TESTS + NULL_MISSING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_centerSphere_argument_handling(collection, test):
    """Verifies $centerSphere accepts valid types, skips non-geospatial
    fields, and handles null/missing."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
