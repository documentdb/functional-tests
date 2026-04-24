"""
Tests for $allElementsTrue argument validation, error codes, and invalid inputs.

Covers argument count errors, non-array argument types, null/missing field
handling, system variable errors, and literal format validation.

Error 5159200: wrong argument count (0 or 2+ args)
Error 17041: non-array argument at runtime (field resolves to non-array)
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.set.allElementsTrue.utils.allElementsTrue_utils import (  # noqa: E501
    AllElementsTrueTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Wrong argument count
# ---------------------------------------------------------------------------
WRONG_ARG_COUNT_TESTS: list[AllElementsTrueTest] = [
    AllElementsTrueTest(
        "no_args",
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="No arguments should error",
    ),
    AllElementsTrueTest(
        "two_args",
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Two arguments should error",
    ),
    AllElementsTrueTest(
        "three_args",
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Three arguments should error",
    ),
    AllElementsTrueTest(
        "six_args",
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Six arguments should error",
    ),
]

_WRONG_ARG_EXPRESSIONS = {
    "no_args": {"$allElementsTrue": []},
    "two_args": {"$allElementsTrue": [[True], [False]]},
    "three_args": {"$allElementsTrue": [[True], [False], [1]]},
    "six_args": {"$allElementsTrue": [[], [], [], [], [], []]},
}


@pytest.mark.parametrize("test", pytest_params(WRONG_ARG_COUNT_TESTS))
def test_allElementsTrue_wrong_arg_count(collection, test):
    """Test $allElementsTrue rejects wrong argument counts."""
    result = execute_expression(collection, _WRONG_ARG_EXPRESSIONS[test.id])
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Literal non-array wrapping — [true] is interpreted as bool arg, not array
# ---------------------------------------------------------------------------
def test_allElementsTrue_unwrapped_bool_literal(collection):
    """Test $allElementsTrue with [true] (bool, not array) errors."""
    result = execute_expression(collection, {"$allElementsTrue": [True]})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Bool literal should error"
    )


def test_allElementsTrue_unwrapped_int_literals(collection):
    """Test $allElementsTrue with [1, 2, 3] interpreted as 3 args errors."""
    result = execute_expression(collection, {"$allElementsTrue": [1, 2, 3]})
    assert_expression_result(
        result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR, msg="Multiple int literals should error"
    )


def test_allElementsTrue_wrapped_int_literals(collection):
    """Test $allElementsTrue with [[1, 2, 3]] (wrapped) succeeds."""
    result = execute_expression(collection, {"$allElementsTrue": [[1, 2, 3]]})
    assert_expression_result(result, expected=True, msg="Wrapped literal array should succeed")


# ---------------------------------------------------------------------------
# Non-array field types — field resolves to non-array
# ---------------------------------------------------------------------------
NON_ARRAY_FIELD_TESTS: list[AllElementsTrueTest] = [
    AllElementsTrueTest(
        "string_field",
        document={"a": "hello"},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="String field should error",
    ),
    AllElementsTrueTest(
        "int_field",
        document={"a": 1},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Int field should error",
    ),
    AllElementsTrueTest(
        "long_field",
        document={"a": Int64(1)},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Long field should error",
    ),
    AllElementsTrueTest(
        "double_field",
        document={"a": 1.5},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Double field should error",
    ),
    AllElementsTrueTest(
        "decimal_field",
        document={"a": Decimal128("1")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal128 field should error",
    ),
    AllElementsTrueTest(
        "bool_field",
        document={"a": True},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Bool field should error",
    ),
    AllElementsTrueTest(
        "null_field",
        document={"a": None},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Null field should error",
    ),
    AllElementsTrueTest(
        "object_field",
        document={"a": {"x": 1}},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Object field should error",
    ),
    AllElementsTrueTest(
        "objectid_field",
        document={"a": ObjectId("507f1f77bcf86cd799439011")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="ObjectId field should error",
    ),
    AllElementsTrueTest(
        "date_field",
        document={"a": datetime(2017, 1, 1)},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Date field should error",
    ),
    AllElementsTrueTest(
        "timestamp_field",
        document={"a": Timestamp(1, 1)},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Timestamp field should error",
    ),
    AllElementsTrueTest(
        "regex_field",
        document={"a": Regex("pattern")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Regex field should error",
    ),
    AllElementsTrueTest(
        "bindata_field",
        document={"a": Binary(b"", 0)},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="BinData field should error",
    ),
    AllElementsTrueTest(
        "nan_field",
        document={"a": float("nan")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="NaN field should error",
    ),
    AllElementsTrueTest(
        "decimal_nan_field",
        document={"a": Decimal128("NaN")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal128 NaN field should error",
    ),
    AllElementsTrueTest(
        "inf_field",
        document={"a": float("inf")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Infinity field should error",
    ),
    AllElementsTrueTest(
        "decimal_inf_field",
        document={"a": Decimal128("Infinity")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal128 Infinity field should error",
    ),
    AllElementsTrueTest(
        "decimal_neg_inf_field",
        document={"a": Decimal128("-Infinity")},
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal128 -Infinity field should error",
    ),
    AllElementsTrueTest(
        "array_field_succeeds",
        document={"a": [True]},
        expected=True,
        msg="Array field should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_ARRAY_FIELD_TESTS))
def test_allElementsTrue_non_array_field(collection, test):
    """Test $allElementsTrue with field resolving to non-array type."""
    result = execute_expression_with_insert(collection, {"$allElementsTrue": ["$a"]}, test.document)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# ---------------------------------------------------------------------------
# Null/missing field handling
# ---------------------------------------------------------------------------
def test_allElementsTrue_null_field(collection):
    """Test $allElementsTrue with field resolving to null errors."""
    result = execute_expression_with_insert(collection, {"$allElementsTrue": ["$a"]}, {"a": None})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Null field should error"
    )


def test_allElementsTrue_missing_field(collection):
    """Test $allElementsTrue with missing field errors."""
    result = execute_expression_with_insert(collection, {"$allElementsTrue": ["$a"]}, {"b": 1})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Missing field should error"
    )


def test_allElementsTrue_missing_field_empty_doc(collection):
    """Test $allElementsTrue with missing field on empty doc errors."""
    result = execute_expression_with_insert(collection, {"$allElementsTrue": ["$nonexistent"]}, {})
    assert_expression_result(
        result,
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Missing field on empty doc should error",
    )


def test_allElementsTrue_missing_field_with_other_fields(collection):
    """Test $allElementsTrue with missing field when doc has other fields."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$missing_field"]}, {"a": [1, 2]}
    )
    assert_expression_result(
        result,
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Missing field should error even when doc has other fields",
    )


