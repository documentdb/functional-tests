"""$toDouble expression tests: arity, field references, expression inputs,
size limits, and return type invariant."""

import struct
from datetime import datetime, timezone

import pytest
from bson import Binary, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    STRING_SIZE_LIMIT_ERROR,
    TO_TYPE_ARITY_ERROR,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_TWO_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    MISSING,
    STRING_SIZE_LIMIT_BYTES,
)

# ---------------------------------------------------------------------------
# Arity tests (literal array arguments to $toDouble).
# These are specific to the $toDouble operator syntax and are not parametrized
# over $convert, because $convert uses a different argument structure.
# ---------------------------------------------------------------------------


def test_toDouble_arity_single_element(collection):
    """Single-element literal array argument is unwrapped to a scalar."""
    result = execute_expression(collection, {"$toDouble": [42]})
    assert_expression_result(result, expected=42.0, msg="Single-element array unwraps to scalar")


def test_toDouble_arity_empty_array(collection):
    """Empty literal array argument is an arity error."""
    result = execute_expression(collection, {"$toDouble": []})
    assert_expression_result(
        result, error_code=TO_TYPE_ARITY_ERROR, msg="Empty array is an arity error"
    )


def test_toDouble_arity_multi_element(collection):
    """Multi-element literal array argument is an arity error."""
    result = execute_expression(collection, {"$toDouble": [1, 2]})
    assert_expression_result(
        result, error_code=TO_TYPE_ARITY_ERROR, msg="Multi-element array is an arity error"
    )


def test_toDouble_arity_single_null(collection):
    """Single-element literal array wrapping null unwraps and returns null."""
    result = execute_expression(collection, {"$toDouble": [None]})
    assert_expression_result(
        result, expected=None, msg="Single-element array [null] unwraps to null"
    )


def test_toDouble_arity_single_bool(collection):
    """Single-element literal array wrapping a bool unwraps and converts."""
    result = execute_expression(collection, {"$toDouble": [True]})
    assert_expression_result(result, expected=1.0, msg="Single-element array [true] unwraps to 1.0")


def test_toDouble_arity_large_array(collection):
    """A large literal array argument is an arity error."""
    result = execute_expression(collection, {"$toDouble": list(range(100))})
    assert_expression_result(
        result, error_code=TO_TYPE_ARITY_ERROR, msg="100-element array is an arity error"
    )


# ---------------------------------------------------------------------------
# Field reference tests: $toDouble resolves values from document fields.
# ---------------------------------------------------------------------------

TODOUBLE_FIELD_REF_TESTS = [
    ("int_field", "$v", {"v": 42}, 42.0),
    ("int64_field", "$v", {"v": Int64(86400000)}, 86400000.0),
    ("double_field", "$v", {"v": 3.14}, 3.14),
    ("string_field", "$v", {"v": "2.5"}, DOUBLE_TWO_AND_HALF),
    ("bool_field", "$v", {"v": True}, 1.0),
    ("nested_field", "$doc.v", {"doc": {"v": 100}}, 100.0),
    ("missing_nested", "$doc.missing", {"doc": {"x": 1}}, None),
    ("missing_field", "$v", {}, None),
]


@pytest.mark.parametrize(
    "name,field_path,doc,expected",
    TODOUBLE_FIELD_REF_TESTS,
    ids=[t[0] for t in TODOUBLE_FIELD_REF_TESTS],
)
def test_toDouble_field_ref(collection, name, field_path, doc, expected):
    """$toDouble resolves field paths and nested paths from inserted documents."""
    result = execute_expression_with_insert(collection, {"$toDouble": field_path}, doc)
    assert_expression_result(result, expected=expected)


def test_toDouble_composite_array_path(collection):
    """$toDouble on a composite array path (array of objects) is a conversion failure."""
    result = execute_expression_with_insert(
        collection,
        {"$toDouble": "$a.b"},
        {"a": [{"b": 1.0}, {"b": 2.0}]},
    )
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR)


