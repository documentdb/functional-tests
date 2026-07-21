"""
Combination tests for $slice composed with other operators.
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

# Property [Composition]: $slice composes with array-producing and array-consuming operators.
SLICE_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "slice_on_concatArrays",
        expression={"$slice": [{"$concatArrays": ["$a", "$b"]}, 3]},
        doc={"a": [1, 2], "b": [3, 4, 5]},
        expected=[1, 2, 3],
        msg="$slice should slice the result of $concatArrays",
    ),
    ExpressionTestCase(
        "slice_on_map",
        expression={"$slice": [{"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}}, 2]},
        doc={"a": [1, 2, 3]},
        expected=[2, 4],
        msg="$slice should slice the result of $map",
    ),
    ExpressionTestCase(
        "slice_on_range",
        expression={"$slice": [{"$range": ["$start", "$end"]}, -3]},
        doc={"start": 0, "end": 10},
        expected=[7, 8, 9],
        msg="$slice should slice the result of $range",
    ),
    ExpressionTestCase(
        "reduce_on_slice",
        expression={
            "$reduce": {
                "input": {"$slice": ["$a", 3]},
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"a": [1, 2, 3, 4, 5]},
        expected=6,
        msg="$reduce should consume the result of $slice",
    ),
    ExpressionTestCase(
        "concatArrays_of_slices",
        expression={"$concatArrays": [{"$slice": ["$a", 2]}, {"$slice": ["$b", -1]}]},
        doc={"a": [1, 2, 3], "b": [4, 5, 6]},
        expected=[1, 2, 6],
        msg="$slice results should compose under $concatArrays",
    ),
    ExpressionTestCase(
        "slice_on_filter",
        expression={"$slice": [{"$filter": {"input": "$a", "cond": {"$gt": ["$$this", 2]}}}, 2]},
        doc={"a": [1, 2, 3, 4, 5]},
        expected=[3, 4],
        msg="$slice should slice the result of $filter",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SLICE_COMBINATION_TESTS))
def test_slice_combination(collection, test):
    """Test $slice composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
