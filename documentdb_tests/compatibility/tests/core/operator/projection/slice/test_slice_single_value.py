"""Tests for $slice projection: single value form, null/missing fields, type preservation.

Tests basic $slice with single integer, behavior on non-array fields, and BSON type handling.
"""

import pytest
from bson import Binary, Code, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DECIMAL128_HALF,
    INT32_MAX,
    INT64_MAX,
    OID_EPOCH,
    TS_EPOCH,
)

SINGLE_NUMBER_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "positive_slice_1",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["a"]}],
        msg="$slice: 1 should return first element",
    ),
    ProjectionTestCase(
        "positive_slice_2",
        projection={"arr": {"$slice": 2}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["a", "b"]}],
        msg="$slice: 2 should return first 2 elements",
    ),
    ProjectionTestCase(
        "positive_3_first_n",
        projection={"arr": {"$slice": 3}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$slice: 3 should return first 3 elements of 11-element array",
    ),
    ProjectionTestCase(
        "negative_slice_1",
        projection={"arr": {"$slice": -1}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["c"]}],
        msg="$slice: -1 should return last element",
    ),
    ProjectionTestCase(
        "negative_slice_2",
        projection={"arr": {"$slice": -2}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["b", "c"]}],
        msg="$slice: -2 should return last 2 elements",
    ),
    ProjectionTestCase(
        "negative_3_last_n",
        projection={"arr": {"$slice": -3}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}],
        expected=[{"_id": 1, "arr": [9, 10, 11]}],
        msg="$slice: -3 should return last 3 elements of 11-element array",
    ),
    ProjectionTestCase(
        "zero",
        projection={"arr": {"$slice": 0}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: 0 should return empty array",
    ),
    ProjectionTestCase(
        "positive_exceeds_length",
        projection={"arr": {"$slice": 5}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["a", "b", "c"]}],
        msg="$slice exceeding array length should return all elements",
    ),
    ProjectionTestCase(
        "negative_exceeds_length",
        projection={"arr": {"$slice": -5}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["a", "b", "c"]}],
        msg="$slice negative exceeding array length should return all elements",
    ),
    ProjectionTestCase(
        "positive_equals_length",
        projection={"arr": {"$slice": 3}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["a", "b", "c"]}],
        msg="$slice equal to array length should return all elements",
    ),
    ProjectionTestCase(
        "negative_equals_length",
        projection={"arr": {"$slice": -3}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["a", "b", "c"]}],
        msg="$slice negative equal to array length should return all elements",
    ),
    ProjectionTestCase(
        "single_element_positive",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": ["x"]}],
        expected=[{"_id": 1, "arr": ["x"]}],
        msg="$slice: 1 on single-element array should return that element",
    ),
    ProjectionTestCase(
        "single_element_negative",
        projection={"arr": {"$slice": -1}},
        doc=[{"_id": 1, "arr": ["x"]}],
        expected=[{"_id": 1, "arr": ["x"]}],
        msg="$slice: -1 on single-element array should return that element",
    ),
    ProjectionTestCase(
        "empty_array",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": []}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice on empty array should return empty array",
    ),
    ProjectionTestCase(
        "empty_array_negative",
        projection={"arr": {"$slice": -1}},
        doc=[{"_id": 1, "arr": []}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: -1 on empty array should return empty array",
    ),
]

NON_ARRAY_FIELD_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "field_is_null",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": None}],
        expected=[{"_id": 1, "arr": None}],
        msg="$slice on null field should return null",
    ),
    ProjectionTestCase(
        "field_missing",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "other": "value"}],
        expected=[{"_id": 1, "other": "value"}],
        msg="$slice on missing field should omit field from result",
    ),
    ProjectionTestCase(
        "field_is_integer",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": 42}],
        expected=[{"_id": 1, "arr": 42}],
        msg="$slice on integer field should return the scalar unchanged",
    ),
    ProjectionTestCase(
        "field_is_string",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": "hello"}],
        expected=[{"_id": 1, "arr": "hello"}],
        msg="$slice on string field should return the string unchanged",
    ),
    ProjectionTestCase(
        "field_is_embedded_document",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": {"nested": "doc"}}],
        expected=[{"_id": 1, "arr": {"nested": "doc"}}],
        msg="$slice on embedded document should return unchanged",
    ),
    ProjectionTestCase(
        "field_is_boolean",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": True}],
        expected=[{"_id": 1, "arr": True}],
        msg="$slice on boolean field should return the boolean unchanged",
    ),
]

