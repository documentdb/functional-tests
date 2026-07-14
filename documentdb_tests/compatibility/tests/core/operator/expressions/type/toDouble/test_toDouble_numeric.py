"""$toDouble numeric type tests: null/missing, boolean, int32, int64, double identity, and NaN."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_ZERO,
    MISSING,
)

# Property [Null and Missing]: $toDouble returns null for null and missing inputs.
TODOUBLE_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null", msg="Should return null for null", expression={"$toDouble": None}, expected=None
    ),
    ExpressionTestCase(
        "missing",
        msg="Should return null for missing",
        expression={"$toDouble": MISSING},
        expected=None,
    ),
]

# Property [Boolean]: $toDouble converts true to 1.0 and false to +0.0.
TODOUBLE_BOOL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_true", msg="True converts to 1.0", expression={"$toDouble": True}, expected=1.0
    ),
    ExpressionTestCase(
        "bool_false",
        msg="False converts to positive 0.0",
        expression={"$toDouble": False},
        expected=DOUBLE_ZERO,
    ),
]

# Property [Int32]: $toDouble converts int32 values to their exact double equivalents.
TODOUBLE_INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        msg="int32 zero converts to 0.0",
        expression={"$toDouble": INT32_ZERO},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "int32_one",
        msg="int32 1 converts exactly to 1.0",
        expression={"$toDouble": 1},
        expected=1.0,
    ),
    ExpressionTestCase(
        "int32_neg_one",
        msg="int32 -1 converts exactly to -1.0",
        expression={"$toDouble": -1},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "int32_max",
        msg="int32 max converts exactly",
        expression={"$toDouble": INT32_MAX},
        expected=2147483647.0,
    ),
    ExpressionTestCase(
        "int32_min",
        msg="int32 min converts exactly",
        expression={"$toDouble": INT32_MIN},
        expected=-2147483648.0,
    ),
]

# Property [Int64]: $toDouble converts int64 values, with precision loss above 2^53.
TODOUBLE_INT64_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_zero",
        msg="int64 zero converts to 0.0",
        expression={"$toDouble": INT64_ZERO},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "int64_one", msg="int64 1 converts to 1.0", expression={"$toDouble": Int64(1)}, expected=1.0
    ),
    ExpressionTestCase(
        "int64_safe_max",
        msg="int64 at 2^53 (max safe integer) converts exactly",
        expression={"$toDouble": Int64(DOUBLE_MAX_SAFE_INTEGER)},
        expected=9007199254740992.0,
    ),
    ExpressionTestCase(
        "int64_above_safe",
        msg="int64 above 2^53 loses the last bit of precision",
        expression={"$toDouble": Int64(DOUBLE_PRECISION_LOSS)},
        expected=9007199254740992.0,
    ),
    ExpressionTestCase(
        "int64_neg_one",
        msg="int64 -1 converts to -1.0",
        expression={"$toDouble": Int64(-1)},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "int64_max",
        msg="int64 max converts with precision loss",
        expression={"$toDouble": INT64_MAX},
        expected=DOUBLE_FROM_INT64_MAX,
    ),
    ExpressionTestCase(
        "int64_max_minus_one",
        msg="int64 max-1 rounds to the same double as int64 max",
        expression={"$toDouble": INT64_MAX_MINUS_1},
        expected=DOUBLE_FROM_INT64_MAX,
    ),
    ExpressionTestCase(
        "int64_min",
        msg="int64 min converts to -2^63 representation",
        expression={"$toDouble": INT64_MIN},
        expected=-DOUBLE_FROM_INT64_MAX,
    ),
]

# Property [Double Identity]: $toDouble is the identity function for double inputs.
TODOUBLE_DOUBLE_IDENTITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_zero",
        msg="0.0 passes through unchanged",
        expression={"$toDouble": DOUBLE_ZERO},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "double_neg_zero",
        msg="-0.0 passes through preserving sign",
        expression={"$toDouble": DOUBLE_NEGATIVE_ZERO},
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "double_inf",
        msg="+Inf passes through unchanged",
        expression={"$toDouble": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "double_neg_inf",
        msg="-Inf passes through unchanged",
        expression={"$toDouble": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "double_one",
        msg="1.0 passes through unchanged",
        expression={"$toDouble": 1.0},
        expected=1.0,
    ),
    ExpressionTestCase(
        "double_pi",
        msg="pi passes through unchanged",
        expression={"$toDouble": 3.141592653589793},
        expected=3.141592653589793,
    ),
    ExpressionTestCase(
        "double_large",
        msg="Large double passes through unchanged",
        expression={"$toDouble": DOUBLE_MAX},
        expected=DOUBLE_MAX,
    ),
    ExpressionTestCase(
        "double_subnormal",
        msg="Minimum positive subnormal double passes through unchanged",
        expression={"$toDouble": DOUBLE_MIN_SUBNORMAL},
        expected=DOUBLE_MIN_SUBNORMAL,
    ),
    ExpressionTestCase(
        "double_neg_subnormal",
        msg="Minimum negative subnormal double passes through unchanged",
        expression={"$toDouble": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    ),
]

# Property [NaN]: $toDouble preserves NaN inputs as double NaN.
TODOUBLE_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_nan",
        msg="double NaN passes through as NaN",
        expression={"$toDouble": FLOAT_NAN},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
    ),
    ExpressionTestCase(
        "dec128_nan",
        msg="Decimal128 nan converts to double NaN",
        expression={"$toDouble": DECIMAL128_NAN},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
    ),
    ExpressionTestCase(
        "str_nan",
        msg="'NaN' string converts to double NaN",
        expression={"$toDouble": "NaN"},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
    ),
    ExpressionTestCase(
        "str_nan_lower",
        msg="'nan' string converts to double NaN",
        expression={"$toDouble": "nan"},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
    ),
]

TODOUBLE_NUMERIC_TESTS = (
    TODOUBLE_NULL_MISSING_TESTS
    + TODOUBLE_BOOL_TESTS
    + TODOUBLE_INT32_TESTS
    + TODOUBLE_INT64_TESTS
    + TODOUBLE_DOUBLE_IDENTITY_TESTS
    + TODOUBLE_NAN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_NUMERIC_TESTS))
def test_toDouble_numeric(collection, test: ExpressionTestCase):
    """$toDouble converts null, bool, int32, int64, double, and NaN inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
