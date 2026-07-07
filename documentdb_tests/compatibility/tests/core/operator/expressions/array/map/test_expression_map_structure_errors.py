"""
Structural error tests for $map expression.

Tests invalid $map argument structure: non-object argument, unknown/misspelled fields,
missing required fields (input, in), and runtime errors in the 'in' expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_NON_OBJECT_ARG_ERROR,
    MAP_MISSING_IN_ERROR,
    MAP_MISSING_INPUT_ERROR,
    MAP_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Error: non-object argument
# ---------------------------------------------------------------------------
NON_OBJECT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_arg",
        expression={"$map": None},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="Null arg should error",
    ),
    ExpressionTestCase(
        id="int_arg",
        expression={"$map": 1},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="Int arg should error",
    ),
    ExpressionTestCase(
        id="string_arg",
        expression={"$map": "string"},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="String arg should error",
    ),
    ExpressionTestCase(
        id="array_arg",
        expression={"$map": [1, 2]},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="Array arg should error",
    ),
    ExpressionTestCase(
        id="bool_arg",
        expression={"$map": True},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="Bool arg should error",
    ),
]

# ---------------------------------------------------------------------------
# Error: unknown fields
# ---------------------------------------------------------------------------
UNKNOWN_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="extra_unknown",
        expression={"$map": {"input": [1], "in": "$$this", "unknown": 1}},
        error_code=MAP_UNKNOWN_FIELD_ERROR,
        msg="Extra unknown field should error",
    ),
    ExpressionTestCase(
        id="misspelled_inputs",
        expression={"$map": {"inputs": [1], "in": "$$this"}},
        error_code=MAP_UNKNOWN_FIELD_ERROR,
        msg="Misspelled 'inputs' should error",
    ),
]

# ---------------------------------------------------------------------------
# Error: missing required fields
# ---------------------------------------------------------------------------
MISSING_REQUIRED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_input",
        expression={"$map": {"in": "$$this"}},
        error_code=MAP_MISSING_INPUT_ERROR,
        msg="Missing input should error",
    ),
    ExpressionTestCase(
        id="missing_in",
        expression={"$map": {"input": [1, 2, 3]}},
        error_code=MAP_MISSING_IN_ERROR,
        msg="Missing in should error",
    ),
    ExpressionTestCase(
        id="missing_in_with_as",
        expression={"$map": {"input": [1, 2, 3], "as": "x"}},
        error_code=MAP_MISSING_IN_ERROR,
        msg="Missing in with as should error",
    ),
    ExpressionTestCase(
        id="empty_object",
        expression={"$map": {}},
        error_code=MAP_MISSING_INPUT_ERROR,
        msg="Empty object should error",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_STRUCTURE_TESTS = NON_OBJECT_ARG_TESTS + UNKNOWN_FIELD_TESTS + MISSING_REQUIRED_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_STRUCTURE_TESTS))
def test_map_structure_error(collection, test):
    """Test $map argument structure validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