# ---------------------------------------------------------------------------
# Null literal argument
# ---------------------------------------------------------------------------
def test_allElementsTrue_null_literal_arg(collection):
    """Test $allElementsTrue with null literal argument errors."""
    result = execute_expression(collection, {"$allElementsTrue": [None]})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Null literal arg should error"
    )


def test_allElementsTrue_null_inside_array_arg(collection):
    """Test $allElementsTrue with [None] inside array argument — null as element, not arg."""
    result = execute_expression(collection, {"$allElementsTrue": [[None]]})
    assert_expression_result(
        result, expected=False, msg="Should return false when null is a falsy element"
    )


# ---------------------------------------------------------------------------
# Non-array literal arguments
# ---------------------------------------------------------------------------
def test_allElementsTrue_string_literal(collection):
    """Test $allElementsTrue with string literal errors."""
    result = execute_expression(collection, {"$allElementsTrue": "not_an_array"})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="String literal should error"
    )


def test_allElementsTrue_int_literal(collection):
    """Test $allElementsTrue with int literal errors."""
    result = execute_expression(collection, {"$allElementsTrue": 123})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Int literal should error"
    )


def test_allElementsTrue_null_top_level(collection):
    """Test $allElementsTrue with null top-level errors."""
    result = execute_expression(collection, {"$allElementsTrue": None})
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Null top-level should error"
    )


# ---------------------------------------------------------------------------
# System variables — resolve to non-array
# ---------------------------------------------------------------------------
def test_allElementsTrue_root_variable(collection):
    """Test $allElementsTrue with $$ROOT (object, not array) errors."""
    result = execute_expression_with_insert(collection, {"$allElementsTrue": ["$$ROOT"]}, {"a": 1})
    assert_expression_result(
        result,
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Should error when ROOT variable resolves to object",
    )


def test_allElementsTrue_current_variable(collection):
    """Test $allElementsTrue with $$CURRENT (object, not array) errors."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$$CURRENT"]}, {"a": 1}
    )
    assert_expression_result(
        result,
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Should error when CURRENT variable resolves to object",
    )


def test_allElementsTrue_remove_variable(collection):
    """Test $allElementsTrue with $$REMOVE (missing) errors."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$$REMOVE"]}, {"a": 1}
    )
    assert_expression_result(
        result,
        error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Should error when REMOVE variable resolves to missing",
    )


# ---------------------------------------------------------------------------
# Object expression input — not array
# ---------------------------------------------------------------------------
def test_allElementsTrue_object_expression_input(collection):
    """Test $allElementsTrue with object expression (not array) errors."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": [{"a": "$x"}]}, {"x": 1}
    )
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Object expression should error"
    )


# ---------------------------------------------------------------------------
# Missing field path in array argument
# ---------------------------------------------------------------------------
def test_allElementsTrue_missing_field_path_in_array(collection):
    """Test $allElementsTrue with ["$not_exist"] (missing field in array arg) errors."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$not_exist"]}, {"a": 1}
    )
    assert_expression_result(
        result, error_code=ALL_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Missing field path should error"
    )
