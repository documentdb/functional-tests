"""
Combination tests for $isArray composed with other operators.
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

ISARRAY_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="isarray_guard_array",
        expression={"$cond": {"if": {"$isArray": "$arr"}, "then": {"$size": "$arr"}, "else": "NA"}},
        doc={"arr": [1, 2]},
        expected=2,
        msg="$isArray guard should allow $size on array",
    ),
    ExpressionTestCase(
        id="isarray_on_concatArrays",
        expression={"$isArray": {"$concatArrays": ["$a", "$b"]}},
        doc={"a": [1], "b": [2]},
        expected=True,
        msg="$isArray on $concatArrays result should return true",
    ),
    ExpressionTestCase(
        id="isarray_on_objectToArray",
        expression={"$isArray": {"$objectToArray": "$obj"}},
        doc={"obj": {"a": 1}},
        expected=True,
        msg="$isArray on $objectToArray result should return true",
    ),
    ExpressionTestCase(
        id="isarray_on_non_array_expression",
        expression={"$isArray": {"$add": ["$x", "$y"]}},
        doc={"x": 1, "y": 2},
        expected=False,
        msg="$isArray on $add result should return false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ISARRAY_COMBINATION_TESTS))
def test_isArray_combination(collection, test):
    """Test $isArray composed with other operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
