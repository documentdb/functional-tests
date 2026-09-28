"""Tests for $setIntersection null propagation, missing fields, and non-array errors."""

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
from documentdb_tests.framework.error_codes import SET_INTERSECTION_NON_ARRAY_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    MISSING,
)

# Property [Null Propagation]: a null operand makes the whole result null,
# regardless of position or number of operands.
SETINTERSECTION_NULL_PROP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first",
        doc={"a": None, "b": [1, 2, 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=None,
        msg="$setIntersection should return null when the first operand is null",
    ),
    ExpressionTestCase(
        "null_second",
        doc={"a": [1, 2, 3], "b": None},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=None,
        msg="$setIntersection should return null when the second operand is null",
    ),
    ExpressionTestCase(
        "null_both",
        doc={"a": None, "b": None},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=None,
        msg="$setIntersection should return null when both operands are null",
    ),
    ExpressionTestCase(
        "null_among_many",
        doc={"a": [1, 2], "b": None, "c": [1, 2]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=None,
        msg="$setIntersection should return null when a null operand appears among many",
    ),
    ExpressionTestCase(
        "null_and_empty",
        doc={"a": [1, 2], "b": None, "c": []},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=None,
        msg="$setIntersection should return null when null takes precedence over an empty operand",
    ),
]

# Property [Null Elements]: a null element inside an array is an ordinary value
# subject to set membership and dedup.
SETINTERSECTION_NULL_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_in_both",
        doc={"a": [None, 1, 2], "b": [None, 2, 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[None, 2],
        msg="$setIntersection should return the null element when present in both arrays",
    ),
    ExpressionTestCase(
        "null_only_element",
        doc={"a": [None], "b": [None]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[None],
        msg="$setIntersection should return null as the only common element",
    ),
    ExpressionTestCase(
        "null_in_one_only",
        doc={"a": [None, 1], "b": [2, 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when null is in one array only",
    ),
    ExpressionTestCase(
        "null_element_not_in_second",
        doc={"a": [None, 1], "b": [1, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1],
        msg="$setIntersection should return the non-null common when null is not in second",
    ),
]

# Property [Missing Field]: a field path to an absent field resolves to null and
# propagates null through the operator.
SETINTERSECTION_MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_first",
        doc={"b": [1, 2, 3]},
        expression={"$setIntersection": [MISSING, "$b"]},
        expected=None,
        msg="$setIntersection should return null when the first field is missing",
    ),
    ExpressionTestCase(
        "missing_second",
        doc={"a": [1, 2, 3]},
        expression={"$setIntersection": ["$a", MISSING]},
        expected=None,
        msg="$setIntersection should return null when the second field is missing",
    ),
    ExpressionTestCase(
        "missing_both",
        doc={"z": 1},
        expression={"$setIntersection": ["$x", "$y"]},
        expected=None,
        msg="$setIntersection should return null when both fields are missing",
    ),
]

# Property [Null Precedence]: a null operand propagates null before a non-array
# operand in another position is validated.
SETINTERSECTION_NULL_PRECEDENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first_non_array_second",
        expression={"$setIntersection": [None, 1]},
        expected=None,
        msg="$setIntersection should propagate null from a null operand rather than "
        "error on a non-array sibling",
    ),
]

SETINTERSECTION_SUCCESS_TESTS: list[ExpressionTestCase] = (
    SETINTERSECTION_NULL_PROP_TESTS
    + SETINTERSECTION_NULL_ELEMENT_TESTS
    + SETINTERSECTION_MISSING_FIELD_TESTS
    + SETINTERSECTION_NULL_PRECEDENCE_TESTS
)

# Property [Non-Array First]: a non-array first operand errors, and every
# non-array BSON type is rejected.
SETINTERSECTION_NON_ARRAY_FIRST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_first",
        doc={"a": val, "b": [1, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg=f"$setIntersection should return error for {tid} as first operand",
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

# Property [Non-Array Second]: a non-array second operand errors, and every
# non-array BSON type is rejected.
SETINTERSECTION_NON_ARRAY_SECOND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"{tid}_second",
        doc={"a": [1, 2], "b": val},
        expression={"$setIntersection": ["$a", "$b"]},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg=f"$setIntersection should return error for {tid} as second operand",
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

# Property [Non-Array Literal Operand]: a literal operand list that is not made of
# arrays is rejected.
SETINTERSECTION_NON_ARRAY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_literal",
        expression={"$setIntersection": 1},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg="$setIntersection should return error for an integer literal operand",
    ),
    ExpressionTestCase(
        "non_array_elements",
        expression={"$setIntersection": [1, 2, 3]},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg="$setIntersection should return error for non-array elements as operands",
    ),
]

# Property [Field Resolves To Non-Array]: a field path that resolves to a
# non-array value errors.
SETINTERSECTION_FIELD_NON_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_resolves_int",
        doc={"a": 5},
        expression={"$setIntersection": ["$a", [1]]},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg="$setIntersection should error when a field resolves to int",
    ),
    ExpressionTestCase(
        "field_resolves_string",
        doc={"a": "hello"},
        expression={"$setIntersection": ["$a", [1]]},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg="$setIntersection should error when a field resolves to string",
    ),
    ExpressionTestCase(
        "field_resolves_object",
        doc={"a": {"b": 1}},
        expression={"$setIntersection": ["$a", [1]]},
        error_code=SET_INTERSECTION_NON_ARRAY_ERROR,
        msg="$setIntersection should error when a field resolves to object",
    ),
]

SETINTERSECTION_ERROR_TESTS: list[ExpressionTestCase] = (
    SETINTERSECTION_NON_ARRAY_FIRST_TESTS
    + SETINTERSECTION_NON_ARRAY_SECOND_TESTS
    + SETINTERSECTION_NON_ARRAY_LITERAL_TESTS
    + SETINTERSECTION_FIELD_NON_ARRAY_TESTS
)

SETINTERSECTION_INVALID_TESTS: list[ExpressionTestCase] = (
    SETINTERSECTION_SUCCESS_TESTS + SETINTERSECTION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETINTERSECTION_INVALID_TESTS))
def test_setIntersection_invalid(collection, test):
    """Test $setIntersection null, missing, and non-array handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg, ignore_order=True
    )
