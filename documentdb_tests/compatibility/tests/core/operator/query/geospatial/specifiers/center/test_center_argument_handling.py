"""Tests for $center valid argument and type handling."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="valid_structure",
        filter={"loc": {"$geoWithin": {"$center": [[-74, 40.74], 100]}}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept valid $center structure",
    ),
    QueryTestCase(
        id="coords_int_and_int64",
        filter={"loc": {"$geoWithin": {"$center": [[0, INT64_ZERO], 10]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [100, 100]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept int and Int64 mixed coordinates",
    ),
    QueryTestCase(
        id="coords_int64_and_decimal128",
        filter={"loc": {"$geoWithin": {"$center": [[Int64(0), Decimal128("0")], 10]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [100, 100]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept Int64 and Decimal128 mixed coordinates",
    ),
    QueryTestCase(
        id="coords_float_and_decimal128",
        filter={"loc": {"$geoWithin": {"$center": [[0.0, Decimal128("0")], 10]}}},
        doc=[{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [100, 100]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should accept float and Decimal128 mixed coordinates",
    ),
    QueryTestCase(
        id="string_field_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}},
        doc=[{"_id": 1, "loc": "not a coordinate"}],
        expected=[],
        msg="Should not match string field value",
    ),
    QueryTestCase(
        id="number_field_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}},
        doc=[{"_id": 1, "loc": 42}],
        expected=[],
        msg="Should not match plain number field value",
    ),
    QueryTestCase(
        id="object_field_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}},
        doc=[{"_id": 1, "loc": {"nested": "object"}}],
        expected=[],
        msg="Should not match nested object field value",
    ),
    QueryTestCase(
        id="boolean_field_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}},
        doc=[{"_id": 1, "loc": True}],
        expected=[],
        msg="Should not match boolean field value",
    ),
    QueryTestCase(
        id="decimal128_field_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}},
        doc=[{"_id": 1, "loc": Decimal128("42")}],
        expected=[],
        msg="Should not match Decimal128 field value",
    ),
    QueryTestCase(
        id="null_field_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}},
        doc=[{"_id": 1, "loc": None}, {"_id": 2, "loc": [0, 0]}],
        expected=[{"_id": 2, "loc": [0, 0]}],
        msg="Should not match document with null location field",
    ),
    QueryTestCase(
        id="missing_field_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 100]}}},
        doc=[{"_id": 1, "other": "value"}, {"_id": 2, "loc": [0, 0]}],
        expected=[{"_id": 2, "loc": [0, 0]}],
        msg="Should not match document with missing location field",
    ),
    QueryTestCase(
        id="embedded_xy_document",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[{"_id": 1, "loc": {"x": 0, "y": 0}}, {"_id": 2, "loc": {"x": 10, "y": 10}}],
        expected=[{"_id": 1, "loc": {"x": 0, "y": 0}}],
        msg="Should match embedded document with x/y fields",
    ),
    QueryTestCase(
        id="array_more_than_two_elements",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[{"_id": 1, "loc": [1, 1, 99]}, {"_id": 2, "loc": [10, 10, 0]}],
        expected=[{"_id": 1, "loc": [1, 1, 99]}],
        msg="Should use first 2 elements of array with more than 2 elements",
    ),
    QueryTestCase(
        id="nested_array_field",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[{"_id": 1, "loc": [[0, 0]]}, {"_id": 2, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [[0, 0]]}, {"_id": 2, "loc": [0, 0]}],
        msg="Should match array-of-arrays via multi-key expansion",
    ),
    QueryTestCase(
        id="empty_array_no_match",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
        doc=[{"_id": 1, "loc": []}, {"_id": 2, "loc": [0, 0]}],
        expected=[{"_id": 2, "loc": [0, 0]}],
        msg="Should not match document with empty array location field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_center_argument_handling(collection, test):
    """Verifies $center accepts valid argument structures and field formats."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
