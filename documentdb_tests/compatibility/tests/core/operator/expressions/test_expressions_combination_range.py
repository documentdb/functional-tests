"""
Combination tests for $range composed with other operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

RANGE_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="reverseArray_on_range",
        expression={"$reverseArray": {"$range": ["$start", "$end"]}},
        doc={"start": 0, "end": 5},
        expected=[4, 3, 2, 1, 0],
        msg="$reverseArray on $range result",
    ),
    ExpressionTestCase(
        id="concatArrays_two_ranges",
        expression={"$concatArrays": [{"$range": [0, 3]}, {"$range": [3, 6]}]},
        doc={"x": 1},
        expected=[0, 1, 2, 3, 4, 5],
        msg="$concatArrays on two $range results",
    ),
    ExpressionTestCase(
        id="in_on_range",
        expression={"$in": [5, {"$range": ["$start", "$end"]}]},
        doc={"start": 0, "end": 10},
        expected=True,
        msg="$in on $range result",
    ),
    ExpressionTestCase(
        id="isArray_on_range",
        expression={"$isArray": {"$range": [0, 3]}},
        doc={"x": 1},
        expected=True,
        msg="$isArray on $range result should return true",
    ),
    ExpressionTestCase(
        id="in_miss_on_range",
        expression={"$in": [5, {"$range": [0, 5]}]},
        doc={"x": 1},
        expected=False,
        msg="5 should not be in [0..4] (exclusive end)",
    ),
    ExpressionTestCase(
        id="self_nesting_start",
        expression={"$range": [{"$arrayElemAt": [{"$range": [2, 5]}, 0]}, 10]},
        doc={"x": 1},
        expected=[2, 3, 4, 5, 6, 7, 8, 9],
        msg="Start from inner range",
    ),
    ExpressionTestCase(
        id="self_nesting_end",
        expression={"$range": [0, {"$size": {"$range": [0, 5]}}]},
        doc={"x": 1},
        expected=[0, 1, 2, 3, 4],
        msg="End from size of inner range",
    ),
    ExpressionTestCase(
        id="indexOfArray_on_range",
        expression={"$indexOfArray": [{"$range": [0, 10]}, 7]},
        doc={"x": 1},
        expected=7,
        msg="Index of 7 in range 0..9 should be 7",
    ),
    ExpressionTestCase(
        id="output_type_is_int",
        expression={"$type": {"$arrayElemAt": [{"$range": [0, 1]}, 0]}},
        doc={"x": 1},
        expected="int",
        msg="Output element should be int type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RANGE_COMBINATION_TESTS))
def test_range_combination(collection, test):
    """Test $range composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
