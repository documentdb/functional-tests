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
        "null_arg",
        expression={"$filter": None},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="$filter null arg should error",
    ),
    ExpressionTestCase(
        "int_arg",
        expression={"$filter": 1},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="$filter int arg should error",
    ),
    ExpressionTestCase(
        "string_arg",
        expression={"$filter": "string"},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="$filter string arg should error",
    ),
    ExpressionTestCase(
        "array_arg",
        expression={"$filter": []},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="$filter array arg should error",
    ),
    ExpressionTestCase(
        "bool_arg",
        expression={"$filter": True},
        error_code=FILTER_NON_OBJECT_ARG_ERROR,
        msg="$filter bool arg should error",
    ),
]

# Error: unknown fields
UNKNOWN_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "extra_unknown",
        expression={"$filter": {"input": [1], "cond": True, "unknown": 1}},
        error_code=FILTER_UNKNOWN_FIELD_ERROR,
        msg="$filter extra unknown field should error",
    ),
    ExpressionTestCase(
        "only_unknown",
        expression={"$filter": {"dummy": 124}},
        error_code=FILTER_UNKNOWN_FIELD_ERROR,
        msg="$filter only unknown field should error",
    ),
]

# Error: missing required fields
MISSING_REQUIRED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_input",
        expression={"$filter": {"as": "x", "cond": True}},
        error_code=FILTER_MISSING_INPUT_ERROR,
        msg="$filter missing input should error",
    ),
    ExpressionTestCase(
        "missing_cond",
        expression={"$filter": {"input": [1, 2, 3]}},
        error_code=FILTER_MISSING_COND_ERROR,
        msg="$filter missing cond should error",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$filter": {}},
        error_code=FILTER_MISSING_INPUT_ERROR,
        msg="$filter empty object should error",
    ),
]

# Aggregate and test
ALL_STRUCTURE_TESTS = NON_OBJECT_ARG_TESTS + UNKNOWN_FIELD_TESTS + MISSING_REQUIRED_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_STRUCTURE_TESTS))
def test_filter_structure_error(collection, test):
    """Test $filter argument structure validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
