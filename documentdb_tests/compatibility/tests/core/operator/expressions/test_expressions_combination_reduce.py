"""
Combination tests for $reduce composed with other operators.
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

# Property [Operator Composition]: $reduce composes correctly with $range, $map, $size,
# $cond, and comparison operators.
REDUCE_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="reduce_sum_on_range",
        expression={
            "$reduce": {
                "input": {"$range": [1, 6]},
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"_placeholder": 1},
        expected=15,
        msg="Should sum $range(1,6)",
    ),
    ExpressionTestCase(
        id="reduce_on_map",
        expression={
            "$reduce": {
                "input": {"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2, 3]},
        expected=12,
        msg="Should sum mapped array",
    ),
    ExpressionTestCase(
        id="reduce_flatten_then_size",
        expression={
            "$size": {
                "$reduce": {
                    "input": "$arr",
                    "initialValue": [],
                    "in": {"$concatArrays": ["$$value", "$$this"]},
                }
            }
        },
        doc={"arr": [[1, 2], [3], [4, 5, 6]]},
        expected=6,
        msg="Size of flattened array",
    ),
    ExpressionTestCase(
        id="max_value",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {
                    "$cond": {
                        "if": {"$gt": ["$$this", "$$value"]},
                        "then": "$$this",
                        "else": "$$value",
                    }
                },
            }
        },
        doc={"arr": [3, 1, 4, 1, 5, 9, 2, 6]},
        expected=9,
        msg="Should find max value",
    ),
    ExpressionTestCase(
        id="null_elements_count_non_null",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {
                    "$cond": {
                        "if": {"$ne": ["$$this", None]},
                        "then": {"$add": ["$$value", 1]},
                        "else": "$$value",
                    }
                },
            }
        },
        doc={"arr": [1, None, 2, None, 3]},
        expected=3,
        msg="Should count non-null elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REDUCE_COMBINATION_TESTS))
def test_reduce_combination(collection, test):
    """Test $reduce composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
