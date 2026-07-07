"""
Combination tests for $map composed with other operators.
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

MAP_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="map_on_range",
        expression={
            "$map": {"input": {"$range": [0, 5]}, "in": {"$multiply": ["$$this", "$$this"]}}
        },
        doc={"_placeholder": 1},
        expected=[0, 1, 4, 9, 16],
        msg="Should map squares over $range result",
    ),
    ExpressionTestCase(
        id="map_with_concatArrays",
        expression={
            "$concatArrays": [
                {"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}},
                {"$map": {"input": "$b", "in": {"$multiply": ["$$this", 3]}}},
            ]
        },
        doc={"a": [1, 2], "b": [3, 4]},
        expected=[2, 4, 9, 12],
        msg="Should concatenate two mapped arrays",
    ),
    ExpressionTestCase(
        id="map_with_filter",
        expression={
            "$map": {
                "input": {"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}}},
                "in": {"$multiply": ["$$this", 10]},
            }
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[30, 40, 50],
        msg="Should map over filtered array",
    ),
    ExpressionTestCase(
        id="map_result_into_reduce",
        expression={
            "$reduce": {
                "input": {"$map": {"input": "$arr", "in": {"$multiply": ["$$this", 2]}}},
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2, 3]},
        expected=12,
        msg="$reduce on $map result should sum doubled values",
    ),
    ExpressionTestCase(
        id="map_3_level_nested",
        expression={
            "$map": {
                "input": [[[1]]],
                "as": "a",
                "in": {
                    "$map": {
                        "input": "$$a",
                        "as": "b",
                        "in": {
                            "$map": {
                                "input": "$$b",
                                "in": {"$add": ["$$this", 100]},
                            }
                        },
                    }
                },
            }
        },
        doc={"_placeholder": 1},
        expected=[[[101]]],
        msg="3-level nested $map should work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MAP_COMBINATION_TESTS))
def test_map_combination(collection, test):
    """Test $map composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