# ---------------------------------------------------------------------------
# Invalid field path tests (specific to $toDouble syntax only).
# ---------------------------------------------------------------------------


def test_toDouble_bare_dollar_field_path(collection):
    """Bare '$' is an invalid field path and produces an error."""
    result = execute_expression(collection, {"$toDouble": "$"})
    assert_expression_result(
        result, error_code=INVALID_DOLLAR_FIELD_PATH, msg="Bare $ is an invalid field path"
    )


def test_toDouble_double_dollar_field_path(collection):
    """'$$' is an empty variable name and produces a parse error."""
    result = execute_expression(collection, {"$toDouble": "$$"})
    assert_expression_result(
        result, error_code=FAILED_TO_PARSE_ERROR, msg="$$ is rejected as empty variable name"
    )


# ---------------------------------------------------------------------------
# Expression-as-input tests: $toDouble accepts any expression as its argument.
# ---------------------------------------------------------------------------


def test_toDouble_expression_as_input_add(collection):
    """$toDouble accepts an arithmetic expression operator as input."""
    result = execute_expression(collection, {"$toDouble": {"$add": [10, 20]}})
    assert_expression_result(
        result, expected=30.0, msg="$toDouble should convert integer expression result"
    )


def test_toDouble_expression_as_input_concat(collection):
    """$toDouble accepts a $concat string expression as input."""
    result = execute_expression(collection, {"$toDouble": {"$concat": ["3", ".", "14"]}})
    assert_expression_result(
        result, expected=3.14, msg="$toDouble should convert string expression result"
    )


def test_toDouble_expression_as_input_nested_conversion(collection):
    """$toDouble accepts the result of a nested type-conversion expression."""
    result = execute_expression(collection, {"$toDouble": {"$toDecimal": 42}})
    assert_expression_result(
        result, expected=42.0, msg="$toDouble should convert result of nested type conversion"
    )


# ---------------------------------------------------------------------------
# Size-limit tests.
# ---------------------------------------------------------------------------


def test_toDouble_string_under_limit_numeric(collection):
    """A valid numeric string one byte under the limit converts successfully."""
    result = execute_expression(
        collection, {"$toDouble": "0" * (STRING_SIZE_LIMIT_BYTES - 2) + "1"}
    )
    assert_expression_result(
        result, expected=1.0, msg="Valid numeric string one byte under limit should succeed"
    )


def test_toDouble_string_under_limit_hex(collection):
    """A valid hex string one byte under the limit converts successfully."""
    result = execute_expression(
        collection, {"$toDouble": "0X" + "0" * (STRING_SIZE_LIMIT_BYTES - 4) + "F"}
    )
    assert_expression_result(
        result,
        expected=15.0,
        msg="Valid hex string one byte under limit should succeed with value 15.0",
    )


def test_toDouble_string_non_numeric_under_limit(collection):
    """A non-numeric string one byte under the limit passes the size check but fails conversion."""
    result = execute_expression(collection, {"$toDouble": "a" * (STRING_SIZE_LIMIT_BYTES - 1)})
    assert_expression_result(
        result,
        error_code=CONVERSION_FAILURE_ERROR,
        msg="Non-numeric string just under limit: CONVERSION_FAILURE, not STRING_SIZE_LIMIT",
    )


def test_toDouble_string_at_size_limit(collection):
    """A string at exactly STRING_SIZE_LIMIT_BYTES is rejected with STRING_SIZE_LIMIT_ERROR."""
    result = execute_expression(collection, {"$toDouble": "a" * STRING_SIZE_LIMIT_BYTES})
    assert_expression_result(
        result,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="String at STRING_SIZE_LIMIT_BYTES should be rejected",
    )


