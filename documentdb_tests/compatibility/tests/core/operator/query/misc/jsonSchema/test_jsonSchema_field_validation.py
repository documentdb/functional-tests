"""
Tests for $jsonSchema type-specific validation keywords.

Validates string (minLength, maxLength, pattern), numeric (minimum, maximum,
exclusiveMinimum, exclusiveMaximum, multipleOf), and array (minItems, maxItems,
uniqueItems, items, additionalItems) constraint keywords against document field values.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
)

STRING_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_minLength_matches",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 3}}}},
        doc=[{"_id": 1, "x": "abc"}, {"_id": 2, "x": "ab"}, {"_id": 3, "x": "abcd"}],
        expected=[{"_id": 1, "x": "abc"}, {"_id": 3, "x": "abcd"}],
        msg="minLength should match strings with sufficient length",
    ),
    QueryTestCase(
        id="string_maxLength_matches",
        filter={"$jsonSchema": {"properties": {"x": {"maxLength": 5}}}},
        doc=[{"_id": 1, "x": "abcde"}, {"_id": 2, "x": "abcdef"}, {"_id": 3, "x": "ab"}],
        expected=[{"_id": 1, "x": "abcde"}, {"_id": 3, "x": "ab"}],
        msg="maxLength should match strings within length limit",
    ),
    QueryTestCase(
        id="string_minLength_zero_matches_empty",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 0}}}},
        doc=[{"_id": 1, "x": ""}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": ""}, {"_id": 2, "x": "a"}],
        msg="minLength 0 should match empty string",
    ),
    QueryTestCase(
        id="string_minLength_maxLength_zero_only_empty",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 0, "maxLength": 0}}}},
        doc=[{"_id": 1, "x": ""}, {"_id": 2, "x": "a"}],
        expected=[{"_id": 1, "x": ""}],
        msg="minLength 0 and maxLength 0 should match only empty string",
    ),
    QueryTestCase(
        id="string_minLength_non_string_passes",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 1}}}},
        doc=[{"_id": 1, "x": 42}, {"_id": 2, "x": "abc"}],
        expected=[{"_id": 1, "x": 42}, {"_id": 2, "x": "abc"}],
        msg="minLength on non-string field should pass",
    ),
    QueryTestCase(
        id="string_pattern_prefix",
        filter={"$jsonSchema": {"properties": {"x": {"pattern": "^abc"}}}},
        doc=[{"_id": 1, "x": "abcdef"}, {"_id": 2, "x": "xyzabc"}],
        expected=[{"_id": 1, "x": "abcdef"}],
        msg="Pattern with ^ prefix should match strings starting with pattern",
    ),
    QueryTestCase(
        id="string_pattern_digits",
        filter={"$jsonSchema": {"properties": {"x": {"pattern": "[0-9]+"}}}},
        doc=[{"_id": 1, "x": "test123"}, {"_id": 2, "x": "test"}],
        expected=[{"_id": 1, "x": "test123"}],
        msg="Pattern with digit regex should match strings containing digits",
    ),
    QueryTestCase(
        id="string_pattern_non_string_passes",
        filter={"$jsonSchema": {"properties": {"x": {"pattern": "abc"}}}},
        doc=[{"_id": 1, "x": {"a": 1}}, {"_id": 2, "x": "abc"}],
        expected=[{"_id": 1, "x": {"a": 1}}, {"_id": 2, "x": "abc"}],
        msg="Pattern on non-string field should pass",
    ),
    QueryTestCase(
        id="string_pattern_empty_matches_all",
        filter={"$jsonSchema": {"properties": {"x": {"pattern": ""}}}},
        doc=[{"_id": 1, "x": "abc"}, {"_id": 2, "x": ""}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": "abc"}, {"_id": 2, "x": ""}, {"_id": 3, "x": 42}],
        msg="Empty pattern should match all strings",
    ),
    QueryTestCase(
        id="string_pattern_exact_empty",
        filter={"$jsonSchema": {"properties": {"x": {"pattern": "^$"}}}},
        doc=[{"_id": 1, "x": ""}, {"_id": 2, "x": "a"}, {"_id": 3, "x": 42}],
        expected=[{"_id": 1, "x": ""}, {"_id": 3, "x": 42}],
        msg="Pattern ^$ should match only empty string",
    ),
    QueryTestCase(
        id="string_pattern_dot_matches_any",
        filter={"$jsonSchema": {"properties": {"x": {"pattern": "a.b"}}}},
        doc=[{"_id": 1, "x": "axb"}, {"_id": 2, "x": "ab"}, {"_id": 3, "x": "a.b"}],
        expected=[{"_id": 1, "x": "axb"}, {"_id": 3, "x": "a.b"}],
        msg="Pattern with dot should match any character",
    ),
    QueryTestCase(
        id="string_combined_constraints",
        filter={
            "$jsonSchema": {
                "properties": {"x": {"minLength": 3, "maxLength": 5, "pattern": "^[a-c]+"}}
            }
        },
        doc=[
            {"_id": 1, "x": "abc"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "abcdefghij"},
            {"_id": 4, "x": "xyz"},
        ],
        expected=[{"_id": 1, "x": "abc"}],
        msg="Combined minLength, maxLength, and pattern should all apply",
    ),
    QueryTestCase(
        id="string_missing_field_passes",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 1}}}},
        doc=[{"_id": 1, "x": "abc"}, {"_id": 2}],
        expected=[{"_id": 1, "x": "abc"}, {"_id": 2}],
        msg="String keywords should pass when field is missing",
    ),
    QueryTestCase(
        id="string_minLength_large_rejects_all",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 999999}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": ""}],
        expected=[],
        msg="minLength with huge value should reject all strings",
    ),
    QueryTestCase(
        id="string_maxLength_large_accepts_all",
        filter={"$jsonSchema": {"properties": {"x": {"maxLength": 999999}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": ""}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": ""}],
        msg="maxLength with huge value should accept all strings",
    ),
    QueryTestCase(
        id="string_minLength_unicode",
        filter={"$jsonSchema": {"properties": {"x": {"minLength": 2}}}},
        doc=[{"_id": 1, "x": "\u65e5\u672c"}, {"_id": 2, "x": "\u65e5"}],
        expected=[{"_id": 1, "x": "\u65e5\u672c"}],
        msg="minLength should count code points not bytes",
    ),
    QueryTestCase(
        id="string_maxLength_unicode",
        filter={"$jsonSchema": {"properties": {"x": {"maxLength": 2}}}},
        doc=[{"_id": 1, "x": "\u65e5\u672c"}, {"_id": 2, "x": "\u65e5\u672c\u8a9e"}],
        expected=[{"_id": 1, "x": "\u65e5\u672c"}],
        msg="maxLength should count code points not bytes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STRING_VALIDATION_TESTS))
def test_jsonSchema_string_validation(collection, test):
    """Test $jsonSchema string validation keywords."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


