"""
Boundary value tests for $range expression.

Tests INT32 boundary values and negative zero handling for start, end, step.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.range.utils.range_common import (  # noqa: E501
    RangeTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX, INT32_MAX_MINUS_1, INT32_MIN

# ---------------------------------------------------------------------------
# Success: INT32 boundary values
# ---------------------------------------------------------------------------
INT32_BOUNDARY_TESTS: list[RangeTest] = [
    RangeTest(
        id="int32_max_eq",
        start=INT32_MAX,
        end=INT32_MAX,
        expected=[],
        msg="INT32_MAX == INT32_MAX should be empty",
    ),
    RangeTest(
        id="int32_min_eq",
        start=INT32_MIN,
        end=INT32_MIN,
        expected=[],
        msg="INT32_MIN == INT32_MIN should be empty",
    ),
    RangeTest(
        id="int32_max_minus1",
        start=INT32_MAX_MINUS_1,
        end=INT32_MAX,
        expected=[INT32_MAX_MINUS_1],
        msg="INT32_MAX-1 to INT32_MAX should produce single element",
    ),
    RangeTest(
        id="int32_min_to_plus3",
        start=INT32_MIN,
        end=INT32_MIN + 3,
        expected=[INT32_MIN, INT32_MIN + 1, INT32_MIN + 2],
        msg="INT32_MIN to INT32_MIN+3",
    ),
    RangeTest(
        id="step_int32_max",
        start=0,
        end=INT32_MAX,
        step=INT32_MAX,
        expected=[0],
        msg="Step INT32_MAX should produce single element",
    ),
    RangeTest(
        id="near_int32_max",
        start=INT32_MAX - 7,
        end=INT32_MAX,
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
    RangeTest(
        id="cross_int32_boundary",
        start=INT32_MIN + 1,
        end=INT32_MAX,
        step=INT32_MAX,
        expected=[INT32_MIN + 1, 0],
        msg="Cross INT32 boundary with large step",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_BOUNDARY_TESTS = INT32_BOUNDARY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_BOUNDARY_TESTS))
def test_range_boundary_insert(collection, test):
    """Test $range boundary values with inserted documents."""
    doc = {"start": test.start, "end": test.end}
    args = ["$start", "$end"]
    if test.step is not None:
        args.append("$step")
        doc["step"] = test.step
    result = execute_expression_with_insert(collection, {"$range": args}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_BOUNDARY_TESTS))
def test_range_boundary_literal(collection, test):
    """Test $range boundary values with literal values."""
    args = [test.start, test.end]
    if test.step is not None:
        args.append(test.step)
    result = execute_expression(collection, {"$range": args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
