"""
Tests for $all query operator data type coverage.

Validates $all matching with all BSON types, numeric equivalence,
BSON type distinction, special values, NaN handling, silent skip behavior,
and regex matching.

"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.codec_options import CodecOptions

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, FLOAT_NAN

BSON_TYPE_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_value",
        filter={"a": {"$all": ["hello"]}},
        doc=[{"_id": 1, "a": ["hello", "world"]}, {"_id": 2, "a": ["world"]}],
        expected=[{"_id": 1, "a": ["hello", "world"]}],
        msg="Should match array containing string value",
    ),
    QueryTestCase(
        id="integer_values",
        filter={"a": {"$all": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [1, 2, 3, 4]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [1, 2, 3, 4]}],
        msg="Should match array containing all integer values",
    ),
    QueryTestCase(
        id="long_value",
        filter={"a": {"$all": [Int64(1)]}},
        doc=[{"_id": 1, "a": [Int64(1), Int64(2)]}, {"_id": 2, "a": [Int64(3)]}],
        expected=[{"_id": 1, "a": [Int64(1), Int64(2)]}],
        msg="Should match array containing long value",
    ),
    QueryTestCase(
        id="double_values",
        filter={"a": {"$all": [1.5, 2.5]}},
        doc=[{"_id": 1, "a": [1.5, 2.5, 3.5]}, {"_id": 2, "a": [1.5]}],
        expected=[{"_id": 1, "a": [1.5, 2.5, 3.5]}],
        msg="Should match array containing all double values",
    ),
    QueryTestCase(
        id="decimal128_value",
        filter={"a": {"$all": [Decimal128("1.5")]}},
        doc=[{"_id": 1, "a": [Decimal128("1.5")]}, {"_id": 2, "a": [Decimal128("2.5")]}],
        expected=[{"_id": 1, "a": [Decimal128("1.5")]}],
        msg="Should match array containing decimal128 value",
    ),
    QueryTestCase(
        id="boolean_value",
        filter={"a": {"$all": [True]}},
        doc=[{"_id": 1, "a": [True, False]}, {"_id": 2, "a": [False]}],
        expected=[{"_id": 1, "a": [True, False]}],
        msg="Should match array containing boolean value",
    ),
    QueryTestCase(
        id="null_value",
        filter={"a": {"$all": [None]}},
        doc=[{"_id": 1, "a": [None, 1]}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": [None, 1]}],
        msg="Should match array containing null value",
    ),
    QueryTestCase(
        id="date_value",
        filter={"a": {"$all": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}},
        doc=[
            {"_id": 1, "a": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
            {"_id": 2, "a": [datetime(2025, 1, 1, tzinfo=timezone.utc)]},
        ],
        expected=[{"_id": 1, "a": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}],
        msg="Should match array containing date value",
    ),
    QueryTestCase(
        id="objectid_value",
        filter={"a": {"$all": [ObjectId("000000000000000000000001")]}},
        doc=[
            {"_id": 1, "a": [ObjectId("000000000000000000000001")]},
            {"_id": 2, "a": [ObjectId("000000000000000000000002")]},
        ],
        expected=[{"_id": 1, "a": [ObjectId("000000000000000000000001")]}],
        msg="Should match array containing objectId value",
    ),
    QueryTestCase(
        id="object_value",
        filter={"a": {"$all": [{"x": 1}]}},
        doc=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}, {"_id": 2, "a": [{"x": 2}]}],
        expected=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}],
        msg="Should match array containing object value",
    ),
    QueryTestCase(
        id="array_value",
        filter={"a": {"$all": [[1, 2, 3]]}},
        doc=[{"_id": 1, "a": [[1, 2, 3], "x"]}, {"_id": 2, "a": [[4, 5]]}],
        expected=[{"_id": 1, "a": [[1, 2, 3], "x"]}],
        msg="Should match array containing nested array value",
    ),
    QueryTestCase(
        id="bindata_value",
        filter={"a": {"$all": [Binary(b"\x01\x02")]}},
        doc=[{"_id": 1, "a": [Binary(b"\x01\x02")]}, {"_id": 2, "a": [Binary(b"\x03")]}],
        expected=[{"_id": 1, "a": [b"\x01\x02"]}],
        msg="Should match array containing binary data value",
    ),
    QueryTestCase(
        id="timestamp_value",
        filter={"a": {"$all": [Timestamp(1, 1)]}},
        doc=[{"_id": 1, "a": [Timestamp(1, 1)]}, {"_id": 2, "a": [Timestamp(2, 2)]}],
        expected=[{"_id": 1, "a": [Timestamp(1, 1)]}],
        msg="Should match array containing timestamp value",
    ),
    QueryTestCase(
        id="minkey_value",
        filter={"a": {"$all": [MinKey()]}},
        doc=[{"_id": 1, "a": [MinKey()]}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": [MinKey()]}],
        msg="Should match array containing MinKey value",
    ),
    QueryTestCase(
        id="maxkey_value",
        filter={"a": {"$all": [MaxKey()]}},
        doc=[{"_id": 1, "a": [MaxKey()]}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": [MaxKey()]}],
        msg="Should match array containing MaxKey value",
    ),
    QueryTestCase(
        id="regex_value",
        filter={"a": {"$all": [Regex("^x")]}},
        doc=[
            {"_id": 1, "a": ["xyz", "abc"]},
            {"_id": 2, "a": ["abc", "def"]},
        ],
        expected=[{"_id": 1, "a": ["xyz", "abc"]}],
        msg="Should match array containing element matching regex",
    ),
    QueryTestCase(
        id="code_value",
        filter={"a": {"$all": [Code("function(){}")]}},
        doc=[
            {"_id": 1, "a": [Code("function(){}")]},
            {"_id": 2, "a": ["function(){}"]},
        ],
        expected=[{"_id": 1, "a": [Code("function(){}")]}],
        msg="Should match array containing Code BSON type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSON_TYPE_VALUE_TESTS))
def test_all_bson_type_values(collection, test):
    """Test $all with various BSON types as values in the $all array."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter}, codec_options=codec
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)


