"""Cross-operator combination tests exercising multiple distinct set operators together."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [setDifference Composition]: a $setDifference result feeds the other
# set operators.
SETDIFFERENCE_CROSS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "setDifference_nested_setUnion_operand",
        doc={"a": [1, 2, 3], "b": [3, 4]},
        expression={"$setDifference": [{"$setUnion": ["$a", [5]]}, "$b"]},
        expected=[1, 2, 5],
        msg="$setDifference should accept a $setUnion result as an operand",
    ),
    ExpressionTestCase(
        "setDifference_into_setUnion",
        expression={"$setUnion": [{"$setDifference": [["a", "b", "c"], ["b"]]}, ["d"]]},
        expected=["a", "c", "d"],
        msg="$setDifference result should compose as a $setUnion operand",
    ),
    ExpressionTestCase(
        "setDifference_into_setIntersection",
        expression={"$setIntersection": [{"$setDifference": [["a", "b", "c"], ["c"]]}, ["a", "d"]]},
        expected=["a"],
        msg="$setDifference result should compose as a $setIntersection operand",
    ),
    ExpressionTestCase(
        "setDifference_into_setEquals",
        expression={"$setEquals": [{"$setDifference": [["a", "b"], ["b"]]}, ["a"]]},
        expected=True,
        msg="$setDifference result should compose as a $setEquals operand",
    ),
    ExpressionTestCase(
        "setDifference_into_setIsSubset",
        expression={
            "$setIsSubset": [{"$setDifference": [["a", "b", "c"], ["c"]]}, ["a", "b", "d"]]
        },
        expected=True,
        msg="$setDifference result should compose as a $setIsSubset operand",
    ),
]

SET_OPERATOR_COMBINATION_TESTS: list[ExpressionTestCase] = SETDIFFERENCE_CROSS_TESTS


@pytest.mark.parametrize("test", pytest_params(SET_OPERATOR_COMBINATION_TESTS))
def test_set_operator_combinations(collection, test):
    """Test compositions of two or more distinct set operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg, ignore_order=True)
