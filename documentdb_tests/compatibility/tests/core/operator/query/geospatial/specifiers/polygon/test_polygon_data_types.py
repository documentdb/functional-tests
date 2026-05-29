"""
Tests for $polygon data type coverage.

Validates numeric types in coordinates, matching location field types,
non-matching location field types, and embedded object and nested field
path behavior.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, FLOAT_NAN

NUMERIC_COORDINATE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_coordinates",
        filter={"loc": {"$geoWithin": {"$polygon": [[0.0, 0.0], [3.5, 6.5], [7.0, 0.0]]}}},
        doc=[{"_id": 1, "loc": [2.0, 2.0]}, {"_id": 2, "loc": [10.0, 10.0]}],
        expected=[{"_id": 1, "loc": [2.0, 2.0]}],
        msg="$polygon with double coordinates should succeed",
    ),
    QueryTestCase(
        id="long_coordinates",
        filter={
            "loc": {
                "$geoWithin": {
                    "$polygon": [
                        [Int64(0), Int64(0)],
                        [Int64(3), Int64(6)],
                        [Int64(6), Int64(0)],
                    ]
                }
            }
        },
        doc=[{"_id": 1, "loc": [2, 2]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [2, 2]}],
        msg="$polygon with Int64 coordinates should succeed",
    ),
    QueryTestCase(
        id="decimal128_coordinates",
        filter={
            "loc": {
                "$geoWithin": {
                    "$polygon": [
                        [Decimal128("0"), Decimal128("0")],
                        [Decimal128("3"), Decimal128("6")],
                        [Decimal128("6"), Decimal128("0")],
                    ]
                }
            }
        },
        doc=[{"_id": 1, "loc": [2, 2]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [2, 2]}],
        msg="$polygon with Decimal128 coordinates should succeed",
    ),
    QueryTestCase(
        id="mixed_numeric_types",
        filter={
            "loc": {
                "$geoWithin": {
                    "$polygon": [
                        [0, 0.0],
                        [Int64(3), Decimal128("6")],
                        [6, 0],
                    ]
                }
            }
        },
        doc=[{"_id": 1, "loc": [2, 2]}, {"_id": 2, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [2, 2]}],
        msg="$polygon with mixed numeric types should succeed",
    ),
]


LOCATION_FIELD_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="legacy_coordinate_pair",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Legacy coordinate pair should match",
    ),
    QueryTestCase(
        id="geojson_point_also_matches",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 2, "loc": [5, 5]},
            {"_id": 3, "loc": [15, 15]},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 2, "loc": [5, 5]},
        ],
        msg="$polygon matches both GeoJSON points and legacy coordinate pairs",
    ),
]

NON_MATCHING_FIELD_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": None}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Null location field should not match",
    ),
    QueryTestCase(
        id="missing_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "name": "no_loc"}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Missing location field should not match",
    ),
    QueryTestCase(
        id="string_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": "not_a_point"}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="String location field should not match",
    ),
    QueryTestCase(
        id="int_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": 42}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Integer location field should not match",
    ),
    QueryTestCase(
        id="boolean_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": True}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Boolean location field should not match",
    ),
    QueryTestCase(
        id="nan_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": [FLOAT_NAN, FLOAT_NAN]}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="NaN location field should not match",
    ),
    QueryTestCase(
        id="infinity_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": [FLOAT_INFINITY, FLOAT_INFINITY]}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Infinity location field should not match",
    ),
    QueryTestCase(
        id="javascript_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": Code("function() {}")}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="JavaScript location field should not match",
    ),
    QueryTestCase(
        id="binary_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": Binary(b"\x00")}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Binary location field should not match",
    ),
    QueryTestCase(
        id="objectid_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": ObjectId()}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="ObjectId location field should not match",
    ),
    QueryTestCase(
        id="date_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "loc": [5, 5]},
        ],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Date location field should not match",
    ),
    QueryTestCase(
        id="regex_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": Regex(".*")}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Regex location field should not match",
    ),
    QueryTestCase(
        id="timestamp_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": Timestamp(0, 0)}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Timestamp location field should not match",
    ),
    QueryTestCase(
        id="minkey_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": MinKey()}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="MinKey location field should not match",
    ),
    QueryTestCase(
        id="maxkey_location_no_match",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[{"_id": 1, "loc": MaxKey()}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="MaxKey location field should not match",
    ),
]


EMBEDDED_LOCATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="embedded_object_location",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": {"x": 5, "y": 5}},
            {"_id": 2, "loc": [5, 5]},
            {"_id": 3, "loc": [15, 15]},
        ],
        expected=[{"_id": 1, "loc": {"x": 5, "y": 5}}, {"_id": 2, "loc": [5, 5]}],
        msg="Embedded object {x,y} format should match like coordinate pair",
    ),
    QueryTestCase(
        id="embedded_doc_non_xy_keys",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": {"a": 5, "b": 5}},
            {"_id": 2, "loc": [5, 5]},
            {"_id": 3, "loc": [15, 15]},
        ],
        expected=[
            {"_id": 1, "loc": {"a": 5, "b": 5}},
            {"_id": 2, "loc": [5, 5]},
        ],
        msg="Embedded doc with non-x/y keys uses first two fields as x/y",
    ),
    QueryTestCase(
        id="nested_field_missing_intermediate",
        filter={"address.loc": {"$geoWithin": {"$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "address": {"loc": [5, 5]}},
            {"_id": 2, "other": "no_address"},
            {"_id": 3, "address": None},
        ],
        expected=[{"_id": 1, "address": {"loc": [5, 5]}}],
        msg="Missing intermediate in nested path should not match",
    ),
]


DATA_TYPE_TESTS: list[QueryTestCase] = (
    NUMERIC_COORDINATE_TESTS
    + LOCATION_FIELD_TYPE_TESTS
    + NON_MATCHING_FIELD_TYPE_TESTS
    + EMBEDDED_LOCATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DATA_TYPE_TESTS))
def test_polygon_data_types(collection, test):
    """Test $polygon data type coverage."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