NUMERIC_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_minimum_inclusive",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
        doc=[{"_id": 1, "x": 5}, {"_id": 2, "x": 4}, {"_id": 3, "x": 6}],
        expected=[{"_id": 1, "x": 5}, {"_id": 3, "x": 6}],
        msg="Minimum should be inclusive",
    ),
    QueryTestCase(
        id="numeric_maximum_inclusive",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": 10}}}},
        doc=[{"_id": 1, "x": 10}, {"_id": 2, "x": 11}, {"_id": 3, "x": 9}],
        expected=[{"_id": 1, "x": 10}, {"_id": 3, "x": 9}],
        msg="Maximum should be inclusive",
    ),
    QueryTestCase(
        id="numeric_minimum_with_long",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
        doc=[{"_id": 1, "x": Int64(100)}, {"_id": 2, "x": Int64(4)}],
        expected=[{"_id": 1, "x": Int64(100)}],
        msg="Minimum should work with Int64 values",
    ),
    QueryTestCase(
        id="numeric_minimum_with_double",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
        doc=[{"_id": 1, "x": 5.5}, {"_id": 2, "x": 4.9}],
        expected=[{"_id": 1, "x": 5.5}],
        msg="Minimum should work with double values",
    ),
    QueryTestCase(
        id="numeric_minimum_with_decimal128",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
        doc=[{"_id": 1, "x": Decimal128("10.5")}, {"_id": 2, "x": Decimal128("3.2")}],
        expected=[{"_id": 1, "x": Decimal128("10.5")}],
        msg="Minimum should work with Decimal128 values",
    ),
    QueryTestCase(
        id="numeric_cross_type_minimum_decimal_with_int",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": DECIMAL128_TRAILING_ZERO}}}},
        doc=[{"_id": 1, "x": 5}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": 5}],
        msg="Minimum as Decimal128 should match int values",
    ),
    QueryTestCase(
        id="numeric_exclusive_minimum",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5, "exclusiveMinimum": True}}}},
        doc=[{"_id": 1, "x": 5}, {"_id": 2, "x": 6}, {"_id": 3, "x": 4}],
        expected=[{"_id": 2, "x": 6}],
        msg="exclusiveMinimum true should exclude boundary value",
    ),
    QueryTestCase(
        id="numeric_exclusive_maximum",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": 10, "exclusiveMaximum": True}}}},
        doc=[{"_id": 1, "x": 10}, {"_id": 2, "x": 9}, {"_id": 3, "x": 11}],
        expected=[{"_id": 2, "x": 9}],
        msg="exclusiveMaximum true should exclude boundary value",
    ),
    QueryTestCase(
        id="numeric_exclusive_minimum_false",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5, "exclusiveMinimum": False}}}},
        doc=[{"_id": 1, "x": 5}, {"_id": 2, "x": 4}],
        expected=[{"_id": 1, "x": 5}],
        msg="exclusiveMinimum false should be same as default inclusive",
    ),
    QueryTestCase(
        id="numeric_exclusive_maximum_false",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": 10, "exclusiveMaximum": False}}}},
        doc=[{"_id": 1, "x": 10}, {"_id": 2, "x": 11}],
        expected=[{"_id": 1, "x": 10}],
        msg="exclusiveMaximum false should be same as default inclusive",
    ),
    QueryTestCase(
        id="numeric_multipleOf_matches",
        filter={"$jsonSchema": {"properties": {"x": {"multipleOf": 3}}}},
        doc=[{"_id": 1, "x": 9}, {"_id": 2, "x": 10}, {"_id": 3, "x": 12}],
        expected=[{"_id": 1, "x": 9}, {"_id": 3, "x": 12}],
        msg="multipleOf should match multiples and reject non-multiples",
    ),
    QueryTestCase(
        id="numeric_minimum_non_numeric_passes",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 10}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 10}],
        msg="Minimum on non-numeric field should pass",
    ),
    QueryTestCase(
        id="numeric_maximum_non_numeric_passes",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": 10}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 3}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": 3}],
        msg="Maximum on non-numeric field should pass",
    ),
    QueryTestCase(
        id="numeric_multipleOf_non_numeric_passes",
        filter={"$jsonSchema": {"properties": {"x": {"multipleOf": 3}}}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": 6}],
        expected=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": 6}],
        msg="multipleOf on non-numeric field should pass",
    ),
    QueryTestCase(
        id="numeric_minimum_maximum_range",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 0, "maximum": 100}}}},
        doc=[
            {"_id": 1, "x": -1},
            {"_id": 2, "x": 0},
            {"_id": 3, "x": 50},
            {"_id": 4, "x": 100},
            {"_id": 5, "x": 101},
        ],
        expected=[{"_id": 2, "x": 0}, {"_id": 3, "x": 50}, {"_id": 4, "x": 100}],
        msg="Minimum and maximum together should validate range",
    ),
    QueryTestCase(
        id="numeric_missing_field_passes",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 5}}}},
        doc=[{"_id": 1, "x": 10}, {"_id": 2}],
        expected=[{"_id": 1, "x": 10}, {"_id": 2}],
        msg="Numeric keywords should pass when field is missing",
    ),
    QueryTestCase(
        id="numeric_minimum_negative",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": -1}}}},
        doc=[{"_id": 1, "x": 0}, {"_id": 2, "x": -2}, {"_id": 3, "x": -1}],
        expected=[{"_id": 1, "x": 0}, {"_id": 3, "x": -1}],
        msg="Minimum with negative value should work",
    ),
    QueryTestCase(
        id="numeric_maximum_negative",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": -1}}}},
        doc=[{"_id": 1, "x": 0}, {"_id": 2, "x": -2}, {"_id": 3, "x": -1}],
        expected=[{"_id": 2, "x": -2}, {"_id": 3, "x": -1}],
        msg="Maximum with negative value should work",
    ),
    QueryTestCase(
        id="numeric_minimum_large_rejects_all",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": INT64_MAX}}}},
        doc=[{"_id": 1, "x": 999999}, {"_id": 2, "x": 0}],
        expected=[],
        msg="Minimum with INT64_MAX should reject normal values",
    ),
    QueryTestCase(
        id="numeric_maximum_large_accepts_below",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": INT64_MAX}}}},
        doc=[{"_id": 1, "x": 999999}, {"_id": 2, "x": 0}],
        expected=[{"_id": 1, "x": 999999}, {"_id": 2, "x": 0}],
        msg="Maximum with INT64_MAX should accept normal values",
    ),
    QueryTestCase(
        id="numeric_multipleOf_decimal",
        filter={"$jsonSchema": {"properties": {"x": {"multipleOf": 0.1}}}},
        doc=[{"_id": 1, "x": 0.3}, {"_id": 2, "x": 0.5}],
        expected=[{"_id": 1, "x": 0.3}, {"_id": 2, "x": 0.5}],
        msg="multipleOf with decimal value should work",
    ),
    QueryTestCase(
        id="numeric_minimum_nan_field",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 0}}}},
        doc=[{"_id": 1, "x": FLOAT_NAN}, {"_id": 2, "x": DECIMAL128_NAN}, {"_id": 3, "x": 1}],
        expected=[{"_id": 3, "x": 1}],
        msg="NaN fields (float and decimal) should not satisfy minimum",
    ),
    QueryTestCase(
        id="numeric_maximum_nan_field",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": 100}}}},
        doc=[{"_id": 1, "x": FLOAT_NAN}, {"_id": 2, "x": DECIMAL128_NAN}, {"_id": 3, "x": 1}],
        expected=[{"_id": 3, "x": 1}],
        msg="NaN fields (float and decimal) should not satisfy maximum",
    ),
    QueryTestCase(
        id="numeric_minimum_infinity_field",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 0}}}},
        doc=[
            {"_id": 1, "x": FLOAT_INFINITY},
            {"_id": 2, "x": FLOAT_NEGATIVE_INFINITY},
            {"_id": 3, "x": DECIMAL128_INFINITY},
            {"_id": 4, "x": DECIMAL128_NEGATIVE_INFINITY},
        ],
        expected=[{"_id": 1, "x": FLOAT_INFINITY}, {"_id": 3, "x": DECIMAL128_INFINITY}],
        msg="Infinity should satisfy minimum, -Infinity should not (float and decimal)",
    ),
    QueryTestCase(
        id="numeric_maximum_infinity_field",
        filter={"$jsonSchema": {"properties": {"x": {"maximum": 0}}}},
        doc=[
            {"_id": 1, "x": FLOAT_NEGATIVE_INFINITY},
            {"_id": 2, "x": FLOAT_INFINITY},
            {"_id": 3, "x": DECIMAL128_NEGATIVE_INFINITY},
            {"_id": 4, "x": DECIMAL128_INFINITY},
        ],
        expected=[
            {"_id": 1, "x": FLOAT_NEGATIVE_INFINITY},
            {"_id": 3, "x": DECIMAL128_NEGATIVE_INFINITY},
        ],
        msg="-Infinity should satisfy maximum 0, Infinity should not (float and decimal)",
    ),
    QueryTestCase(
        id="numeric_minimum_negative_zero",
        filter={"$jsonSchema": {"properties": {"x": {"minimum": 0}}}},
        doc=[
            {"_id": 1, "x": DOUBLE_NEGATIVE_ZERO},
            {"_id": 2, "x": DOUBLE_ZERO},
            {"_id": 3, "x": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 4, "x": DECIMAL128_ZERO},
        ],
        expected=[
            {"_id": 1, "x": DOUBLE_NEGATIVE_ZERO},
            {"_id": 2, "x": DOUBLE_ZERO},
            {"_id": 3, "x": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 4, "x": DECIMAL128_ZERO},
        ],
        msg="-0.0 and 0.0 should both satisfy minimum 0 (float and decimal)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_VALIDATION_TESTS))
def test_jsonSchema_numeric_validation(collection, test):
    """Test $jsonSchema numeric validation keywords."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)


ARRAY_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_minItems_matches",
        filter={"$jsonSchema": {"properties": {"x": {"minItems": 2}}}},
        doc=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": [1]}],
        expected=[{"_id": 1, "x": [1, 2, 3]}],
        msg="minItems should match arrays with sufficient elements",
    ),
    QueryTestCase(
        id="array_maxItems_matches",
        filter={"$jsonSchema": {"properties": {"x": {"maxItems": 3}}}},
        doc=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": [1, 2, 3, 4]}],
        expected=[{"_id": 1, "x": [1, 2, 3]}],
        msg="maxItems should match arrays within limit",
    ),
    QueryTestCase(
        id="array_minItems_zero_matches_empty",
        filter={"$jsonSchema": {"properties": {"x": {"minItems": 0}}}},
        doc=[{"_id": 1, "x": []}, {"_id": 2, "x": [1]}],
        expected=[{"_id": 1, "x": []}, {"_id": 2, "x": [1]}],
        msg="minItems 0 should match empty array",
    ),
    QueryTestCase(
        id="array_minItems_maxItems_zero_only_empty",
        filter={"$jsonSchema": {"properties": {"x": {"minItems": 0, "maxItems": 0}}}},
        doc=[{"_id": 1, "x": []}, {"_id": 2, "x": [1]}],
        expected=[{"_id": 1, "x": []}],
        msg="minItems 0 and maxItems 0 should match only empty array",
    ),
    QueryTestCase(
        id="array_minItems_non_array_passes",
        filter={"$jsonSchema": {"properties": {"x": {"minItems": 1}}}},
        doc=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": [1, 2]}],
        expected=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": [1, 2]}],
        msg="minItems on non-array field should pass",
    ),
    QueryTestCase(
        id="array_minItems_missing_field_passes",
        filter={"$jsonSchema": {"properties": {"x": {"minItems": 1}}}},
        doc=[{"_id": 1, "x": [1, 2]}, {"_id": 2}],
        expected=[{"_id": 1, "x": [1, 2]}, {"_id": 2}],
        msg="minItems should pass when field is missing",
    ),
    QueryTestCase(
        id="array_uniqueItems_true_matches",
        filter={"$jsonSchema": {"properties": {"x": {"uniqueItems": True}}}},
        doc=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": [1, 1, 2]}],
        expected=[{"_id": 1, "x": [1, 2, 3]}],
        msg="uniqueItems true should match arrays with all distinct elements",
    ),
    QueryTestCase(
        id="array_uniqueItems_false_allows_duplicates",
        filter={"$jsonSchema": {"properties": {"x": {"uniqueItems": False}}}},
        doc=[{"_id": 1, "x": [1, 1, 2]}, {"_id": 2, "x": [1, 2]}],
        expected=[{"_id": 1, "x": [1, 1, 2]}, {"_id": 2, "x": [1, 2]}],
        msg="uniqueItems false should allow arrays with duplicates",
    ),
    QueryTestCase(
        id="array_uniqueItems_null_duplicates",
        filter={"$jsonSchema": {"properties": {"x": {"uniqueItems": True}}}},
        doc=[{"_id": 1, "x": [None, None]}, {"_id": 2, "x": [None, 1]}],
        expected=[{"_id": 2, "x": [None, 1]}],
        msg="uniqueItems true should reject [null, null]",
    ),
    QueryTestCase(
        id="array_uniqueItems_zero_false_distinct",
        filter={"$jsonSchema": {"properties": {"x": {"uniqueItems": True}}}},
        doc=[{"_id": 1, "x": [0, False]}, {"_id": 2, "x": [0, 0]}],
        expected=[{"_id": 1, "x": [0, False]}],
        msg="uniqueItems true with [0, false] — distinct BSON types are unique",
    ),
    QueryTestCase(
        id="array_uniqueItems_cross_type_numeric",
        filter={"$jsonSchema": {"properties": {"x": {"uniqueItems": True}}}},
        doc=[{"_id": 1, "x": [1, Int64(1)]}, {"_id": 2, "x": [1, Int64(2)]}],
        expected=[{"_id": 2, "x": [1, Int64(2)]}],
        msg="uniqueItems should treat NumberInt(1) and NumberLong(1) as equivalent",
    ),
    QueryTestCase(
        id="array_uniqueItems_non_array_passes",
        filter={"$jsonSchema": {"properties": {"x": {"uniqueItems": True}}}},
        doc=[{"_id": 1, "x": 42}, {"_id": 2, "x": [1, 1]}],
        expected=[{"_id": 1, "x": 42}],
        msg="uniqueItems on non-array field should pass",
    ),
    QueryTestCase(
        id="array_items_schema_matches",
        filter={"$jsonSchema": {"properties": {"x": {"items": {"bsonType": "int"}}}}},
        doc=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": [1, "two", 3]}],
        expected=[{"_id": 1, "x": [1, 2, 3]}],
        msg="items with schema should validate all array elements",
    ),
    QueryTestCase(
        id="array_items_empty_array_passes",
        filter={"$jsonSchema": {"properties": {"x": {"items": {"bsonType": "string"}}}}},
        doc=[{"_id": 1, "x": []}, {"_id": 2, "x": [1]}],
        expected=[{"_id": 1, "x": []}],
        msg="items on empty array should pass (vacuously true)",
    ),
    QueryTestCase(
        id="array_items_tuple_validation",
        filter={
            "$jsonSchema": {
                "properties": {"x": {"items": [{"bsonType": "string"}, {"bsonType": "int"}]}}
            }
        },
        doc=[{"_id": 1, "x": ["hello", 42]}, {"_id": 2, "x": [42, "hello"]}],
        expected=[{"_id": 1, "x": ["hello", 42]}],
        msg="items with array of schemas should do tuple validation",
    ),
    QueryTestCase(
        id="array_items_tuple_shorter_array_passes",
        filter={
            "$jsonSchema": {
                "properties": {"x": {"items": [{"bsonType": "string"}, {"bsonType": "int"}]}}
            }
        },
        doc=[{"_id": 1, "x": ["hello"]}, {"_id": 2, "x": [42]}],
        expected=[{"_id": 1, "x": ["hello"]}],
        msg="Tuple items with shorter array should pass",
    ),
    QueryTestCase(
        id="array_additionalItems_false_rejects_extra",
        filter={
            "$jsonSchema": {
                "properties": {"x": {"items": [{"bsonType": "string"}], "additionalItems": False}}
            }
        },
        doc=[{"_id": 1, "x": ["hello"]}, {"_id": 2, "x": ["hello", 42]}],
        expected=[{"_id": 1, "x": ["hello"]}],
        msg="additionalItems false should reject extra elements",
    ),
    QueryTestCase(
        id="array_additionalItems_true_allows_extra",
        filter={
            "$jsonSchema": {
                "properties": {"x": {"items": [{"bsonType": "string"}], "additionalItems": True}}
            }
        },
        doc=[{"_id": 1, "x": ["hello", 42]}, {"_id": 2, "x": ["hello"]}],
        expected=[{"_id": 1, "x": ["hello", 42]}, {"_id": 2, "x": ["hello"]}],
        msg="additionalItems true should allow extra elements",
    ),
    QueryTestCase(
        id="array_additionalItems_schema_validates_extra",
        filter={
            "$jsonSchema": {
                "properties": {
                    "x": {"items": [{"bsonType": "string"}], "additionalItems": {"bsonType": "int"}}
                }
            }
        },
        doc=[{"_id": 1, "x": ["hello", 42]}, {"_id": 2, "x": ["hello", "extra"]}],
        expected=[{"_id": 1, "x": ["hello", 42]}],
        msg="additionalItems as schema should validate extra elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_VALIDATION_TESTS))
def test_jsonSchema_array_validation(collection, test):
    """Test $jsonSchema array validation keywords."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected)
