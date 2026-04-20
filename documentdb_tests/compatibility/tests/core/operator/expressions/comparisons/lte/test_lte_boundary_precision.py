"""
Tests for $lte boundary values and double precision.

Covers integer boundaries, double precision, and large integer precision edge cases.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

INT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_eq",
        expression={"$lte": [INT32_MAX, INT32_MAX]},
        expected=True,
        msg="INT32_MAX <= INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min_eq",
        expression={"$lte": [INT32_MIN, INT32_MIN]},
        expected=True,
        msg="INT32_MIN <= INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_min_lte_max",
        expression={"$lte": [INT32_MIN, INT32_MAX]},
        expected=True,
        msg="INT32_MIN <= INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_lte_min",
        expression={"$lte": [INT32_MAX, INT32_MIN]},
        expected=False,
        msg="INT32_MAX not <= INT32_MIN",
    ),
    ExpressionTestCase(
        "int64_max_eq",
        expression={"$lte": [INT64_MAX, INT64_MAX]},
        expected=True,
        msg="INT64_MAX <= INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min_eq",
        expression={"$lte": [INT64_MIN, INT64_MIN]},
        expected=True,
        msg="INT64_MIN <= INT64_MIN",
    ),
    ExpressionTestCase(
        "int64_min_lte_max",
        expression={"$lte": [INT64_MIN, INT64_MAX]},
        expected=True,
        msg="INT64_MIN <= INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_max_lte_min",
        expression={"$lte": [INT64_MAX, INT64_MIN]},
        expected=False,
        msg="INT64_MAX not <= INT64_MIN",
    ),
]

DOUBLE_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_max_eq",
        expression={"$lte": [DOUBLE_NEAR_MAX, DOUBLE_NEAR_MAX]},
        expected=True,
        msg="DOUBLE_NEAR_MAX <= DOUBLE_NEAR_MAX",
    ),
    ExpressionTestCase(
        "subnormal_lte_zero",
        expression={"$lte": [DOUBLE_MIN_SUBNORMAL, 0.0]},
        expected=False,
        msg="subnormal not <= 0",
    ),
    ExpressionTestCase(
        "zero_lte_subnormal",
        expression={"$lte": [0.0, DOUBLE_MIN_SUBNORMAL]},
        expected=True,
        msg="0 <= subnormal",
    ),
    ExpressionTestCase(
        "neg_subnormal_lte_zero",
        expression={"$lte": [DOUBLE_MIN_NEGATIVE_SUBNORMAL, 0.0]},
        expected=True,
        msg="negative subnormal <= 0",
    ),
    ExpressionTestCase(
        "near_min_lte_near_max",
        expression={"$lte": [DOUBLE_NEAR_MIN, DOUBLE_NEAR_MAX]},
        expected=True,
        msg="DOUBLE_NEAR_MIN <= DOUBLE_NEAR_MAX",
    ),
]

LARGE_INT_VS_DOUBLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_beyond_double_mantissa",
        expression={"$lte": [Int64(9007199254740993), 9007199254740992.0]},
        expected=False,
        msg="int64 beyond double mantissa: 9007199254740993 not <= 9007199254740992.0",
    ),
    ExpressionTestCase(
        "int64_exactly_representable",
        expression={"$lte": [Int64(9007199254740992), 9007199254740992.0]},
        expected=True,
        msg="exactly representable int64 == double",
    ),
]

ALL_TESTS: list[ExpressionTestCase] = (
    INT_BOUNDARY_TESTS + DOUBLE_PRECISION_TESTS + LARGE_INT_VS_DOUBLE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lte_boundary_precision(collection, test):
    """Test $lte boundary values and precision."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