TYPE_PRESERVATION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "type_int32",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", INT32_MAX, "end"]}],
        expected=[{"_id": 1, "arr": [INT32_MAX]}],
        msg="$slice preserves int32 elements",
    ),
    ProjectionTestCase(
        "type_int64",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", INT64_MAX, "end"]}],
        expected=[{"_id": 1, "arr": [INT64_MAX]}],
        msg="$slice preserves int64 elements",
    ),
    ProjectionTestCase(
        "type_double",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", 3.14, "end"]}],
        expected=[{"_id": 1, "arr": [3.14]}],
        msg="$slice preserves double elements",
    ),
    ProjectionTestCase(
        "type_decimal128",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", DECIMAL128_HALF, "end"]}],
        expected=[{"_id": 1, "arr": [DECIMAL128_HALF]}],
        msg="$slice preserves Decimal128 elements",
    ),
    ProjectionTestCase(
        "type_string",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", "hello", "end"]}],
        expected=[{"_id": 1, "arr": ["hello"]}],
        msg="$slice preserves string elements",
    ),
    ProjectionTestCase(
        "type_boolean",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", True, "end"]}],
        expected=[{"_id": 1, "arr": [True]}],
        msg="$slice preserves boolean elements",
    ),
    ProjectionTestCase(
        "type_date",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", DATE_EPOCH, "end"]}],
        expected=[{"_id": 1, "arr": [DATE_EPOCH]}],
        msg="$slice preserves date elements",
    ),
    ProjectionTestCase(
        "type_null",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", None, "end"]}],
        expected=[{"_id": 1, "arr": [None]}],
        msg="$slice preserves null elements",
    ),
    ProjectionTestCase(
        "type_object_id",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", OID_EPOCH, "end"]}],
        expected=[{"_id": 1, "arr": [OID_EPOCH]}],
        msg="$slice preserves ObjectId elements",
    ),
    ProjectionTestCase(
        "type_embedded_doc",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", {"a": 1, "b": "x"}, "end"]}],
        expected=[{"_id": 1, "arr": [{"a": 1, "b": "x"}]}],
        msg="$slice preserves embedded document elements",
    ),
    ProjectionTestCase(
        "type_nested_array",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", [1, 2, 3], "end"]}],
        expected=[{"_id": 1, "arr": [[1, 2, 3]]}],
        msg="$slice preserves nested array elements",
    ),
    ProjectionTestCase(
        "type_binary",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", Binary(b"\x00\x01\x02"), "end"]}],
        expected=[{"_id": 1, "arr": [b"\x00\x01\x02"]}],
        msg="$slice preserves binary elements",
    ),
    ProjectionTestCase(
        "type_regex",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", Regex("^abc", "i"), "end"]}],
        expected=[{"_id": 1, "arr": [Regex("^abc", "i")]}],
        msg="$slice preserves regex elements",
    ),
    ProjectionTestCase(
        "type_timestamp",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", TS_EPOCH, "end"]}],
        expected=[{"_id": 1, "arr": [TS_EPOCH]}],
        msg="$slice preserves timestamp elements",
    ),
    ProjectionTestCase(
        "type_javascript",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", Code("function(){}"), "end"]}],
        expected=[{"_id": 1, "arr": [Code("function(){}")]}],
        msg="$slice preserves JavaScript elements",
    ),
    ProjectionTestCase(
        "type_min_key",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", MinKey(), "end"]}],
        expected=[{"_id": 1, "arr": [MinKey()]}],
        msg="$slice preserves MinKey elements",
    ),
    ProjectionTestCase(
        "type_max_key",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["padding", MaxKey(), "end"]}],
        expected=[{"_id": 1, "arr": [MaxKey()]}],
        msg="$slice preserves MaxKey elements",
    ),
    ProjectionTestCase(
        "preserves_element_order",
        projection={"arr": {"$slice": 3}},
        doc=[{"_id": 1, "arr": [5, 3, 1, 4, 2]}],
        expected=[{"_id": 1, "arr": [5, 3, 1]}],
        msg="$slice should preserve original element order",
    ),
    ProjectionTestCase(
        "preserves_mixed_types",
        projection={"arr": {"$slice": 4}},
        doc=[{"_id": 1, "arr": [1, "two", 3.0, True, None, {"k": "v"}, [7, 8]]}],
        expected=[{"_id": 1, "arr": [1, "two", 3.0, True]}],
        msg="$slice on mixed-type array should preserve types and order",
    ),
]

ALL_TESTS = SINGLE_NUMBER_TESTS + NON_ARRAY_FIELD_TESTS + TYPE_PRESERVATION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_slice_single_value(collection, test: ProjectionTestCase):
    """Test $slice with single value form, null/missing fields, and type preservation."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "projection": test.projection},
    )
    assertSuccess(result, test.expected, msg=test.msg)
