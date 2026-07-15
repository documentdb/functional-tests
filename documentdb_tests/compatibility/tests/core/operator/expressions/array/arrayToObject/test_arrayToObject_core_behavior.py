"""
Core behavior tests for $arrayToObject expression.

Tests both input forms (k/v documents and two-element arrays), empty arrays,
duplicate keys, format equivalence, field ordering, case sensitivity,
value edge cases, key edge cases, and large inputs.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params

# Property [K/V Form]: $arrayToObject builds an object from {k, v} document entries.
KV_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="kv_single_pair",
        doc={"arr": [{"k": "a", "v": 1}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 1},
        msg="$arrayToObject should convert single k/v pair",
    ),
    ExpressionTestCase(
        id="kv_multiple_pairs",
        doc={"arr": [{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 1, "b": 2, "c": 3},
        msg="$arrayToObject should convert multiple k/v pairs",
    ),
    ExpressionTestCase(
        id="kv_string_values",
        doc={"arr": [{"k": "name", "v": "Alice"}, {"k": "city", "v": "Mycity"}]},
        expression={"$arrayToObject": "$arr"},
        expected={"name": "Alice", "city": "Mycity"},
        msg="$arrayToObject should convert k/v pairs with string values",
    ),
    ExpressionTestCase(
        id="kv_mixed_value_types",
        doc={
            "arr": [
                {"k": "int", "v": 1},
                {"k": "str", "v": "hello"},
                {"k": "bool", "v": True},
                {"k": "null", "v": None},
            ]
        },
        expression={"$arrayToObject": "$arr"},
        expected={"int": 1, "str": "hello", "bool": True, "null": None},
        msg="$arrayToObject should convert k/v pairs with mixed value types",
    ),
    ExpressionTestCase(
        id="kv_nested_object_value",
        doc={"arr": [{"k": "obj", "v": {"x": 1, "y": 2}}]},
        expression={"$arrayToObject": "$arr"},
        expected={"obj": {"x": 1, "y": 2}},
        msg="$arrayToObject should convert k/v pair with nested object value",
    ),
    ExpressionTestCase(
        id="kv_array_value",
        doc={"arr": [{"k": "arr", "v": [1, 2, 3]}]},
        expression={"$arrayToObject": "$arr"},
        expected={"arr": [1, 2, 3]},
        msg="$arrayToObject should convert k/v pair with array value",
    ),
]

# Property [Pair Form]: $arrayToObject builds an object from two-element [key, value] arrays.
TWO_ELEM_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="pair_single",
        doc={"arr": [["a", 1]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 1},
        msg="$arrayToObject should convert single two-element pair",
    ),
    ExpressionTestCase(
        id="pair_multiple",
        doc={"arr": [["a", 1], ["b", 2], ["c", 3]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 1, "b": 2, "c": 3},
        msg="$arrayToObject should convert multiple two-element pairs",
    ),
    ExpressionTestCase(
        id="pair_string_values",
        doc={"arr": [["name", "Alice"], ["city", "Mycity"]]},
        expression={"$arrayToObject": "$arr"},
        expected={"name": "Alice", "city": "Mycity"},
        msg="$arrayToObject should convert pairs with string values",
    ),
    ExpressionTestCase(
        id="pair_mixed_value_types",
        doc={"arr": [["int", 1], ["str", "hello"], ["bool", True], ["null", None]]},
        expression={"$arrayToObject": "$arr"},
        expected={"int": 1, "str": "hello", "bool": True, "null": None},
        msg="$arrayToObject should convert pairs with mixed value types",
    ),
    ExpressionTestCase(
        id="pair_nested_object_value",
        doc={"arr": [["obj", {"x": 1, "y": 2}]]},
        expression={"$arrayToObject": "$arr"},
        expected={"obj": {"x": 1, "y": 2}},
        msg="$arrayToObject should convert pair with nested object value",
    ),
    ExpressionTestCase(
        id="pair_array_value",
        doc={"arr": [["arr", [1, 2, 3]]]},
        expression={"$arrayToObject": "$arr"},
        expected={"arr": [1, 2, 3]},
        msg="$arrayToObject should convert pair with array value",
    ),
]

# Property [Empty And Null]: $arrayToObject returns {} for an empty array and null for null input.
EMPTY_AND_NULL_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="empty_array",
        doc={"arr": []},
        expression={"$arrayToObject": "$arr"},
        expected={},
        msg="$arrayToObject should return empty object for empty array",
    ),
    ExpressionTestCase(
        id="null_array",
        doc={"arr": None},
        expression={"$arrayToObject": "$arr"},
        expected=None,
        msg="$arrayToObject should return null for null array",
    ),
]

# Property [Duplicate Keys]: when keys repeat, $arrayToObject keeps the last value.
DUPLICATE_KEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="kv_duplicate_keys",
        doc={"arr": [{"k": "a", "v": 1}, {"k": "a", "v": 2}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 2},
        msg="$arrayToObject should keep the last value for duplicate keys (k/v form)",
    ),
    ExpressionTestCase(
        id="pair_duplicate_keys",
        doc={"arr": [["a", 1], ["a", 2]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 2},
        msg="$arrayToObject should keep the last value for duplicate keys (pair form)",
    ),
    ExpressionTestCase(
        id="kv_triple_duplicate",
        doc={"arr": [{"k": "x", "v": 1}, {"k": "x", "v": 2}, {"k": "x", "v": 3}]},
        expression={"$arrayToObject": "$arr"},
        expected={"x": 3},
        msg="$arrayToObject should keep the last of three duplicate keys",
    ),
    ExpressionTestCase(
        id="pair_dup_different_types",
        doc={"arr": [["a", 1], ["a", "hello"]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": "hello"},
        msg="$arrayToObject should keep the last value even with different value types",
    ),
    ExpressionTestCase(
        id="pair_dup_interspersed",
        doc={"arr": [["a", 1], ["b", 2], ["a", 3]]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 3, "b": 2},
        msg="$arrayToObject should keep the last value with interspersed duplicate keys",
    ),
    ExpressionTestCase(
        id="kv_dup_interspersed",
        doc={"arr": [{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "a", "v": 3}]},
        expression={"$arrayToObject": "$arr"},
        expected={"a": 3, "b": 2},
        msg="$arrayToObject should keep the last value with interspersed duplicates (k/v form)",
    ),
    ExpressionTestCase(
        id="kv_reversed_field_order",
        doc={"arr": [{"v": "val", "k": "key"}]},
        expression={"$arrayToObject": "$arr"},
        expected={"key": "val"},
        msg="$arrayToObject should work regardless of k/v field order in document",
    ),
]

# Property [Key Characters]: $arrayToObject accepts unicode, emoji, and spaced keys.
KEY_EDGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="unicode_key",
        doc={"arr": [{"k": "日本語", "v": 1}]},
        expression={"$arrayToObject": "$arr"},
        expected={"日本語": 1},
        msg="$arrayToObject should accept a unicode key",
    ),
    ExpressionTestCase(
        id="emoji_key",
        doc={"arr": [{"k": "🔑", "v": "value"}]},
        expression={"$arrayToObject": "$arr"},
        expected={"🔑": "value"},
        msg="$arrayToObject should accept an emoji key",
    ),
    ExpressionTestCase(
        id="key_with_spaces",
        doc={"arr": [["key with spaces", 1]]},
        expression={"$arrayToObject": "$arr"},
        expected={"key with spaces": 1},
        msg="$arrayToObject should accept a key with spaces",
    ),
    ExpressionTestCase(
        id="numeric_string_keys",
        doc={"arr": [["0", "a"], ["1", "b"]]},
        expression={"$arrayToObject": "$arr"},
        expected={"0": "a", "1": "b"},
        msg="$arrayToObject should treat numeric string keys as strings",
    ),
    ExpressionTestCase(
        id="underscore_id_key",
        doc={"arr": [["_id", 1]]},
        expression={"$arrayToObject": "$arr"},
        expected={"_id": 1},
        msg="$arrayToObject should accept _id as a key",
    ),
    ExpressionTestCase(
        id="operator_like_key",
        doc={"arr": [["$set", 1]]},
        expression={"$arrayToObject": "$arr"},
        expected={"$set": 1},
        msg="$arrayToObject should accept an operator-like key",
    ),
    ExpressionTestCase(
        id="very_long_key",
        doc={"arr": [["k" * 1_024, 1]]},
        expression={"$arrayToObject": "$arr"},
        expected={"k" * 1_024: 1},
        msg="$arrayToObject should not truncate a very long key",
    ),
]

# Property [Key Handling]: $arrayToObject treats keys case-sensitively and preserves arbitrary
# nested/empty values. Output field-order preservation is verified separately in
# test_arrayToObject_preserves_field_order (a plain object comparison is order-insensitive).
# Property [Value Types]: $arrayToObject preserves complex value types.
EDGE_CASE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="case_sensitive_keys_kv",
        doc={"arr": [{"k": "price", "v": 24}, {"k": "PRICE", "v": 100}]},
        expression={"$arrayToObject": "$arr"},
        expected={"price": 24, "PRICE": 100},
        msg="$arrayToObject should treat case-differing keys as distinct",
    ),
    ExpressionTestCase(
        id="case_sensitive_keys_pair",
        doc={"arr": [["price", 24], ["PRICE", 100]]},
        expression={"$arrayToObject": "$arr"},
        expected={"price": 24, "PRICE": 100},
        msg="$arrayToObject should treat case-differing keys as distinct (pair form)",
    ),
    ExpressionTestCase(
        id="deeply_nested_object_value",
        doc={"arr": [["key", {"a": {"b": {"c": {"d": 1}}}}]]},
        expression={"$arrayToObject": "$arr"},
        expected={"key": {"a": {"b": {"c": {"d": 1}}}}},
        msg="$arrayToObject should handle deeply nested object",
    ),
    ExpressionTestCase(
        id="deeply_nested_array_value",
        doc={"arr": [["key", [[[[1]]]]]]},
        expression={"$arrayToObject": "$arr"},
        expected={"key": [[[[1]]]]},
        msg="$arrayToObject should handle deeply nested array",
    ),
    ExpressionTestCase(
        id="empty_object_value",
        doc={"arr": [["key", {}]]},
        expression={"$arrayToObject": "$arr"},
        expected={"key": {}},
        msg="$arrayToObject should handle empty object value",
    ),
    ExpressionTestCase(
        id="empty_array_value",
        doc={"arr": [["key", []]]},
        expression={"$arrayToObject": "$arr"},
        expected={"key": []},
        msg="$arrayToObject should handle empty array value",
    ),
    ExpressionTestCase(
        id="empty_string_value",
        doc={"arr": [["key", ""]]},
        expression={"$arrayToObject": "$arr"},
        expected={"key": ""},
        msg="$arrayToObject should handle empty string value",
    ),
    ExpressionTestCase(
        id="large_string_value",
        doc={"arr": [["key", "x" * 10_240]]},
        expression={"$arrayToObject": "$arr"},
        expected={"key": "x" * 10_240},
        msg="$arrayToObject should handle large string value",
    ),
]

ALL_TESTS = (
    KV_FORM_TESTS
    + TWO_ELEM_FORM_TESTS
    + EMPTY_AND_NULL_ARRAY_TESTS
    + DUPLICATE_KEY_TESTS
    + KEY_EDGE_TESTS
    + EDGE_CASE_TESTS
)

TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "kv_single_pair_literal",
        doc=None,
        expression={"$arrayToObject": {"$literal": [{"k": "a", "v": 1}]}},
        expected={"a": 1},
        msg="$arrayToObject should build object from literal kv pair",
    ),
    ExpressionTestCase(
        "pair_single_literal",
        doc=None,
        expression={"$arrayToObject": {"$literal": [["a", 1]]}},
        expected={"a": 1},
        msg="$arrayToObject should build object from literal two-element pair",
    ),
    ExpressionTestCase(
        "empty_array_literal",
        doc=None,
        expression={"$arrayToObject": {"$literal": []}},
        expected={},
        msg="$arrayToObject should return empty object for literal empty array",
    ),
    ExpressionTestCase(
        "kv_duplicate_keys_literal",
        doc=None,
        expression={"$arrayToObject": {"$literal": [{"k": "a", "v": 1}, {"k": "a", "v": 2}]}},
        expected={"a": 2},
        msg="$arrayToObject should use last value for literal duplicate keys",
    ),
    ExpressionTestCase(
        "case_sensitive_keys_kv_literal",
        doc=None,
        expression={"$arrayToObject": {"$literal": [{"k": "Name", "v": 1}, {"k": "name", "v": 2}]}},
        expected={"Name": 1, "name": 2},
        msg="$arrayToObject should treat literal keys as case-sensitive",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayToObject_literal(collection, test):
    """Test $arrayToObject with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayToObject_insert(collection, test):
    """Test $arrayToObject with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize(
    "large_arr",
    [
        pytest.param(
            lazy(lambda: [[f"key_{i}", i] for i in range(10_000)]), id="two_element_pairs"
        ),
        pytest.param(
            lazy(lambda: [{"k": f"key_{i}", "v": i} for i in range(10_000)]), id="kv_documents"
        ),
    ],
)
def test_arrayToObject_large_array(collection, large_arr):
    """Test $arrayToObject builds a 10,000-field object from pair and k/v forms."""
    expected = {f"key_{i}": i for i in range(10_000)}
    result = execute_expression(collection, {"$arrayToObject": {"$literal": large_arr}})
    assert_expression_result(
        result,
        expected=expected,
        msg="$arrayToObject should build a 10,000-field object",
    )


def test_arrayToObject_preserves_field_order(collection):
    """Test $arrayToObject preserves input pair order in the output object.

    Wrapped in $objectToArray so the assertion observes key order; a plain object
    comparison is order-insensitive and would not detect a reordering.
    """
    result = execute_expression(
        collection,
        {"$objectToArray": {"$arrayToObject": {"$literal": [["z", 1], ["a", 2], ["m", 3]]}}},
    )
    assert_expression_result(
        result,
        expected=[{"k": "z", "v": 1}, {"k": "a", "v": 2}, {"k": "m", "v": 3}],
        msg="$arrayToObject should preserve input field order in the output",
    )
