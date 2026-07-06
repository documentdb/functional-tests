"""
Structural error tests for $filter expression.

Tests invalid $filter argument structure: non-object argument, unknown/misspelled fields,
and missing required fields (input, cond).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    FILTER_MISSING_COND_ERROR,
    FILTER_MISSING_INPUT_ERROR,
    FILTER_NON_OBJECT_ARG_ERROR,
    FILTER_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Error: non-object argument
NON_OBJECT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_arg",
        expression={"$filter": None},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="Null arg should error",
    ),
    ExpressionTestCase(
        id="int_arg",
        expression={"$filter": 1},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="Int arg should error",
    ),
    ExpressionTestCase(
        id="string_arg",
        expression={"$filter": "string"},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="String arg should error",
    ),
    ExpressionTestCase(
        id="array_arg",
        expression={"$filter": []},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="Array arg should error",
    ),
    ExpressionTestCase(
        id="bool_arg",
        expression={"$filter": True},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="Bool arg should error",
    ),
]

# Error: unknown fields
UNKNOWN_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="extra_unknown",
        expression={"$filter": {"input": [1], "cond": True, "unknown": 1}},
        error_code=FILTER_UNKNOWN_FIELD_ERROR,
        msg="Extra unknown field should error",
    ),
    ExpressionTestCase(
        id="only_unknown",
        expression={"$filter": {"dummy": 124}},
        error_code=FILTER_UNKNOWN_FIELD_ERROR,
        msg="Only unknown field should error",
    ),
]

# Error: missing required fields
MISSING_REQUIRED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_input",
        expression={"$filter": {"as": "x", "cond": True}},
        error_code=FILTER_MISSING_INPUT_ERROR,
        msg="Missing input should error",
    ),
    ExpressionTestCase(
        id="missing_cond",
        expression={"$filter": {"input": [1, 2, 3]}},
        error_code=FILTER_MISSING_COND_ERROR,
        msg="Missing cond should error",
    ),
    ExpressionTestCase(
        id="empty_object",
        expression={"$filter": {}},
        error_code=FILTER_MISSING_INPUT_ERROR,
        msg="Empty object should error",
    ),
]

# Aggregate and test
ALL_STRUCTURE_TESTS = NON_OBJECT_ARG_TESTS + UNKNOWN_FIELD_TESTS + MISSING_REQUIRED_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_STRUCTURE_TESTS))
def test_filter_structure_error(collection, test):
    """Test $filter argument structure validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
