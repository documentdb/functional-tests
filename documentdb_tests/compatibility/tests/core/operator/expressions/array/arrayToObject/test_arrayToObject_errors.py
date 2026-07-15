"""
Error tests for $arrayToObject expression.

Tests non-array input, invalid element format, non-string keys,
and wrong arity errors.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
    ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
    ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
    ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
    ARRAY_TO_OBJECT_MIXED_KV_THEN_PAIR_ERROR,
    ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
    ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
    ARRAY_TO_OBJECT_NULL_BYTE_KV_KEY_ERROR,
    ARRAY_TO_OBJECT_NULL_BYTE_PAIR_KEY_ERROR,
    ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
    ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Array Type Strictness]: $arrayToObject rejects a non-array input.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        doc={"arr": "hello"},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject string input",
    ),
    ExpressionTestCase(
        id="int_input",
        doc={"arr": 42},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject int input",
    ),
    ExpressionTestCase(
        id="bool_input",
        doc={"arr": True},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject bool input",
    ),
    ExpressionTestCase(
        id="object_input",
        doc={"arr": {"a": 1}},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject object input",
    ),
    ExpressionTestCase(
        id="double_input",
        doc={"arr": 3.14},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject double input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        doc={"arr": Decimal128("1")},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        doc={"arr": Int64(1)},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        doc={"arr": ObjectId()},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        doc={"arr": datetime(2024, 1, 1)},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        doc={"arr": Binary(b"x", 0)},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        doc={"arr": Regex("x")},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        doc={"arr": MaxKey()},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        doc={"arr": MinKey()},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject minkey input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        doc={"arr": Timestamp(0, 0)},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject timestamp input",
    ),
]

# Property [Element Format]: $arrayToObject rejects an element that is not a k/v doc or pair.
INVALID_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="element_is_string",
        doc={"arr": ["not_a_pair"]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject string element",
    ),
    ExpressionTestCase(
        id="element_is_int",
        doc={"arr": [42]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject int element",
    ),
    ExpressionTestCase(
        id="element_is_null",
        doc={"arr": [None]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject null element",
    ),
    ExpressionTestCase(
        id="element_is_bool",
        doc={"arr": [True]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject bool element",
    ),
    ExpressionTestCase(
        id="element_is_double",
        doc={"arr": [3.14]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject double element",
    ),
    ExpressionTestCase(
        id="element_is_objectid",
        doc={"arr": [ObjectId()]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject ObjectId element",
    ),
    ExpressionTestCase(
        id="kv_missing_v",
        doc={"arr": [{"k": "a"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc missing v field",
    ),
    ExpressionTestCase(
        id="kv_missing_k",
        doc={"arr": [{"v": 1}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc missing k field",
    ),
    ExpressionTestCase(
        id="kv_extra_field",
        doc={"arr": [{"k": "a", "v": 1, "extra": 2}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc with extra field",
    ),
    ExpressionTestCase(
        id="kv_empty_doc",
        doc={"arr": [{}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject empty document",
    ),
    ExpressionTestCase(
        id="kv_wrong_field_names",
        doc={"arr": [{"y": "x", "x": "y"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject wrong field names",
    ),
    ExpressionTestCase(
        id="kv_uppercase_K",
        doc={"arr": [{"K": "k1", "v": 2}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject uppercase K (case-sensitive)",
    ),
    ExpressionTestCase(
        id="kv_uppercase_V",
        doc={"arr": [{"k": "k1", "V": 2}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject uppercase V (case-sensitive)",
    ),
    ExpressionTestCase(
        id="kv_key_value_names",
        doc={"arr": [{"key": "k1", "value": "v1"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject 'key'/'value' instead of 'k'/'v'",
    ),
    ExpressionTestCase(
        id="pair_one_element",
        doc={"arr": [["a"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject one-element array pair",
    ),
    ExpressionTestCase(
        id="pair_three_elements",
        doc={"arr": [["a", 1, 2]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject three-element array pair",
    ),
    ExpressionTestCase(
        id="pair_empty_array",
        doc={"arr": [[]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject empty array pair",
    ),
]

# Property [Key Type Strictness]: $arrayToObject rejects a non-string key.
KEY_NOT_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="kv_int_key",
        doc={"arr": [{"k": 1, "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject int key in k/v form",
    ),
    ExpressionTestCase(
        id="kv_bool_key",
        doc={"arr": [{"k": True, "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject bool key in k/v form",
    ),
    ExpressionTestCase(
        id="kv_null_key",
        doc={"arr": [{"k": None, "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject null key in k/v form",
    ),
    ExpressionTestCase(
        id="kv_array_key",
        doc={"arr": [{"k": [1], "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject array key in k/v form",
    ),
    ExpressionTestCase(
        id="kv_object_key",
        doc={"arr": [{"k": {"x": 1}, "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject object key in k/v form",
    ),
    ExpressionTestCase(
        id="kv_double_key",
        doc={"arr": [{"k": 1.5, "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject double key in k/v form",
    ),
    ExpressionTestCase(
        id="kv_int64_key",
        doc={"arr": [{"k": Int64(1), "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Int64 key in k/v form",
    ),
    ExpressionTestCase(
        id="kv_decimal128_key",
        doc={"arr": [{"k": Decimal128("1"), "v": "val"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Decimal128 key in k/v form",
    ),
    ExpressionTestCase(
        id="pair_int_key",
        doc={"arr": [[1, "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject int key in pair form",
    ),
    ExpressionTestCase(
        id="pair_bool_key",
        doc={"arr": [[True, "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject bool key in pair form",
    ),
    ExpressionTestCase(
        id="pair_null_key",
        doc={"arr": [[None, "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject null key in pair form",
    ),
    ExpressionTestCase(
        id="pair_array_key",
        doc={"arr": [[[1], "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject array key in pair form",
    ),
    ExpressionTestCase(
        id="pair_object_key",
        doc={"arr": [[{"x": 1}, "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject object key in pair form",
    ),
    ExpressionTestCase(
        id="pair_double_key",
        doc={"arr": [[1.5, "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject double key in pair form",
    ),
    ExpressionTestCase(
        id="pair_int64_key",
        doc={"arr": [[Int64(1), "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Int64 key in pair form",
    ),
    ExpressionTestCase(
        id="pair_decimal128_key",
        doc={"arr": [[Decimal128("1"), "val"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Decimal128 key in pair form",
    ),
]

# Property [Mixed Formats]: $arrayToObject rejects arrays mixing k/v doc and pair forms.
MIXED_FORMAT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="mixed_kv_then_pair",
        doc={"arr": [{"k": "price", "v": 24}, ["item", "apple"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_MIXED_KV_THEN_PAIR_ERROR,
        msg="$arrayToObject should reject a k/v doc followed by a pair",
    ),
    ExpressionTestCase(
        id="mixed_pair_then_kv",
        doc={"arr": [["item", "apple"], {"k": "price", "v": 24}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
        msg="$arrayToObject should reject a pair followed by a k/v doc",
    ),
    ExpressionTestCase(
        id="mixed_pair_then_non_array",
        doc={"arr": [["a", 1], 123]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
        msg="$arrayToObject should reject a pair followed by a non-array element",
    ),
]

# Property [Null Byte Key]: $arrayToObject rejects a key containing a null byte.
NULL_BYTE_KEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_byte_in_key_pair",
        doc={"arr": [["a\x00b", "value"]]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NULL_BYTE_PAIR_KEY_ERROR,
        msg="$arrayToObject should reject a null byte in a key (pair form)",
    ),
    ExpressionTestCase(
        id="null_byte_in_key_kv",
        doc={"arr": [{"k": "a\x00b", "v": "value"}]},
        expression={"$arrayToObject": "$arr"},
        error_code=ARRAY_TO_OBJECT_NULL_BYTE_KV_KEY_ERROR,
        msg="$arrayToObject should reject a null byte in a key (k/v form)",
    ),
]

ALL_TESTS = (
    NOT_ARRAY_ERROR_TESTS
    + INVALID_ELEMENT_TESTS
    + KEY_NOT_STRING_TESTS
    + MIXED_FORMAT_TESTS
    + NULL_BYTE_KEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayToObject_insert(collection, test):
    """Test $arrayToObject error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Arity]: $arrayToObject requires exactly one argument.
ARITY_ERROR_TESTS = [
    pytest.param({"$arrayToObject": [[], []]}, id="two_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_arrayToObject_arity_error(collection, expr):
    """Test $arrayToObject errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)
