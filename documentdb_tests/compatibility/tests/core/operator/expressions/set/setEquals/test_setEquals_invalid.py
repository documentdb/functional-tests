"""Tests for $setEquals null handling, argument-count errors, and non-array operand errors."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
    SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
    SET_EQUALS_WRONG_ARG_COUNT_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    MISSING,
)

# Property [Null Elements]: a null element inside an array is an ordinary value
# subject to set membership, so the operator succeeds.
SETEQUALS_NULL_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_elem_both",
        doc={"a": [None, None], "b": [None]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for null elements in both arrays",
    ),
    ExpressionTestCase(
        "null_elem_mixed",
        doc={"a": [None, 1], "b": [1, None]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for a null element alongside other elements",
    ),
    ExpressionTestCase(
        "null_elem_vs_int",
        doc={"a": [None], "b": [1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for a null element versus an int element",
    ),
    ExpressionTestCase(
        "null_elem_vs_empty",
        doc={"a": [None], "b": []},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for a null element versus an empty array",
    ),
]

# Property [Argument Count]: $setEquals requires two or more array operands, so a
# non-array operand list or fewer than two operands errors.
SETEQUALS_WRONG_ARG_COUNT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$setEquals": []},
        error_code=SET_EQUALS_WRONG_ARG_COUNT_ERROR,
        msg="$setEquals should return error for zero arguments",
    ),
    ExpressionTestCase(
        "one_arg",
        expression={"$setEquals": [[1, 2]]},
        error_code=SET_EQUALS_WRONG_ARG_COUNT_ERROR,
        msg="$setEquals should return error for a single argument",
    ),
    ExpressionTestCase(
        "non_array_wrapper",
        expression={"$setEquals": "not_an_array"},
        error_code=SET_EQUALS_WRONG_ARG_COUNT_ERROR,
        msg="$setEquals should return error for a string operand list",
    ),
    ExpressionTestCase(
        "scalar_wrapper",
        expression={"$setEquals": 1},
        error_code=SET_EQUALS_WRONG_ARG_COUNT_ERROR,
        msg="$setEquals should return error for a scalar operand list",
    ),
    ExpressionTestCase(
        "object_operand",
        expression={"$setEquals": {"a": [1, 2]}},
        error_code=SET_EQUALS_WRONG_ARG_COUNT_ERROR,
        msg="$setEquals should return error for an object operand list",
    ),
]

# Property [Null Literal Operand]: a null literal operand is not an array and
# errors in any position, including among three or more operands.
SETEQUALS_NULL_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first",
        expression={"$setEquals": [None, [1, 2]]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg="$setEquals should return error for a null first operand",
    ),
    ExpressionTestCase(
        "null_second",
        expression={"$setEquals": [[1, 2], None]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg="$setEquals should return error for a null second operand",
    ),
    ExpressionTestCase(
        "null_both",
        expression={"$setEquals": [None, None]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg="$setEquals should return error for two null operands",
    ),
    ExpressionTestCase(
        "null_middle",
        expression={"$setEquals": [[1, 2], None, [1, 2]]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg="$setEquals should return error for a null operand in the middle of three",
    ),
    ExpressionTestCase(
        "null_first_of_three",
        expression={"$setEquals": [None, [1], [2]]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg="$setEquals should return error for a null first operand of three",
    ),
    ExpressionTestCase(
        "null_last_of_three",
        expression={"$setEquals": [[1], [1], None]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg="$setEquals should return error for a null last operand of three",
    ),
]

# Property [Non-Array Literal First]: a non-array literal first operand errors,
# and every non-array BSON type is rejected.
SETEQUALS_NON_ARRAY_FIRST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_first",
        expression={"$setEquals": [val, [1, 2]]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg=f"$setEquals should return error for {tid} as the first operand",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("string", "hello"),
        ("bool", True),
        ("object", {"a": 1}),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")),
        ("regex", Regex("abc", "")),
        ("javascript", Code("function(){}")),
        ("binary", Binary(b"\x01", 0)),
        ("timestamp", Timestamp(1, 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("nan", FLOAT_NAN),
        ("infinity", FLOAT_INFINITY),
        ("decimal_nan", DECIMAL128_NAN),
        ("decimal_infinity", DECIMAL128_INFINITY),
    ]
]

# Property [Non-Array Literal Second]: a non-array literal second operand errors,
# and every non-array BSON type is rejected.
SETEQUALS_NON_ARRAY_SECOND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_second",
        expression={"$setEquals": [[1, 2], val]},
        error_code=SET_EQUALS_LITERAL_NON_ARRAY_ERROR,
        msg=f"$setEquals should return error for {tid} as the second operand",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("string", "hello"),
        ("bool", True),
        ("object", {"a": 1}),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")),
        ("regex", Regex("abc", "")),
        ("javascript", Code("function(){}")),
        ("binary", Binary(b"\x01", 0)),
        ("timestamp", Timestamp(1, 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("nan", FLOAT_NAN),
        ("infinity", FLOAT_INFINITY),
        ("decimal_nan", DECIMAL128_NAN),
        ("decimal_infinity", DECIMAL128_INFINITY),
    ]
]

# Property [Missing Field]: a field path to an absent field resolves to missing
# and errors at runtime rather than being treated as an array.
SETEQUALS_MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_first",
        doc={"b": [1, 2]},
        expression={"$setEquals": [MISSING, "$b"]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should return error when the first field is missing",
    ),
    ExpressionTestCase(
        "missing_second",
        doc={"a": [1, 2]},
        expression={"$setEquals": ["$a", MISSING]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should return error when the second field is missing",
    ),
    ExpressionTestCase(
        "missing_both",
        doc={"z": 1},
        expression={"$setEquals": ["$x", "$y"]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should return error when both fields are missing",
    ),
]

# Property [Field Resolves To Non-Array]: a field path that resolves to a
# non-array value errors at runtime, including a field present as null.
SETEQUALS_FIELD_NON_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_resolves_int",
        doc={"a": 5},
        expression={"$setEquals": ["$a", [1]]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a field resolves to int",
    ),
    ExpressionTestCase(
        "field_resolves_int_second",
        doc={"a": 5},
        expression={"$setEquals": [[1], "$a"]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a second-position field resolves to int",
    ),
    ExpressionTestCase(
        "field_resolves_string",
        doc={"a": "hello"},
        expression={"$setEquals": ["$a", [1]]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a field resolves to string",
    ),
    ExpressionTestCase(
        "field_resolves_string_second",
        doc={"a": "hello"},
        expression={"$setEquals": [[1], "$a"]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a second-position field resolves to string",
    ),
    ExpressionTestCase(
        "field_resolves_object",
        doc={"a": {"b": 1}},
        expression={"$setEquals": ["$a", [1]]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a field resolves to object",
    ),
    ExpressionTestCase(
        "field_resolves_object_second",
        doc={"a": {"b": 1}},
        expression={"$setEquals": [[1], "$a"]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a second-position field resolves to object",
    ),
    ExpressionTestCase(
        "field_resolves_null",
        doc={"a": None},
        expression={"$setEquals": ["$a", [1]]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a field resolves to null",
    ),
    ExpressionTestCase(
        "field_resolves_null_second",
        doc={"a": None},
        expression={"$setEquals": [[1], "$a"]},
        error_code=SET_EQUALS_RUNTIME_NON_ARRAY_ERROR,
        msg="$setEquals should error when a second-position field resolves to null",
    ),
]

SETEQUALS_ERROR_TESTS: list[ExpressionTestCase] = (
    SETEQUALS_WRONG_ARG_COUNT_TESTS
    + SETEQUALS_NULL_LITERAL_TESTS
    + SETEQUALS_NON_ARRAY_FIRST_TESTS
    + SETEQUALS_NON_ARRAY_SECOND_TESTS
    + SETEQUALS_MISSING_FIELD_TESTS
    + SETEQUALS_FIELD_NON_ARRAY_TESTS
)

SETEQUALS_INVALID_TESTS: list[ExpressionTestCase] = (
    SETEQUALS_NULL_ELEMENT_TESTS + SETEQUALS_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETEQUALS_INVALID_TESTS))
def test_setEquals_invalid(collection, test):
    """Test $setEquals null, argument-count, missing-field, and non-array handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
