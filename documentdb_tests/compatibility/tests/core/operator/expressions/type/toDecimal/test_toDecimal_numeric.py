"""$toDecimal numeric type tests: null/missing, boolean, int32, and int64."""

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
    DECIMAL128_INT64_MAX,
    DECIMAL128_ZERO,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT32_ZERO,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
    INT64_ZERO,
    MISSING,
)

# Property [Null and Missing]: $toDecimal returns null for null and missing inputs.
TODECIMAL_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="Should return null for null",
        expression={"$toDecimal": None},
        expected=None,
    ),
    ExpressionTestCase(
        "missing",
        msg="Should return null for missing",
        expression={"$toDecimal": MISSING},
        expected=None,
    ),
]

# Property [Boolean]: $toDecimal converts true to Decimal128("1") and false to Decimal128("0").
TODECIMAL_BOOL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_true",
        msg="True converts to Decimal128('1')",
        expression={"$toDecimal": True},
        expected=Decimal128("1"),
    ),
    ExpressionTestCase(
        "bool_false",
        msg="False converts to Decimal128('0')",
        expression={"$toDecimal": False},
        expected=DECIMAL128_ZERO,
    ),
]

# Property [Int32]: $toDecimal converts int32 values to exact Decimal128 with no trailing zeros.
TODECIMAL_INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        msg="int32 zero converts to Decimal128('0')",
        expression={"$toDecimal": INT32_ZERO},
        expected=DECIMAL128_ZERO,
    ),
    ExpressionTestCase(
        "int32_one",
        msg="int32 1 converts to Decimal128('1')",
        expression={"$toDecimal": 1},
        expected=Decimal128("1"),
    ),
    ExpressionTestCase(
        "int32_neg_one",
        msg="int32 -1 converts to Decimal128('-1')",
        expression={"$toDecimal": -1},
        expected=Decimal128("-1"),
    ),
    ExpressionTestCase(
        "int32_max",
        msg="int32 max converts exactly",
        expression={"$toDecimal": INT32_MAX},
        expected=Decimal128(str(INT32_MAX)),
    ),
    ExpressionTestCase(
        "int32_min",
        msg="int32 min converts exactly",
        expression={"$toDecimal": INT32_MIN},
        expected=Decimal128(str(INT32_MIN)),
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        msg="int32 max-1 converts exactly",
        expression={"$toDecimal": INT32_MAX_MINUS_1},
        expected=Decimal128(str(INT32_MAX_MINUS_1)),
    ),
    ExpressionTestCase(
        "int32_min_plus_1",
        msg="int32 min+1 converts exactly",
        expression={"$toDecimal": INT32_MIN_PLUS_1},
        expected=Decimal128(str(INT32_MIN_PLUS_1)),
    ),
]

# Property [Int64]: $toDecimal converts int64 values to exact Decimal128 with no trailing zeros.
TODECIMAL_INT64_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_zero",
        msg="int64 zero converts to Decimal128('0')",
        expression={"$toDecimal": INT64_ZERO},
        expected=DECIMAL128_ZERO,
    ),
    ExpressionTestCase(
        "int64_one",
        msg="int64 1 converts to Decimal128('1')",
        expression={"$toDecimal": Int64(1)},
        expected=Decimal128("1"),
    ),
    ExpressionTestCase(
        "int64_neg_one",
        msg="int64 -1 converts to Decimal128('-1')",
        expression={"$toDecimal": Int64(-1)},
        expected=Decimal128("-1"),
    ),
    ExpressionTestCase(
        "int64_beyond_int32_pos",
        msg="int64 just beyond int32 max converts exactly",
        expression={"$toDecimal": INT32_OVERFLOW},
        expected=Decimal128(str(INT32_OVERFLOW)),
    ),
    ExpressionTestCase(
        "int64_beyond_int32_neg",
        msg="int64 just beyond int32 min converts exactly",
        expression={"$toDecimal": INT32_UNDERFLOW},
        expected=Decimal128(str(INT32_UNDERFLOW)),
    ),
    ExpressionTestCase(
        "int64_max",
        msg="int64 max converts exactly to Decimal128",
        expression={"$toDecimal": INT64_MAX},
        expected=DECIMAL128_INT64_MAX,
    ),
    ExpressionTestCase(
        "int64_min",
        msg="int64 min converts exactly to Decimal128",
        expression={"$toDecimal": INT64_MIN},
        expected=Decimal128(str(INT64_MIN)),
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        msg="int64 max-1 converts exactly",
        expression={"$toDecimal": INT64_MAX_MINUS_1},
        expected=Decimal128(str(INT64_MAX_MINUS_1)),
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        msg="int64 min+1 converts exactly",
        expression={"$toDecimal": INT64_MIN_PLUS_1},
        expected=Decimal128(str(INT64_MIN_PLUS_1)),
    ),
]

TODECIMAL_NUMERIC_TESTS = (
    TODECIMAL_NULL_MISSING_TESTS
    + TODECIMAL_BOOL_TESTS
    + TODECIMAL_INT32_TESTS
    + TODECIMAL_INT64_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_NUMERIC_TESTS))
def test_toDecimal_numeric(collection, test: ExpressionTestCase):
    """$toDecimal converts null, missing, bool, int32, and int64 inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
