"""Tests for $setIsSubset argument-count errors, null operands, and non-array operand errors."""

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
    EXPRESSION_TYPE_MISMATCH_ERROR,
    SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
    SET_IS_SUBSET_SECOND_NOT_ARRAY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    MISSING,
)

# Property [Argument Count]: $setIsSubset takes exactly two operands, so any other
# operand-list arity or a non-array operand list errors.
SETISSUBSET_WRONG_ARG_COUNT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$setIsSubset": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$setIsSubset should return error for zero arguments",
    ),
    ExpressionTestCase(
        "one_arg",
        expression={"$setIsSubset": [[1, 2]]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$setIsSubset should return error for a single argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$setIsSubset": [[1], [2], [3]]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$setIsSubset should return error for three arguments",
    ),
    ExpressionTestCase(
        "non_array_wrapper",
        expression={"$setIsSubset": "not_an_array"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$setIsSubset should return error for a string operand list",
    ),
    ExpressionTestCase(
        "scalar_wrapper",
        expression={"$setIsSubset": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$setIsSubset should return error for a scalar operand list",
    ),
    ExpressionTestCase(
        "object_operand",
        expression={"$setIsSubset": {"a": [1, 2]}},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$setIsSubset should return error for an object operand list",
    ),
    ExpressionTestCase(
        "null_wrapper",
        expression={"$setIsSubset": None},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$setIsSubset should return error for a null operand list",
    ),
]

# Property [Null Operand]: a null operand is not an array and errors by position,
# reporting the first operand's code when both are null.
SETISSUBSET_NULL_OPERAND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first",
        expression={"$setIsSubset": [None, [1, 2]]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should return error for a null first operand",
    ),
    ExpressionTestCase(
        "null_second",
        expression={"$setIsSubset": [[1, 2], None]},
        error_code=SET_IS_SUBSET_SECOND_NOT_ARRAY_ERROR,
        msg="$setIsSubset should return error for a null second operand",
    ),
    ExpressionTestCase(
        "null_both",
        expression={"$setIsSubset": [None, None]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should report the first operand error when both operands are null",
    ),
    ExpressionTestCase(
        "null_first_empty_second",
        expression={"$setIsSubset": [None, []]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should return error for a null first operand with an empty second",
    ),
    ExpressionTestCase(
        "null_second_empty_first",
        expression={"$setIsSubset": [[], None]},
        error_code=SET_IS_SUBSET_SECOND_NOT_ARRAY_ERROR,
        msg="$setIsSubset should return error for a null second operand with an empty first",
    ),
]

# Property [Non-Array First Operand]: every non-array BSON type in the first
# operand position is rejected.
SETISSUBSET_NON_ARRAY_FIRST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_first",
        expression={"$setIsSubset": [val, [1, 2]]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg=f"$setIsSubset should return error for {tid} as the first operand",
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
        ("decimal_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Non-Array Second Operand]: every non-array BSON type in the second
# operand position is rejected.
SETISSUBSET_NON_ARRAY_SECOND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_second",
        expression={"$setIsSubset": [[1, 2], val]},
        error_code=SET_IS_SUBSET_SECOND_NOT_ARRAY_ERROR,
        msg=f"$setIsSubset should return error for {tid} as the second operand",
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
        ("decimal_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Both Operands Non-Array]: when both operands are non-array the first
# operand's error is reported.
SETISSUBSET_BOTH_NON_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "both_non_array",
        expression={"$setIsSubset": ["hello", 123]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should report the first operand error when both operands are non-array",
    ),
]

# Property [Missing Field]: a field path to an absent field resolves to missing
# and errors by position, reporting the first operand's code when both are missing.
SETISSUBSET_MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_first",
        doc={"b": [1, 2]},
        expression={"$setIsSubset": [MISSING, "$b"]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should return error when the first field is missing",
    ),
    ExpressionTestCase(
        "missing_second",
        doc={"a": [1, 2]},
        expression={"$setIsSubset": ["$a", MISSING]},
        error_code=SET_IS_SUBSET_SECOND_NOT_ARRAY_ERROR,
        msg="$setIsSubset should return error when the second field is missing",
    ),
    ExpressionTestCase(
        "missing_both",
        doc={"z": 1},
        expression={"$setIsSubset": ["$x", "$y"]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should report the first operand error when both fields are missing",
    ),
]

# Property [Field Resolves To Non-Array]: a field path that resolves to a
# non-array value errors by position, including a field present as null.
SETISSUBSET_FIELD_NON_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_resolves_int_first",
        doc={"a": 5},
        expression={"$setIsSubset": ["$a", [1]]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should error when the first field resolves to int",
    ),
    ExpressionTestCase(
        "field_resolves_string_first",
        doc={"a": "hello"},
        expression={"$setIsSubset": ["$a", [1]]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should error when the first field resolves to string",
    ),
    ExpressionTestCase(
        "field_resolves_null_first",
        doc={"a": None, "b": [1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        error_code=SET_IS_SUBSET_FIRST_NOT_ARRAY_ERROR,
        msg="$setIsSubset should error when the first field resolves to null",
    ),
    ExpressionTestCase(
        "field_resolves_int_second",
        doc={"b": 5},
        expression={"$setIsSubset": [[1], "$b"]},
        error_code=SET_IS_SUBSET_SECOND_NOT_ARRAY_ERROR,
        msg="$setIsSubset should error when the second field resolves to int",
    ),
    ExpressionTestCase(
        "field_resolves_null_second",
        doc={"a": [1], "b": None},
        expression={"$setIsSubset": ["$a", "$b"]},
        error_code=SET_IS_SUBSET_SECOND_NOT_ARRAY_ERROR,
        msg="$setIsSubset should error when the second field resolves to null",
    ),
]

SETISSUBSET_INVALID_TESTS: list[ExpressionTestCase] = (
    SETISSUBSET_WRONG_ARG_COUNT_TESTS
    + SETISSUBSET_NULL_OPERAND_TESTS
    + SETISSUBSET_NON_ARRAY_FIRST_TESTS
    + SETISSUBSET_NON_ARRAY_SECOND_TESTS
    + SETISSUBSET_BOTH_NON_ARRAY_TESTS
    + SETISSUBSET_MISSING_FIELD_TESTS
    + SETISSUBSET_FIELD_NON_ARRAY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETISSUBSET_INVALID_TESTS))
def test_setIsSubset_invalid(collection, test):
    """Test $setIsSubset argument-count, null, missing-field, and non-array errors."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
