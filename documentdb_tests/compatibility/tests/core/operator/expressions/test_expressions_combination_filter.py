"""
Combination tests for $filter composed with other operators.
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

FILTER_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="filter_then_size",
        expression={"$size": {"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=3,
        msg="Size of filtered array",
    ),
    ExpressionTestCase(
        id="map_then_filter",
        expression={
            "$filter": {
                "input": {"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
                "cond": {"$gt": ["$$this", 5]},
            }
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[6, 8, 10],
        msg="Should filter mapped array",
    ),
    ExpressionTestCase(
        id="isArray_on_filter_result",
        expression={"$isArray": {"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}}}},
        doc={"arr": [1, 2, 3]},
        expected=True,
        msg="$isArray on $filter result should return true",
    ),
    ExpressionTestCase(
        id="filter_result_into_reduce",
        expression={
            "$reduce": {
                "input": {"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 3]}}},
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=9,
        msg="$reduce of filtered result (4+5=9)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FILTER_COMBINATION_TESTS))
def test_filter_combination(collection, test):
    """Test $filter composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
