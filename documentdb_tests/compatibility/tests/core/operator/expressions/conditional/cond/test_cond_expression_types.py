"""Tests for $cond expression type coverage — field path, expression operator,
system variable, array expression, and object expression in each input position."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

IF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "if_field_path",
        expression={"$cond": {"if": "$flag", "then": "yes", "else": "no"}},
        doc={"flag": True},
        expected="yes",
        msg="Field path truthy → then",
    ),
    ExpressionTestCase(
        "if_system_variable",
        expression={"$cond": {"if": "$$ROOT.flag", "then": "yes", "else": "no"}},
        doc={"flag": True},
        expected="yes",
        msg="$$ROOT.flag truthy → then",
    ),
    ExpressionTestCase(
        "if_expression_operator",
        expression={"$cond": {"if": {"$gt": ["$x", 0]}, "then": "yes", "else": "no"}},
        doc={"x": 5},
        expected="yes",
        msg="Expression operator → then",
    ),
]

BRANCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "then_field_path",
        expression={"$cond": {"if": True, "then": "$val", "else": 0}},
        doc={"val": 99},
        expected=99,
        msg="Field path in then",
    ),
    ExpressionTestCase(
        "then_expression_operator",
        expression={"$cond": {"if": True, "then": {"$add": ["$x", 1]}, "else": 0}},
        doc={"x": 10},
        expected=11,
        msg="Expression operator in then",
    ),
    ExpressionTestCase(
        "then_system_variable",
        expression={"$cond": {"if": True, "then": "$$ROOT.val", "else": 0}},
        doc={"val": 77},
        expected=77,
        msg="$$ROOT.val in then",
    ),
    ExpressionTestCase(
        "then_array_expression",
        expression={"$cond": {"if": True, "then": ["$x", "$y"], "else": 0}},
        doc={"x": 1, "y": 2},
        expected=[1, 2],
        msg="Array expression in then",
    ),
    ExpressionTestCase(
        "then_object_expression",
        expression={"$cond": {"if": True, "then": {"a": "$x"}, "else": 0}},
        doc={"x": 5},
        expected={"a": 5},
        msg="Object expression in then",
    ),
    ExpressionTestCase(
        "else_field_path",
        expression={"$cond": {"if": False, "then": 0, "else": "$val"}},
        doc={"val": 99},
        expected=99,
        msg="Field path in else",
    ),
    ExpressionTestCase(
        "else_expression_operator",
        expression={"$cond": {"if": False, "then": 0, "else": {"$subtract": ["$x", 1]}}},
        doc={"x": 10},
        expected=9,
        msg="Expression operator in else",
    ),
    ExpressionTestCase(
        "else_system_variable",
        expression={"$cond": {"if": False, "then": 0, "else": "$$ROOT.val"}},
        doc={"val": 77},
        expected=77,
        msg="$$ROOT.val in else",
    ),
    ExpressionTestCase(
        "else_array_expression",
        expression={"$cond": {"if": False, "then": 0, "else": ["$x", "$y"]}},
        doc={"x": 1, "y": 2},
        expected=[1, 2],
        msg="Array expression in else",
    ),
    ExpressionTestCase(
        "else_object_expression",
        expression={"$cond": {"if": False, "then": 0, "else": {"a": "$x"}}},
        doc={"x": 5},
        expected={"a": 5},
        msg="Object expression in else",
    ),
]

ARRAY_WRAPPING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "if_array_wrapping_missing",
        expression={"$cond": [["$inv"], "then", "else"]},
        doc={"x": 1},
        expected="then",
        msg="Array wrapping missing field is truthy",
    ),
    ExpressionTestCase(
        "if_nested_array_wrapping",
        expression={"$cond": [[["$inv"]], "then", "else"]},
        doc={"x": 1},
        expected="then",
        msg="Nested array wrapping missing field is truthy",
    ),
    ExpressionTestCase(
        "then_array_missing_field",
        expression={"$cond": [True, ["$xinv"], "else"]},
        doc={"x": 1},
        expected=[None],
        msg="Array with missing field returns [null]",
    ),
    ExpressionTestCase(
        "else_array_missing_field",
        expression={"$cond": [False, "then", ["$zinv"]]},
        doc={"x": 1},
        expected=[None],
        msg="Array with missing field in else returns [null]",
    ),
]

COMPLEX_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_three_as_expressions",
        expression={
            "$cond": {
                "if": {"$gt": ["$a", 10]},
                "then": {"$add": ["$a", 1]},
                "else": {"$concat": ["$s", "-suffix"]},
            }
        },
        doc={"a": 5, "s": "hello"},
        expected="hello-suffix",
        msg="All three args as expressions, condition false",
    ),
]


ALL_TESTS = IF_TESTS + BRANCH_TESTS + ARRAY_WRAPPING_TESTS + COMPLEX_EXPRESSION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cond_expression_types(collection, test):
    """Test $cond with field paths, operators, system variables, and arrays in if/then/else."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
