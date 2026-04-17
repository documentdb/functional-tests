"""
Tests for $eq boundary values and precision.

Covers cross-type boundary values, large number precision at double/long boundary,
and overflow adjacency.
Decimal128 precision and double self-equality are tested in
/core/bson_types/test_bson_types_ordering.py.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_PRECISION_LOSS,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_as_long",
        expression={"$eq": [INT32_MAX, Int64(INT32_MAX)]},
        expected=True,
        msg="INT32_MAX equals Int64(INT32_MAX)",
    ),
    ExpressionTestCase(
        "int32_min_as_long",
        expression={"$eq": [INT32_MIN, Int64(INT32_MIN)]},
        expected=True,
        msg="INT32_MIN equals Int64(INT32_MIN)",
    ),
    ExpressionTestCase(
        "int64_max_as_dec128",
        expression={"$eq": [INT64_MAX, Decimal128(str(INT64_MAX))]},
        expected=True,
        msg="INT64_MAX equals Decimal128(INT64_MAX)",
    ),
    ExpressionTestCase(
        "int64_min_as_dec128",
        expression={"$eq": [INT64_MIN, Decimal128(str(INT64_MIN))]},
        expected=True,
        msg="INT64_MIN equals Decimal128(INT64_MIN)",
    ),
]


LARGE_NUMBER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "beyond_double_precision",
        expression={"$eq": [Int64(DOUBLE_PRECISION_LOSS), float(DOUBLE_PRECISION_LOSS)]},
        expected=False,
        msg="Int64(2^53+1) not equal to double(2^53+1) — beyond double precision",
    ),
    ExpressionTestCase(
        "exactly_representable",
        expression={"$eq": [Int64(DOUBLE_MAX_SAFE_INTEGER), float(DOUBLE_MAX_SAFE_INTEGER)]},
        expected=True,
        msg="Int64(2^53) vs double(2^53) — exactly representable",
    ),
    ExpressionTestCase(
        "dec128_preserves_precision",
        expression={"$eq": [Decimal128(str(DOUBLE_PRECISION_LOSS)), Int64(DOUBLE_PRECISION_LOSS)]},
        expected=True,
        msg="Decimal128(2^53+1) equals Int64(2^53+1)",
    ),
]

OVERFLOW_ADJACENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_overflow_as_long",
        expression={"$eq": [INT32_OVERFLOW, Int64(INT32_OVERFLOW)]},
        expected=True,
        msg="INT32_MAX+1 as int equals Int64(INT32_MAX+1) — promoted to long",
    ),
    ExpressionTestCase(
        "int32_underflow_as_long",
        expression={"$eq": [INT32_UNDERFLOW, Int64(INT32_UNDERFLOW)]},
        expected=True,
        msg="INT32_MIN-1 as int equals Int64(INT32_MIN-1) — promoted to long",
    ),
    ExpressionTestCase(
        "int32_overflow_vs_max",
        expression={"$eq": [INT32_OVERFLOW, INT32_MAX]},
        expected=False,
        msg="INT32_MAX+1 not equal to INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_underflow_vs_min",
        expression={"$eq": [INT32_UNDERFLOW, INT32_MIN]},
        expected=False,
        msg="INT32_MIN-1 not equal to INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_max_minus1",
        expression={"$eq": [INT32_MAX_MINUS_1, INT32_MAX]},
        expected=False,
        msg="INT32_MAX-1 not equal to INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min_plus1",
        expression={"$eq": [INT32_MIN_PLUS_1, INT32_MIN]},
        expected=False,
        msg="INT32_MIN+1 not equal to INT32_MIN",
    ),
    ExpressionTestCase(
        "int64_max_minus1",
        expression={"$eq": [INT64_MAX_MINUS_1, INT64_MAX]},
        expected=False,
        msg="INT64_MAX-1 not equal to INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min_plus1",
        expression={"$eq": [INT64_MIN_PLUS_1, INT64_MIN]},
        expected=False,
        msg="INT64_MIN+1 not equal to INT64_MIN",
    ),
    ExpressionTestCase(
        "int64_max_as_double",
        expression={"$eq": [INT64_MAX, float(INT64_MAX)]},
        expected=False,
        msg="INT64_MAX not equal to float(INT64_MAX) — precision loss",
    ),
    ExpressionTestCase(
        "int64_min_as_double",
        expression={"$eq": [INT64_MIN, float(INT64_MIN)]},
        expected=True,
        msg="INT64_MIN equals float(INT64_MIN) — exact power of 2",
    ),
]


ALL_TESTS = BOUNDARY_TESTS + LARGE_NUMBER_TESTS + OVERFLOW_ADJACENCY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_literal(collection, test):
    """Test $eq across numeric boundary values and cross-type precision edges."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
