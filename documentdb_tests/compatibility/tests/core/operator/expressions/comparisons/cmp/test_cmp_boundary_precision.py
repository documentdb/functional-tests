"""
Tests for $cmp boundary values and precision.

Covers cross-type boundary values, large number precision at double/long boundary,
and overflow adjacency.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
)

BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_self",
        expression={"$cmp": [INT32_MAX, INT32_MAX]},
        expected=0,
        msg="INT32_MAX equals itself",
    ),
    ExpressionTestCase(
        "int32_max_vs_overflow",
        expression={"$cmp": [INT32_MAX, INT32_OVERFLOW]},
        expected=-1,
        msg="INT32_MAX < INT32_OVERFLOW (promoted to long)",
    ),
    ExpressionTestCase(
        "int32_min_vs_underflow",
        expression={"$cmp": [INT32_MIN, INT32_UNDERFLOW]},
        expected=1,
        msg="INT32_MIN > INT32_UNDERFLOW (promoted to long)",
    ),
    ExpressionTestCase(
        "int32_max_vs_int64_max",
        expression={"$cmp": [INT32_MAX, INT64_MAX]},
        expected=-1,
        msg="INT32_MAX < INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min_vs_int32_min",
        expression={"$cmp": [INT64_MIN, INT32_MIN]},
        expected=-1,
        msg="INT64_MIN < INT32_MIN",
    ),
    ExpressionTestCase(
        "int64_max_self",
        expression={"$cmp": [INT64_MAX, INT64_MAX]},
        expected=0,
        msg="INT64_MAX equals itself",
    ),
]


LARGE_NUMBER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "beyond_double_precision",
        expression={"$cmp": [Int64(DOUBLE_PRECISION_LOSS), float(DOUBLE_PRECISION_LOSS)]},
        expected=1,
        msg="Int64(2^53+1) > double(2^53+1) — beyond double precision",
    ),
    ExpressionTestCase(
        "exactly_representable",
        expression={"$cmp": [Int64(DOUBLE_MAX_SAFE_INTEGER), float(DOUBLE_MAX_SAFE_INTEGER)]},
        expected=0,
        msg="Int64(2^53) vs double(2^53) — exactly representable",
    ),
    ExpressionTestCase(
        "dec128_preserves_precision",
        expression={"$cmp": [Decimal128(str(DOUBLE_PRECISION_LOSS)), Int64(DOUBLE_PRECISION_LOSS)]},
        expected=0,
        msg="Decimal128(2^53+1) equals Int64(2^53+1)",
    ),
    ExpressionTestCase(
        "neg_zero_vs_pos_zero",
        expression={"$cmp": [DOUBLE_NEGATIVE_ZERO, 0]},
        expected=0,
        msg="-0.0 equals 0 (negative zero is equal to positive zero)",
    ),
]


ALL_TESTS = BOUNDARY_TESTS + LARGE_NUMBER_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_literal(collection, test):
    """Test $cmp across numeric boundary values and cross-type precision edges."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
