"""
Boundary tests for $trunc expression.

Covers INT32/INT64 boundary values, double subnormals (including
negative subnormal), near-min/near-max doubles, max-safe-integer,
and Decimal128 max/min/exponent/trailing-zero boundaries.
"""

import pytest
from bson import (
    Decimal128,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

TRUNC_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        expression={"$trunc": INT32_MAX},
        expected=INT32_MAX,
        msg="Should preserve INT32_MAX unchanged",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        expression={"$trunc": INT32_MAX_MINUS_1},
        expected=INT32_MAX_MINUS_1,
        msg="Should preserve INT32_MAX - 1 unchanged",
    ),
    ExpressionTestCase(
        "int32_min",
        expression={"$trunc": INT32_MIN},
        expected=INT32_MIN,
        msg="Should preserve INT32_MIN unchanged",
    ),
    ExpressionTestCase(
        "int32_min_plus_1",
        expression={"$trunc": INT32_MIN_PLUS_1},
        expected=INT32_MIN_PLUS_1,
        msg="Should preserve INT32_MIN + 1 unchanged",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$trunc": INT64_MAX},
        expected=INT64_MAX,
        msg="Should preserve INT64_MAX unchanged",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        expression={"$trunc": INT64_MAX_MINUS_1},
        expected=INT64_MAX_MINUS_1,
        msg="Should preserve INT64_MAX - 1 unchanged",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$trunc": INT64_MIN},
        expected=INT64_MIN,
        msg="Should preserve INT64_MIN unchanged",
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        expression={"$trunc": INT64_MIN_PLUS_1},
        expected=INT64_MIN_PLUS_1,
        msg="Should preserve INT64_MIN + 1 unchanged",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$trunc": DOUBLE_MIN_SUBNORMAL},
        expected=0.0,
        msg="Should truncate the smallest positive subnormal double to 0.0",
    ),
    ExpressionTestCase(
        "double_min_negative_subnormal",
        expression={"$trunc": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected=-0.0,
        msg="Should truncate the smallest negative subnormal double to -0.0",
    ),
    ExpressionTestCase(
        "double_near_min",
        expression={"$trunc": DOUBLE_NEAR_MIN},
        expected=0.0,
        msg="Should truncate a double near the minimum positive value to 0.0",
    ),
    ExpressionTestCase(
        "double_near_max",
        expression={"$trunc": DOUBLE_NEAR_MAX},
        expected=DOUBLE_NEAR_MAX,
        msg="Should preserve a double near the maximum value unchanged",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        expression={"$trunc": float(DOUBLE_MAX_SAFE_INTEGER)},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="Should preserve the double max safe integer unchanged",
    ),
    ExpressionTestCase(
        "decimal128_max",
        expression={"$trunc": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="Should preserve Decimal128 max value unchanged",
    ),
    ExpressionTestCase(
        "decimal128_min",
        expression={"$trunc": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="Should preserve Decimal128 min value unchanged",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        expression={"$trunc": DECIMAL128_SMALL_EXPONENT},
        expected=Decimal128("0"),
        msg="Should truncate a Decimal128 with a very small exponent to 0",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        expression={"$trunc": DECIMAL128_LARGE_EXPONENT},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="Should preserve a Decimal128 with a very large exponent unchanged",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        expression={"$trunc": DECIMAL128_TRAILING_ZERO},
        expected=Decimal128("1"),
        msg="Should truncate a Decimal128 with a trailing-zero fraction to its integer part",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        expression={"$trunc": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=Decimal128("1"),
        msg="Should truncate a Decimal128 with many trailing zeros to its integer part",
    ),
]

TRUNC_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        expression={"$trunc": "$value"},
        doc={"value": INT32_MAX},
        expected=INT32_MAX,
        msg="Should preserve INT32_MAX unchanged",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        expression={"$trunc": "$value"},
        doc={"value": INT32_MAX_MINUS_1},
        expected=INT32_MAX_MINUS_1,
        msg="Should preserve INT32_MAX - 1 unchanged",
    ),
    ExpressionTestCase(
        "int32_min",
        expression={"$trunc": "$value"},
        doc={"value": INT32_MIN},
        expected=INT32_MIN,
        msg="Should preserve INT32_MIN unchanged",
    ),
    ExpressionTestCase(
        "int32_min_plus_1",
        expression={"$trunc": "$value"},
        doc={"value": INT32_MIN_PLUS_1},
        expected=INT32_MIN_PLUS_1,
        msg="Should preserve INT32_MIN + 1 unchanged",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$trunc": "$value"},
        doc={"value": INT64_MAX},
        expected=INT64_MAX,
        msg="Should preserve INT64_MAX unchanged",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        expression={"$trunc": "$value"},
        doc={"value": INT64_MAX_MINUS_1},
        expected=INT64_MAX_MINUS_1,
        msg="Should preserve INT64_MAX - 1 unchanged",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$trunc": "$value"},
        doc={"value": INT64_MIN},
        expected=INT64_MIN,
        msg="Should preserve INT64_MIN unchanged",
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        expression={"$trunc": "$value"},
        doc={"value": INT64_MIN_PLUS_1},
        expected=INT64_MIN_PLUS_1,
        msg="Should preserve INT64_MIN + 1 unchanged",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expected=0.0,
        msg="Should truncate the smallest positive subnormal double to 0.0",
    ),
    ExpressionTestCase(
        "double_min_negative_subnormal",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected=-0.0,
        msg="Should truncate the smallest negative subnormal double to -0.0",
    ),
    ExpressionTestCase(
        "double_near_min",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_NEAR_MIN},
        expected=0.0,
        msg="Should truncate a double near the minimum positive value to 0.0",
    ),
    ExpressionTestCase(
        "double_near_max",
        expression={"$trunc": "$value"},
        doc={"value": DOUBLE_NEAR_MAX},
        expected=DOUBLE_NEAR_MAX,
        msg="Should preserve a double near the maximum value unchanged",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        expression={"$trunc": "$value"},
        doc={"value": float(DOUBLE_MAX_SAFE_INTEGER)},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="Should preserve the double max safe integer unchanged",
    ),
    ExpressionTestCase(
        "decimal128_max",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="Should preserve Decimal128 max value unchanged",
    ),
    ExpressionTestCase(
        "decimal128_min",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="Should preserve Decimal128 min value unchanged",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expected=Decimal128("0"),
        msg="Should truncate a Decimal128 with a very small exponent to 0",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_LARGE_EXPONENT},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="Should preserve a Decimal128 with a very large exponent unchanged",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_TRAILING_ZERO},
        expected=Decimal128("1"),
        msg="Should truncate a Decimal128 with a trailing-zero fraction to its integer part",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        expression={"$trunc": "$value"},
        doc={"value": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=Decimal128("1"),
        msg="Should truncate a Decimal128 with many trailing zeros to its integer part",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TRUNC_LITERAL_TESTS))
def test_trunc_literal(collection, test):
    """Test $trunc with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TRUNC_INSERT_TESTS))
def test_trunc_insert(collection, test):
    """Test $trunc with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
