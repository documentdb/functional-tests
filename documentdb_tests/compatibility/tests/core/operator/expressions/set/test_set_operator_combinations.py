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

# Property [setIntersection Composition]: $setIntersection composes with the other
# set operators.
SETINTERSECTION_CROSS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "setIntersection_nested_setUnion_operand",
        expression={"$setIntersection": [{"$setUnion": [[1, 2], [3]]}, [2, 3, 4]]},
        expected=[2, 3],
        msg="$setIntersection should accept a $setUnion result as an operand",
    ),
    ExpressionTestCase(
        "setIntersection_with_setDifference",
        expression={"$setIntersection": [{"$setDifference": [[1, 2, 3], [1]]}, [2, 4]]},
        expected=[2],
        msg="$setIntersection should accept a $setDifference result as an operand",
    ),
]

# Property [setEquals Composition]: $setEquals verifies the results of the other
# set operators.
SETEQUALS_CROSS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "setEquals_setUnion_operand",
        expression={"$setEquals": [{"$setUnion": [[1, 2], [3]]}, [1, 2, 3]]},
        expected=True,
        msg="$setEquals should accept a $setUnion result as an operand",
    ),
    ExpressionTestCase(
        "setEquals_setIntersection_operand",
        expression={"$setEquals": [{"$setIntersection": [[1, 2, 3], [2, 3, 4]]}, [2, 3]]},
        expected=True,
        msg="$setEquals should accept a $setIntersection result as an operand",
    ),
    ExpressionTestCase(
        "setEquals_setDifference_operand",
        expression={"$setEquals": [{"$setDifference": [[1, 2, 3], [2]]}, [1, 3]]},
        expected=True,
        msg="$setEquals should accept a $setDifference result as an operand",
    ),
    ExpressionTestCase(
        "setEquals_chained_setUnion",
        expression={"$setEquals": [{"$setUnion": [[1, 2], [3]]}, {"$setUnion": [[3], [1, 2]]}]},
        expected=True,
        msg="$setEquals should compare two $setUnion results as commutative operands",
    ),
]

SET_OPERATOR_COMBINATION_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_CROSS_TESTS + SETINTERSECTION_CROSS_TESTS + SETEQUALS_CROSS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SET_OPERATOR_COMBINATION_TESTS))
def test_set_operator_combinations(collection, test):
    """Test compositions of two or more distinct set operators."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg, ignore_order=True)