SILENT_SKIP_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="field_is_boolean",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": True}],
        expected=[],
        msg="Boolean field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_objectid",
        filter={"a": {"$all": [1]}},
        doc=[{"_id": 1, "a": ObjectId()}],
        expected=[],
        msg="ObjectId field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_timestamp",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": Timestamp(1, 1)}],
        expected=[],
        msg="Timestamp field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_date",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected=[],
        msg="Date field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_object",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": {"k": "v"}}],
        expected=[],
        msg="Object field (not array) should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_minkey",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": MinKey()}],
        expected=[],
        msg="MinKey field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_maxkey",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": MaxKey()}],
        expected=[],
        msg="MaxKey field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_bindata",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": Binary(b"\x01")}],
        expected=[],
        msg="BinData field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_regex",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": Regex("pattern")}],
        expected=[],
        msg="Regex field should be silently excluded",
    ),
    QueryTestCase(
        id="field_is_javascript",
        filter={"a": {"$all": ["x"]}},
        doc=[{"_id": 1, "a": Code("return 1")}],
        expected=[],
        msg="JavaScript field should be silently excluded",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SILENT_SKIP_TESTS))
def test_all_silent_skip_non_matchable(collection, test):
    """Test $all silently excludes documents where field is a non-matchable type."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter}, codec_options=codec
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)


NUMERIC_EQUIVALENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_matches_double",
        filter={"a": {"$all": [1]}},
        doc=[{"_id": 1, "a": [1.0]}, {"_id": 2, "a": [2.0]}],
        expected=[{"_id": 1, "a": [1.0]}],
        msg="Int in $all should match double with same value",
    ),
    QueryTestCase(
        id="long_matches_int",
        filter={"a": {"$all": [Int64(1)]}},
        doc=[{"_id": 1, "a": [1]}, {"_id": 2, "a": [2]}],
        expected=[{"_id": 1, "a": [1]}],
        msg="Long in $all should match int with same value",
    ),
    QueryTestCase(
        id="decimal128_matches_int",
        filter={"a": {"$all": [Decimal128("1")]}},
        doc=[{"_id": 1, "a": [1]}, {"_id": 2, "a": [2]}],
        expected=[{"_id": 1, "a": [1]}],
        msg="Decimal128 in $all should match int with same value",
    ),
    QueryTestCase(
        id="zero_cross_type",
        filter={"a": {"$all": [0]}},
        doc=[
            {"_id": 1, "a": [Int64(0)]},
            {"_id": 2, "a": [0.0]},
            {"_id": 3, "a": [Decimal128("0")]},
            {"_id": 4, "a": [1]},
        ],
        expected=[
            {"_id": 1, "a": [Int64(0)]},
            {"_id": 2, "a": [0.0]},
            {"_id": 3, "a": [Decimal128("0")]},
        ],
        msg="Zero should match across all numeric types",
    ),
    QueryTestCase(
        id="negative_zero_matches_zero",
        filter={"a": {"$all": [-0.0]}},
        doc=[{"_id": 1, "a": [0.0]}, {"_id": 2, "a": [1.0]}],
        expected=[{"_id": 1, "a": [0.0]}],
        msg="Negative zero should match positive zero",
    ),
    QueryTestCase(
        id="decimal128_neg_zero_matches_zero",
        filter={"a": {"$all": [Decimal128("-0")]}},
        doc=[{"_id": 1, "a": [Decimal128("0")]}, {"_id": 2, "a": [Decimal128("1")]}],
        expected=[{"_id": 1, "a": [Decimal128("0")]}],
        msg="Decimal128 negative zero should match Decimal128 zero",
    ),
    QueryTestCase(
        id="cross_type_three_way",
        filter={"a": {"$all": [1, 2, 3]}},
        doc=[
            {"_id": 1, "a": [1.0, Int64(2), Decimal128("3")]},
            {"_id": 2, "a": [1.0, Int64(2)]},
        ],
        expected=[{"_id": 1, "a": [1.0, Int64(2), Decimal128("3")]}],
        msg="Int $all should match mixed double, long, and Decimal128 elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_EQUIVALENCE_TESTS))
def test_all_numeric_equivalence(collection, test):
    """Test $all cross-type numeric equivalence matching."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


