"""
Expression and field path tests for $reduce expression.

Tests field path lookups, composite paths, system variables,
null/missing propagation via expressions, nested $reduce, and
access to outer document fields in the 'in' expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Path Input]: $reduce resolves a field path to the input array.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        expression={
            "$reduce": {"input": "$a.b", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"a": {"b": [1, 2, 3]}},
        expected=6,
        msg="$reduce should resolve a nested field path for input",
    ),
    ExpressionTestCase(
        "composite_array_path",
        expression={
            "$reduce": {"input": "$a.b", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        expected=6,
        msg="$reduce should resolve a composite array path for input",
    ),
]

# Property [Variable Input]: $reduce reads its input from bound and system variables.
LET_AND_VARIABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "let_variable",
        expression={
            "$let": {
                "vars": {"arr": "$values"},
                "in": {
                    "$reduce": {
                        "input": "$$arr",
                        "initialValue": 0,
                        "in": {"$add": ["$$value", "$$this"]},
                    }
                },
            }
        },
        doc={"values": [1, 2, 3]},
        expected=6,
        msg="$reduce should read input from a $let variable",
    ),
    ExpressionTestCase(
        "root_variable",
        expression={
            "$reduce": {
                "input": "$$ROOT.values",
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"_id": 1, "values": [10, 20]},
        expected=30,
        msg="$reduce should read input via $$ROOT",
    ),
]

# Property [Null/Missing Input]: a missing or removed input field propagates null.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field",
        expression={
            "$reduce": {
                "input": "$nonexistent",
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"other": 1},
        expected=None,
        msg="$reduce should return null for a missing input field",
    ),
    ExpressionTestCase(
        "missing_input_type_is_null",
        expression={
            "$type": {
                "$reduce": {
                    "input": "$nonexistent",
                    "initialValue": 0,
                    "in": {"$add": ["$$value", "$$this"]},
                }
            }
        },
        doc={"x": 1},
        expected="null",
        msg="$reduce should produce null type for a missing input field",
    ),
    ExpressionTestCase(
        "remove_variable",
        expression={
            "$reduce": {
                "input": "$$REMOVE",
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"x": 1},
        expected=None,
        msg="$reduce should propagate null for $$REMOVE input",
    ),
]

# Property [In Expression Context]: 'in' can nest $reduce and reference outer fields.
MISC_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_reduce",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {
                    "$add": [
                        "$$value",
                        {
                            "$reduce": {
                                "input": "$$this",
                                "initialValue": 0,
                                "in": {"$add": ["$$value", "$$this"]},
                            }
                        },
                    ]
                },
            }
        },
        doc={"arr": [[1, 2], [3, 4]]},
        expected=10,
        msg="$reduce should support a nested $reduce",
    ),
    ExpressionTestCase(
        "access_outer_field",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {"$add": ["$$value", {"$multiply": ["$$this", "$factor"]}]},
            }
        },
        doc={"arr": [1, 2, 3], "factor": 10},
        expected=60,
        msg="$reduce should access an outer document field in 'in'",
    ),
    ExpressionTestCase(
        "field_ref_in_in",
        expression={
            "$reduce": {
                "input": [1, 2, 3, 4],
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this", "$val"]},
            }
        },
        doc={"val": 1},
        expected=14,
        msg="$reduce should add an outer field ref each iteration",
    ),
]

# Property [InitialValue Expression]: initialValue accepts field references and expressions.
INITIAL_VALUE_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "initialValue_from_field",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": "$init",
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2, 3], "init": 4},
        expected=10,
        msg="$reduce should accept initialValue from a field reference",
    ),
    ExpressionTestCase(
        "initialValue_from_expression",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": {"$multiply": [2, 2]},
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2, 3]},
        expected=10,
        msg="$reduce should accept initialValue from an expression",
    ),
]

# Property [Expression Input]: input accepts array expressions and $literal arrays.
EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expression_input",
        expression={
            "$reduce": {
                "input": ["$x", "$y", "$z"],
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"x": 1, "y": 2, "z": 3},
        expected=6,
        msg="$reduce should resolve an array expression input",
    ),
    ExpressionTestCase(
        "literal_input",
        expression={
            "$reduce": {
                "input": {"$literal": [5, 10, 15]},
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={},
        expected=30,
        msg="$reduce should accept a $literal array input",
    ),
]

ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + LET_AND_VARIABLE_TESTS
    + NULL_MISSING_EXPR_TESTS
    + MISC_EXPR_TESTS
    + INITIAL_VALUE_EXPR_TESTS
    + EXPRESSION_INPUT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_reduce_expression(collection, test):
    """Test $reduce with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