def test_toDouble_string_four_byte_chars_at_limit(collection):
    """A string of 4-byte characters reaching STRING_SIZE_LIMIT_BYTES is rejected."""
    result = execute_expression(
        collection, {"$toDouble": "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)}
    )
    assert_expression_result(
        result,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="4-byte character string reaching the size limit should be rejected",
    )


# ---------------------------------------------------------------------------
# Return type invariant: all non-null conversions produce BSON "double";
# null and missing inputs produce BSON "null".
# ---------------------------------------------------------------------------

# (name, value, human-readable label)
_RETURN_TYPE_DOUBLE_CASES = [
    ("return_type_bool", True, "bool"),
    ("return_type_double", 3.14, "double"),
    ("return_type_int32", 42, "int32"),
    ("return_type_int64", Int64(42), "int64"),
    ("return_type_decimal128", DECIMAL128_TWO_AND_HALF, "Decimal128"),
    ("return_type_string", "7.5", "string"),
    ("return_type_datetime", datetime(2024, 1, 1, tzinfo=timezone.utc), "datetime"),
    ("return_type_binary", Binary(struct.pack("<d", 1.0)), "Binary"),
    ("return_type_inf", FLOAT_INFINITY, "Infinity"),
    ("return_type_neg_inf", FLOAT_NEGATIVE_INFINITY, "-Infinity"),
    ("return_type_nan", FLOAT_NAN, "NaN"),
]


@pytest.mark.parametrize(
    "name,value,label",
    _RETURN_TYPE_DOUBLE_CASES,
    ids=[t[0] for t in _RETURN_TYPE_DOUBLE_CASES],
)
def test_toDouble_return_type_is_double(collection, name, value, label):
    """$toDouble always returns BSON type 'double' for a successful conversion."""
    result = execute_expression(collection, {"$type": {"$toDouble": value}})
    assert_expression_result(
        result, expected="double", msg=f"$toDouble should return double type for {label} input"
    )


def test_toDouble_return_type_null_for_null(collection):
    """$toDouble returns BSON type 'null' for a null input."""
    result = execute_expression(collection, {"$type": {"$toDouble": None}})
    assert_expression_result(
        result, expected="null", msg="$toDouble of null should return null type"
    )


def test_toDouble_return_type_null_for_missing(collection):
    """$toDouble returns BSON type 'null' for a missing input."""
    result = execute_expression(collection, {"$type": {"$toDouble": MISSING}})
    assert_expression_result(
        result, expected="null", msg="$toDouble of missing should return null type"
    )


# ---------------------------------------------------------------------------
# Idempotency: $toDouble applied twice equals $toDouble applied once.
# ---------------------------------------------------------------------------

# (name, value, expected_double)
_IDEMPOTENCY_CASES = [
    ("idempotent_bool", True, 1.0),
    ("idempotent_double", 3.14, 3.14),
    ("idempotent_int32", 42, 42.0),
    ("idempotent_int64", Int64(99), 99.0),
    ("idempotent_decimal128", DECIMAL128_TWO_AND_HALF, DOUBLE_TWO_AND_HALF),
    ("idempotent_string", "7.5", 7.5),
    ("idempotent_datetime", datetime(2024, 1, 1, tzinfo=timezone.utc), 1_704_067_200_000.0),
    ("idempotent_binary_8byte", Binary(struct.pack("<d", 5.0)), 5.0),
]


@pytest.mark.parametrize(
    "name,value,expected",
    _IDEMPOTENCY_CASES,
    ids=[t[0] for t in _IDEMPOTENCY_CASES],
)
def test_toDouble_idempotency(collection, name, value, expected):
    """Applying $toDouble twice produces the same result as applying it once."""
    result = execute_expression(collection, {"$toDouble": {"$toDouble": value}})
    assert_expression_result(
        result, expected=expected, msg=f"$toDouble should be idempotent for {name}"
    )


def test_toDouble_neg_zero_from_field(collection):
    """$toDouble preserves -0.0 sign when reading from a document field."""
    result = execute_expression_with_insert(
        collection, {"$toDouble": "$v"}, {"v": DOUBLE_NEGATIVE_ZERO}
    )
    assert_expression_result(result, expected=DOUBLE_NEGATIVE_ZERO)
