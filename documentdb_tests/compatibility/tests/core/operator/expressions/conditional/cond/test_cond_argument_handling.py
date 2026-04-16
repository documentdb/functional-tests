"""Tests for $cond argument handling — valid/invalid argument counts, formats, and error codes."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    COND_EXTRA_FIELD_ERROR,
    COND_MISSING_ELSE_ERROR,
    COND_MISSING_IF_ERROR,
    COND_MISSING_THEN_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

OBJECT_VALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_all_three_fields",
        expression={"$cond": {"if": True, "then": "yes", "else": "no"}},
        expected="yes",
        msg="Should succeed with all three fields",
    ),
    ExpressionTestCase(
        "obj_field_order_then_if_else",
        expression={"$cond": {"then": 1, "if": True, "else": 2}},
        expected=1,
        msg="Should succeed regardless of field order",
    ),
    ExpressionTestCase(
        "obj_field_order_else_if_then",
        expression={"$cond": {"else": 2, "if": True, "then": 1}},
        expected=1,
        msg="Should succeed with else-if-then order",
    ),
]

ARRAY_VALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_3_elements",
        expression={"$cond": [True, "yes", "no"]},
        expected="yes",
        msg="Should succeed with 3-element array",
    ),
    ExpressionTestCase(
        "array_string_condition",
        expression={"$cond": ["non_field_path_string", "then", "else"]},
        expected="then",
        msg="Plain string (not field path) in array syntax is truthy",
    ),
]

OBJECT_MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_missing_if",
        expression={"$cond": {"then": 1, "else": 2}},
        error_code=COND_MISSING_IF_ERROR,
        msg="Should error when 'if' is missing",
    ),
    ExpressionTestCase(
        "obj_missing_then",
        expression={"$cond": {"if": True, "else": 2}},
        error_code=COND_MISSING_THEN_ERROR,
        msg="Should error when 'then' is missing",
    ),
    ExpressionTestCase(
        "obj_missing_else",
        expression={"$cond": {"if": True, "then": 1}},
        error_code=COND_MISSING_ELSE_ERROR,
        msg="Should error when 'else' is missing",
    ),
    ExpressionTestCase(
        "obj_empty_object",
        expression={"$cond": {}},
        error_code=COND_MISSING_IF_ERROR,
        msg="Should error with empty object",
    ),
    ExpressionTestCase(
        "obj_only_if",
        expression={"$cond": {"if": True}},
        error_code=COND_MISSING_THEN_ERROR,
        msg="Should error with only 'if' field",
    ),
]

OBJECT_EXTRA_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_extra_field_with_all_three",
        expression={"$cond": {"if": True, "then": 1, "else": 2, "dummy": 234}},
        error_code=COND_EXTRA_FIELD_ERROR,
        msg="Should error with extra unrecognized field",
    ),
    ExpressionTestCase(
        "obj_extra_field_missing_then",
        expression={"$cond": {"if": 1, "else": 2, "dummy": 234}},
        error_code=COND_EXTRA_FIELD_ERROR,
        msg="Should error with extra field even when 'then' missing",
    ),
]

ARRAY_WRONG_COUNT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_0_elements",
        expression={"$cond": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with empty array",
    ),
    ExpressionTestCase(
        "array_1_element",
        expression={"$cond": [True]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with 1 element",
    ),
    ExpressionTestCase(
        "array_2_elements",
        expression={"$cond": [True, 1]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with 2 elements",
    ),
    ExpressionTestCase(
        "array_4_elements",
        expression={"$cond": [True, 1, 2, 3]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with 4 elements",
    ),
]

INVALID_FORMAT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "scalar_true",
        expression={"$cond": True},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with scalar boolean",
    ),
    ExpressionTestCase(
        "scalar_null",
        expression={"$cond": None},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with null",
    ),
    ExpressionTestCase(
        "scalar_int",
        expression={"$cond": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with scalar integer",
    ),
    ExpressionTestCase(
        "scalar_string",
        expression={"$cond": "string"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with scalar string",
    ),
    ExpressionTestCase(
        "nested_null_in_then",
        expression={"$cond": [True, {"$cond": None}, False]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error with null nested in then-branch $cond",
    ),
]

ALL_TESTS = (
    OBJECT_VALID_TESTS
    + ARRAY_VALID_TESTS
    + OBJECT_MISSING_FIELD_TESTS
    + OBJECT_EXTRA_FIELD_TESTS
    + ARRAY_WRONG_COUNT_TESTS
    + INVALID_FORMAT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cond_argument_handling(collection, test):
    """Test $cond argument handling — valid/invalid argument counts, formats, and error codes."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
