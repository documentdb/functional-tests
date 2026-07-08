"""
Boundary value tests for $range expression.

Tests INT32 boundary values and negative zero handling for start, end, step.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX, INT32_MAX_MINUS_1, INT32_MIN

# Success: INT32 boundary values
INT32_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_max_eq",
        doc={"start": INT32_MAX, "end": INT32_MAX},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="INT32_MAX == INT32_MAX should be empty",
    ),
    ExpressionTestCase(
        id="int32_min_eq",
        doc={"start": INT32_MIN, "end": INT32_MIN},
        expression={"$range": ["$start", "$end"]},
        expected=[],
        msg="INT32_MIN == INT32_MIN should be empty",
    ),
    ExpressionTestCase(
        id="int32_max_minus1",
        doc={"start": INT32_MAX_MINUS_1, "end": INT32_MAX},
        expression={"$range": ["$start", "$end"]},
        expected=[INT32_MAX_MINUS_1],
        msg="INT32_MAX-1 to INT32_MAX should produce single element",
    ),
    ExpressionTestCase(
        id="int32_min_to_plus3",
        doc={"start": INT32_MIN, "end": INT32_MIN + 3},
        expression={"$range": ["$start", "$end"]},
        expected=[INT32_MIN, INT32_MIN + 1, INT32_MIN + 2],
        msg="INT32_MIN to INT32_MIN+3",
    ),
    ExpressionTestCase(
        id="step_int32_max",
        doc={"start": 0, "end": INT32_MAX, "step": INT32_MAX},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[0],
        msg="Step INT32_MAX should produce single element",
    ),
    ExpressionTestCase(
        id="near_int32_max",
        doc={"start": INT32_MAX - 7, "end": INT32_MAX},
        expression={"$range": ["$start", "$end"]},
        expected=[
            INT32_MAX - 7,
            INT32_MAX - 6,
            INT32_MAX - 5,
            INT32_MAX - 4,
            INT32_MAX - 3,
            INT32_MAX - 2,
            INT32_MAX - 1,
        ],
        msg="Near INT32_MAX range",
    ),
    ExpressionTestCase(
        id="cross_int32_boundary",
        doc={"start": INT32_MIN + 1, "end": INT32_MAX, "step": INT32_MAX},
        expression={"$range": ["$start", "$end", "$step"]},
        expected=[INT32_MIN + 1, 0],
        msg="Cross INT32 boundary with large step",
    ),
]

# Aggregate and test
ALL_BOUNDARY_TESTS = INT32_BOUNDARY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_BOUNDARY_TESTS))
def test_range_int32_boundary(collection, test):
    """Test $range with INT32 boundary values for start, end, step."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
