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
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    MISSING,
    STRING_SIZE_LIMIT_BYTES,
)

from .utils.toDouble_utils import _DOC_EXPR_FORMS, _EXPR_FORMS, ToDoubleTest

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
    ("string_field", "$v", {"v": "2.5"}, 2.5),
    ("bool_field", "$v", {"v": True}, 1.0),
    ("nested_field", "$doc.v", {"doc": {"v": 100}}, 100.0),
    ("missing_nested", "$doc.missing", {"doc": {"x": 1}}, None),
    ("missing_field", "$v", {}, None),
]


@pytest.mark.parametrize("expr_fn", _DOC_EXPR_FORMS)
@pytest.mark.parametrize(
    "name,expr,doc,expected",
    TODOUBLE_FIELD_REF_TESTS,
    ids=[t[0] for t in TODOUBLE_FIELD_REF_TESTS],
)
def test_toDouble_field_ref(collection, name, expr, doc, expected, expr_fn):
    """$toDouble resolves field paths and nested paths from inserted documents."""
    result = execute_expression_with_insert(collection, expr_fn(expr), doc)
    assert_expression_result(result, expected=expected)


@pytest.mark.parametrize("expr_fn", _DOC_EXPR_FORMS)
def test_toDouble_composite_array_path(collection, expr_fn):
    """$toDouble on a composite array path (array of objects) is a conversion failure."""
    result = execute_expression_with_insert(
        collection,
        expr_fn("$a.b"),
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


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_double_dollar_field_path(collection, expr_fn):
    """'$$' is an empty variable name and produces a parse error."""
    test = ToDoubleTest(
        "fieldpath_double_dollar", value="$$", msg="$$ is rejected as empty variable name"
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, error_code=FAILED_TO_PARSE_ERROR, msg=test.msg)


# ---------------------------------------------------------------------------
# Expression-as-input tests: $toDouble accepts any expression as its argument.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_expression_as_input_add(collection, expr_fn):
    """$toDouble accepts an arithmetic expression operator as input."""
    test = ToDoubleTest(
        "expr_add",
        value={"$add": [10, 20]},
        msg="$toDouble should convert integer expression result",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, expected=30.0, msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_expression_as_input_concat(collection, expr_fn):
    """$toDouble accepts a $concat string expression as input."""
    test = ToDoubleTest(
        "expr_concat",
        value={"$concat": ["3", ".", "14"]},
        msg="$toDouble should convert string expression result",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, expected=3.14, msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_expression_as_input_nested_conversion(collection, expr_fn):
    """$toDouble accepts the result of a nested type-conversion expression."""
    test = ToDoubleTest(
        "expr_nested",
        value={"$toDecimal": 42},
        msg="$toDouble should convert result of nested type conversion",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, expected=42.0, msg=test.msg)


# ---------------------------------------------------------------------------
# Size-limit tests.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_string_under_limit_numeric(collection, expr_fn):
    """A valid numeric string one byte under the limit converts successfully."""
    test = ToDoubleTest(
        "str_one_under_valid",
        value="0" * (STRING_SIZE_LIMIT_BYTES - 2) + "1",
        msg="Valid numeric string one byte under limit should succeed",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, expected=1.0, msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_string_under_limit_hex(collection, expr_fn):
    """A valid hex string one byte under the limit converts successfully."""
    test = ToDoubleTest(
        "str_one_under_hex",
        value="0X" + "0" * (STRING_SIZE_LIMIT_BYTES - 4) + "F",
        msg="Valid hex string one byte under limit should succeed with value 15.0",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, expected=15.0, msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_string_non_numeric_under_limit(collection, expr_fn):
    """A non-numeric string one byte under the limit passes the size check but fails conversion."""
    test = ToDoubleTest(
        "str_non_numeric_under_limit",
        value="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="Non-numeric string just under limit: CONVERSION_FAILURE, not STRING_SIZE_LIMIT",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR, msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_string_at_size_limit(collection, expr_fn):
    """A string at exactly STRING_SIZE_LIMIT_BYTES is rejected with STRING_SIZE_LIMIT_ERROR."""
    test = ToDoubleTest(
        "str_at_limit",
        value="a" * STRING_SIZE_LIMIT_BYTES,
        msg="String at STRING_SIZE_LIMIT_BYTES should be rejected",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, error_code=STRING_SIZE_LIMIT_ERROR, msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_string_four_byte_chars_at_limit(collection, expr_fn):
    """A string of 4-byte characters reaching STRING_SIZE_LIMIT_BYTES is rejected."""
    test = ToDoubleTest(
        "str_4byte_at_limit",
        value="\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4),
        msg="4-byte character string reaching the size limit should be rejected",
    )
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, error_code=STRING_SIZE_LIMIT_ERROR, msg=test.msg)


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


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
@pytest.mark.parametrize(
    "name,value,label",
    _RETURN_TYPE_DOUBLE_CASES,
    ids=[t[0] for t in _RETURN_TYPE_DOUBLE_CASES],
)
def test_toDouble_return_type_is_double(collection, name, value, label, expr_fn):
    """$toDouble always returns BSON type 'double' for a successful conversion."""
    test = ToDoubleTest(
        name, value=value, msg=f"$toDouble should return double type for {label} input"
    )
    result = execute_expression(collection, {"$type": expr_fn(test)})
    assert_expression_result(result, expected="double", msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_return_type_null_for_null(collection, expr_fn):
    """$toDouble returns BSON type 'null' for a null input."""
    test = ToDoubleTest(
        "return_type_null", value=None, msg="$toDouble of null should return null type"
    )
    result = execute_expression(collection, {"$type": expr_fn(test)})
    assert_expression_result(result, expected="null", msg=test.msg)


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_return_type_null_for_missing(collection, expr_fn):
    """$toDouble returns BSON type 'null' for a missing input."""
    test = ToDoubleTest(
        "return_type_missing", value=MISSING, msg="$toDouble of missing should return null type"
    )
    result = execute_expression(collection, {"$type": expr_fn(test)})
    assert_expression_result(result, expected="null", msg=test.msg)


# ---------------------------------------------------------------------------
# Idempotency: $toDouble applied twice equals $toDouble applied once.
# ---------------------------------------------------------------------------

# (name, value, expected_double)
_IDEMPOTENCY_CASES = [
    ("idempotent_bool", True, 1.0),
    ("idempotent_double", 3.14, 3.14),
    ("idempotent_int32", 42, 42.0),
    ("idempotent_int64", Int64(99), 99.0),
    ("idempotent_decimal128", DECIMAL128_TWO_AND_HALF, 2.5),
    ("idempotent_string", "7.5", 7.5),
    ("idempotent_datetime", datetime(2024, 1, 1, tzinfo=timezone.utc), 1_704_067_200_000.0),
    ("idempotent_binary_8byte", Binary(struct.pack("<d", 5.0)), 5.0),
]


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
@pytest.mark.parametrize(
    "name,value,expected",
    _IDEMPOTENCY_CASES,
    ids=[t[0] for t in _IDEMPOTENCY_CASES],
)
def test_toDouble_idempotency(collection, name, value, expected, expr_fn):
    """Applying $toDouble twice produces the same result as applying it once."""
    once_test = ToDoubleTest(name, value=value)
    twice_test = ToDoubleTest(f"{name}_twice", value=expr_fn(once_test))
    result = execute_expression(collection, expr_fn(twice_test))
    assert_expression_result(
        result, expected=expected, msg=f"$toDouble should be idempotent for {name}"
    )


@pytest.mark.parametrize("expr_fn", _DOC_EXPR_FORMS)
def test_toDouble_neg_zero_from_field(collection, expr_fn):
    """$toDouble preserves -0.0 sign when reading from a document field."""
    result = execute_expression_with_insert(collection, expr_fn("$v"), {"v": -0.0})
    assert_expression_result(
        result, expected=DOUBLE_NEGATIVE_ZERO, msg="Field -0.0 value preserves sign"
    )
