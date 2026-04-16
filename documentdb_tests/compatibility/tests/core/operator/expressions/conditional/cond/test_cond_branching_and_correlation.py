"""Tests for $cond syntax equivalence, short-circuit evaluation, and $cond vs $ifNull
behavioral differences — verifying object and array syntax produce identical results,
lazy branch evaluation avoids runtime errors, and parse-time validation catches syntax errors."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

SYNTAX_EQUIV_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_true",
        expression={"$cond": {"if": True, "then": "a", "else": "b"}},
        expected="a",
        msg="Object syntax true → a",
    ),
    ExpressionTestCase(
        "arr_true",
        expression={"$cond": [True, "a", "b"]},
        expected="a",
        msg="Array syntax true → a",
    ),
    ExpressionTestCase(
        "obj_false",
        expression={"$cond": {"if": False, "then": "a", "else": "b"}},
        expected="b",
        msg="Object syntax false → b",
    ),
    ExpressionTestCase(
        "arr_false",
        expression={"$cond": [False, "a", "b"]},
        expected="b",
        msg="Array syntax false → b",
    ),
]

COND_VS_IFNULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_string_truthy_in_cond",
        expression={"$cond": {"if": "", "then": "then", "else": "else"}},
        expected="then",
        msg="$cond: empty string → then (truthy), unlike $ifNull which would replace it",
    ),
]

LITERAL_TESTS = SYNTAX_EQUIV_LITERAL_TESTS + COND_VS_IFNULL_TESTS


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_cond_branching_literal(collection, test):
    """Test $cond syntax equivalence and $cond vs $ifNull with literal expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


SYNTAX_EQUIV_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_field_paths",
        expression={"$cond": {"if": "$flag", "then": "$x", "else": "$y"}},
        doc={"flag": True, "x": 10, "y": 20},
        expected=10,
        msg="Object syntax with field paths",
    ),
    ExpressionTestCase(
        "arr_field_paths",
        expression={"$cond": ["$flag", "$x", "$y"]},
        doc={"flag": True, "x": 10, "y": 20},
        expected=10,
        msg="Array syntax with field paths",
    ),
    ExpressionTestCase(
        "obj_gt_condition",
        expression={"$cond": {"if": {"$gt": ["$a", 0]}, "then": "pos", "else": "neg"}},
        doc={"a": 5},
        expected="pos",
        msg="Object syntax with $gt condition",
    ),
    ExpressionTestCase(
        "arr_gt_condition",
        expression={"$cond": [{"$gt": ["$a", 0]}, "pos", "neg"]},
        doc={"a": 5},
        expected="pos",
        msg="Array syntax with $gt condition",
    ),
]

LAZY_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "lazy_else_divide_by_zero",
        expression={
            "$cond": {"if": "$flag", "then": "$val", "else": {"$divide": ["$val", "$zero"]}}
        },
        doc={"flag": True, "val": 1, "zero": 0},
        expected=1,
        msg="Else not evaluated, no divide-by-zero error",
    ),
    ExpressionTestCase(
        "lazy_then_divide_by_zero",
        expression={
            "$cond": {"if": "$flag", "then": {"$divide": ["$val", "$zero"]}, "else": "$val"}
        },
        doc={"flag": False, "val": 1, "zero": 0},
        expected=1,
        msg="Then not evaluated, no divide-by-zero error",
    ),
    ExpressionTestCase(
        "lazy_then_divide_by_zero_with_syntax_error",
        expression={"$cond": {"if": "$flag", "then": {"$divide": ["$val"]}, "else": "$val"}},
        doc={"flag": False, "val": 1, "zero": 0},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Syntax errors are caught at parse time even in untaken branches",
    ),
]

INSERT_TESTS = SYNTAX_EQUIV_FIELD_TESTS + LAZY_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_cond_branching_insert(collection, test):
    """Test $cond syntax equivalence and short-circuit evaluation with field-based expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
