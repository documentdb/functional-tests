"""
Tests for $anyElementTrue error handling and invalid inputs.

Covers non-array argument errors, wrong argument count,
field path resolving to non-array, and missing field errors.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.set.anyElementTrue.utils.anyElementTrue_utils import (  # noqa: E501
    AnyElementTrueTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Non-array argument errors (error code 17041)
# ---------------------------------------------------------------------------
NON_ARRAY_FIELD_TESTS: list[AnyElementTrueTest] = [
    AnyElementTrueTest(
        "string_field",
        document={"A": "red"},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="String field should error",
    ),
    AnyElementTrueTest(
        "int_field",
        document={"A": 1},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Int field should error",
    ),
    AnyElementTrueTest(
        "long_field",
        document={"A": Int64(1)},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Long field should error",
    ),
    AnyElementTrueTest(
        "double_field",
        document={"A": 1.5},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Double field should error",
    ),
    AnyElementTrueTest(
        "decimal_field",
        document={"A": Decimal128("1")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal128 field should error",
    ),
    AnyElementTrueTest(
        "bool_field",
        document={"A": True},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Bool field should error",
    ),
    AnyElementTrueTest(
        "object_field",
        document={"A": {"a": 1}},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Object field should error",
    ),
    AnyElementTrueTest(
        "objectid_field",
        document={"A": ObjectId("507f1f77bcf86cd799439011")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="ObjectId field should error",
    ),
    AnyElementTrueTest(
        "date_field",
        document={"A": datetime(2017, 1, 1)},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Date field should error",
    ),
    AnyElementTrueTest(
        "timestamp_field",
        document={"A": Timestamp(315532800, 0)},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Timestamp field should error",
    ),
    AnyElementTrueTest(
        "bindata_field",
        document={"A": Binary(b"\x62\x25", 2)},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="BinData field should error",
    ),
    AnyElementTrueTest(
        "regex_field",
        document={"A": Regex("[a-m]")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Regex field should error",
    ),
    AnyElementTrueTest(
        "nan_double_field",
        document={"A": float("nan")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="NaN double field should error",
    ),
    AnyElementTrueTest(
        "nan_decimal_field",
        document={"A": Decimal128("NaN")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal NaN field should error",
    ),
    AnyElementTrueTest(
        "inf_field",
        document={"A": float("inf")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Infinity field should error",
    ),
    AnyElementTrueTest(
        "decimal_inf_field",
        document={"A": Decimal128("Infinity")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal Infinity field should error",
    ),
    AnyElementTrueTest(
        "decimal_neg_inf_field",
        document={"A": Decimal128("-Infinity")},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Decimal -Infinity field should error",
    ),
    AnyElementTrueTest(
        "minkey_field",
        document={"A": MinKey()},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="MinKey field should error",
    ),
    AnyElementTrueTest(
        "maxkey_field",
        document={"A": MaxKey()},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="MaxKey field should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_ARRAY_FIELD_TESTS))
def test_anyElementTrue_non_array_field(collection, test):
    """Test $anyElementTrue errors when field resolves to non-array type."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$A"]}, test.document)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Non-array literal argument errors
# ---------------------------------------------------------------------------
NON_ARRAY_LITERAL_TESTS: list[AnyElementTrueTest] = [
    AnyElementTrueTest(
        "literal_string",
        expression={"$anyElementTrue": ["hello"]},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Literal string should error",
    ),
    AnyElementTrueTest(
        "literal_int",
        expression={"$anyElementTrue": [1]},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Literal int should error",
    ),
    AnyElementTrueTest(
        "literal_long",
        expression={"$anyElementTrue": [Int64(1)]},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Literal long should error",
    ),
    AnyElementTrueTest(
        "literal_double",
        expression={"$anyElementTrue": [1.5]},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Literal double should error",
    ),
    AnyElementTrueTest(
        "literal_decimal",
        expression={"$anyElementTrue": [Decimal128("1")]},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Literal decimal should error",
    ),
    AnyElementTrueTest(
        "literal_bool",
        expression={"$anyElementTrue": [True]},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Literal bool should error",
    ),
    AnyElementTrueTest(
        "literal_null",
        expression={"$anyElementTrue": [None]},
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Literal null should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_ARRAY_LITERAL_TESTS))
def test_anyElementTrue_non_array_literal(collection, test):
    """Test $anyElementTrue errors when argument is non-array literal."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Wrong argument count
# ---------------------------------------------------------------------------
def test_anyElementTrue_no_arguments(collection):
    """Test $anyElementTrue with no arguments errors."""
    result = execute_expression(collection, {"$anyElementTrue": []})
    assert_expression_result(
        result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR, msg="No arguments should error"
    )


def test_anyElementTrue_two_arguments(collection):
    """Test $anyElementTrue with two arguments errors."""
    result = execute_expression(collection, {"$anyElementTrue": [[1], [2]]})
    assert_expression_result(
        result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR, msg="Two arguments should error"
    )


# ---------------------------------------------------------------------------
# Field path resolving to non-array
# ---------------------------------------------------------------------------
def test_anyElementTrue_field_int(collection):
    """Test $anyElementTrue errors when field path resolves to int."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$x"]}, {"x": 5})
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Int field should error"
    )