BSON_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_not_zero",
        filter={"a": {"$all": [False]}},
        doc=[{"_id": 1, "a": [0]}, {"_id": 2, "a": [False]}],
        expected=[{"_id": 2, "a": [False]}],
        msg="$all [false] should NOT match field containing 0",
    ),
    QueryTestCase(
        id="true_not_one",
        filter={"a": {"$all": [True]}},
        doc=[{"_id": 1, "a": [1]}, {"_id": 2, "a": [True]}],
        expected=[{"_id": 2, "a": [True]}],
        msg="$all [true] should NOT match field containing 1",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSON_DISTINCTION_TESTS))
def test_all_bson_type_distinction(collection, test):
    """Test $all distinguishes between different BSON types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


SPECIAL_VALUE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="float_infinity",
        filter={"a": {"$all": [FLOAT_INFINITY]}},
        doc=[{"_id": 1, "a": [FLOAT_INFINITY]}, {"_id": 2, "a": [1.0]}],
        expected=[{"_id": 1, "a": [FLOAT_INFINITY]}],
        msg="$all with Infinity should match field containing Infinity",
    ),
    QueryTestCase(
        id="float_neg_infinity",
        filter={"a": {"$all": [float("-inf")]}},
        doc=[{"_id": 1, "a": [float("-inf")]}, {"_id": 2, "a": [1.0]}],
        expected=[{"_id": 1, "a": [float("-inf")]}],
        msg="$all with -Infinity should match field containing -Infinity",
    ),
    QueryTestCase(
        id="decimal128_infinity",
        filter={"a": {"$all": [Decimal128("Infinity")]}},
        doc=[{"_id": 1, "a": [Decimal128("Infinity")]}, {"_id": 2, "a": [Decimal128("1")]}],
        expected=[{"_id": 1, "a": [Decimal128("Infinity")]}],
        msg="$all with Decimal128 Infinity should match",
    ),
    QueryTestCase(
        id="decimal128_neg_infinity",
        filter={"a": {"$all": [Decimal128("-Infinity")]}},
        doc=[{"_id": 1, "a": [Decimal128("-Infinity")]}, {"_id": 2, "a": [Decimal128("1")]}],
        expected=[{"_id": 1, "a": [Decimal128("-Infinity")]}],
        msg="$all with Decimal128 -Infinity should match",
    ),
    QueryTestCase(
        id="cross_type_infinity",
        filter={"a": {"$all": [FLOAT_INFINITY]}},
        doc=[{"_id": 1, "a": [Decimal128("Infinity")]}, {"_id": 2, "a": [1.0]}],
        expected=[{"_id": 1, "a": [Decimal128("Infinity")]}],
        msg="Float Infinity should match Decimal128 Infinity",
    ),
    QueryTestCase(
        id="cross_type_neg_infinity",
        filter={"a": {"$all": [float("-inf")]}},
        doc=[{"_id": 1, "a": [Decimal128("-Infinity")]}, {"_id": 2, "a": [1.0]}],
        expected=[{"_id": 1, "a": [Decimal128("-Infinity")]}],
        msg="Float -Infinity should match Decimal128 -Infinity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPECIAL_VALUE_TESTS))
def test_all_special_values(collection, test):
    """Test $all with special values (Infinity)."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="float_nan",
        filter={"a": {"$all": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": [FLOAT_NAN]}, {"_id": 2, "a": [1.0]}],
        expected=[{"_id": 1, "a": [FLOAT_NAN]}],
        msg="$all with float NaN should match field containing NaN",
    ),
    QueryTestCase(
        id="decimal128_nan",
        filter={"a": {"$all": [Decimal128("NaN")]}},
        doc=[{"_id": 1, "a": [Decimal128("NaN")]}, {"_id": 2, "a": [Decimal128("1")]}],
        expected=[{"_id": 1, "a": [Decimal128("NaN")]}],
        msg="$all with Decimal128 NaN should match field containing Decimal128 NaN",
    ),
    QueryTestCase(
        id="cross_type_nan",
        filter={"a": {"$all": [FLOAT_NAN]}},
        doc=[{"_id": 1, "a": [Decimal128("NaN")]}, {"_id": 2, "a": [1.0]}],
        expected=[{"_id": 1, "a": [Decimal128("NaN")]}],
        msg="Float NaN in $all should match Decimal128 NaN in field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_TESTS))
def test_all_nan_values(collection, test):
    """Test $all with NaN values (require assertSuccessNaN)."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccessNaN(result, test.expected)


REGEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_regex",
        filter={"a": {"$all": [Regex("^abc")]}},
        doc=[{"_id": 1, "a": ["abcdef"]}, {"_id": 2, "a": ["xyz"]}],
        expected=[{"_id": 1, "a": ["abcdef"]}],
        msg="Regex in $all should match elements matching pattern",
    ),
    QueryTestCase(
        id="case_insensitive",
        filter={"a": {"$all": [Regex("^a", "i")]}},
        doc=[{"_id": 1, "a": ["Apple"]}, {"_id": 2, "a": ["banana"]}],
        expected=[{"_id": 1, "a": ["Apple"]}],
        msg="Case insensitive regex should match",
    ),
    QueryTestCase(
        id="regex_and_string",
        filter={"a": {"$all": [Regex("^a"), "abc"]}},
        doc=[
            {"_id": 1, "a": ["abc", "axyz"]},
            {"_id": 2, "a": ["axyz"]},
            {"_id": 3, "a": ["abc"]},
        ],
        expected=[{"_id": 1, "a": ["abc", "axyz"]}, {"_id": 3, "a": ["abc"]}],
        msg="Both regex and exact string must match",
    ),
    QueryTestCase(
        id="multiple_regexes",
        filter={"a": {"$all": [Regex("^a"), Regex("b$")]}},
        doc=[
            {"_id": 1, "a": ["abc", "xb"]},
            {"_id": 2, "a": ["abc"]},
            {"_id": 3, "a": ["xb"]},
        ],
        expected=[{"_id": 1, "a": ["abc", "xb"]}],
        msg="Multiple regexes should each need at least one matching element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REGEX_TESTS))
def test_all_regex(collection, test):
    """Test $all with regex values."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
