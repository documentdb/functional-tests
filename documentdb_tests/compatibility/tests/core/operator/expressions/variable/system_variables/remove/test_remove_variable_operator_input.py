"""
$$REMOVE consumed as an operator argument.

Confirms $$REMOVE, once consumed as an operator argument, propagates as an
ordinary missing value: through nested operator calls, and when materialized
as an array element. Each operator's own contract for a missing/$$REMOVE
input (fallback, null propagation, key omission, or rejection) is covered in
that operator's own test folder.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

# Property [Missing-Value Propagation]: once consumed as an operator argument,
# $$REMOVE propagates exactly like an ordinary missing field — through nested
# operator calls, and as null when materialized inside an array literal.
OPERATOR_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_in_operator_argument_propagates_missing",
        expression={"v": {"$add": [1, {"$multiply": [2, "$$REMOVE"]}]}},
        expected=[{"v": None}],
        msg="Missing from $$REMOVE should propagate through nested operators",
    ),
    ExpressionTestCase(
        id="as_array_expression_element",
        expression={"v": ["$$REMOVE", 1]},
        expected=[{"v": [None, 1]}],
        msg="Array expression should materialize the missing element as null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERATOR_INPUT_TESTS))
def test_remove_variable_as_operator_input(collection, test):
    """$$REMOVE consumed as an operator argument behaves like a missing field."""
    result = execute_project(collection, test.expression)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