def test_anyElementTrue_field_string(collection):
    """Test $anyElementTrue errors when field path resolves to string."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$x"]}, {"x": "hello"})
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="String field should error"
    )


def test_anyElementTrue_field_bool(collection):
    """Test $anyElementTrue errors when field path resolves to bool."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$x"]}, {"x": True})
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Bool field should error"
    )


def test_anyElementTrue_field_object(collection):
    """Test $anyElementTrue errors when field path resolves to object."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$x"]}, {"x": {"a": 1}}
    )
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Object field should error"
    )


def test_anyElementTrue_field_null(collection):
    """Test $anyElementTrue errors when field path resolves to null."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$x"]}, {"x": None})
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Null field should error"
    )


# ---------------------------------------------------------------------------
# Missing field errors
# ---------------------------------------------------------------------------
def test_anyElementTrue_missing_field(collection):
    """Test $anyElementTrue errors when field does not exist."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$nonexistent"]}, {"x": 1}
    )
    assert_expression_result(
        result, error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR, msg="Missing field should error"
    )


def test_anyElementTrue_missing_field_shorthand(collection):
    """Test $anyElementTrue shorthand errors when field does not exist."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": "$not_exist"}, {"x": 1})
    assert_expression_result(
        result,
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Missing field shorthand should error",
    )


# ---------------------------------------------------------------------------
# Non-existent field in literal array (resolves to missing/null, not error)
# ---------------------------------------------------------------------------
def test_anyElementTrue_nonexistent_in_literal_array(collection):
    """Test $anyElementTrue with non-existent field inside literal array returns false."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": [["$non_existent_field"]]}, {"x": 1}
    )
    assert_expression_result(
        result,
        expected=False,
        msg="Should return false for non-existent field in literal array resolving to missing",
    )


def test_anyElementTrue_nonexistent_plus_true_in_literal_array(collection):
    """Test $anyElementTrue with non-existent field plus true in literal array returns true."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": [["$non_existent_field", True]]}, {"x": 1}
    )
    assert_expression_result(
        result,
        expected=True,
        msg="Should return true for non-existent field combined with true in literal array",
    )


# ---------------------------------------------------------------------------
# System variables — resolve to non-array
# ---------------------------------------------------------------------------
def test_anyElementTrue_root_variable(collection):
    """Test $anyElementTrue with $$ROOT (object, not array) errors."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$$ROOT"]}, {"a": 1})
    assert_expression_result(
        result,
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Should error when ROOT variable resolves to object",
    )


def test_anyElementTrue_current_variable(collection):
    """Test $anyElementTrue with $$CURRENT (object, not array) errors."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$$CURRENT"]}, {"a": 1}
    )
    assert_expression_result(
        result,
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Should error when CURRENT variable resolves to object",
    )


def test_anyElementTrue_remove_variable(collection):
    """Test $anyElementTrue with $$REMOVE (missing) errors."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$$REMOVE"]}, {"a": 1})
    assert_expression_result(
        result,
        error_code=ANY_ELEMENTS_TRUE_NON_ARRAY_ERROR,
        msg="Should error when REMOVE variable resolves to missing",
    )
