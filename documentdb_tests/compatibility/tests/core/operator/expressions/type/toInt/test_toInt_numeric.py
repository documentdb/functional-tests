"""$toInt numeric type tests: null/missing, boolean, int32 identity, and int64 conversion."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
    MISSING,
)

# Property [Null and Missing]: $toInt returns null for null and missing inputs.
TOINT_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null", msg="Should return null for null", expression={"$toInt": None}, expected=None
    ),
    ExpressionTestCase(
        "missing",
        msg="Should return null for missing",
        expression={"$toInt": MISSING},
        expected=None,
    ),
]

# Property [Boolean]: $toInt converts true to 1 and false to 0.
TOINT_BOOL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_true", msg="True converts to 1", expression={"$toInt": True}, expected=1
    ),
    ExpressionTestCase(
        "bool_false", msg="False converts to 0", expression={"$toInt": False}, expected=INT32_ZERO
    ),
]

# Property [Int32 Identity]: $toInt is the identity function for int32 inputs.
TOINT_INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        msg="int32 zero passes through unchanged",
        expression={"$toInt": INT32_ZERO},
        expected=INT32_ZERO,
    ),
    ExpressionTestCase(
        "int32_one",
        msg="int32 1 passes through unchanged",
        expression={"$toInt": 1},
        expected=1,
    ),
    ExpressionTestCase(
        "int32_neg_one",
        msg="int32 -1 passes through unchanged",
        expression={"$toInt": -1},
        expected=-1,
    ),
    ExpressionTestCase(
        "int32_max",
        msg="int32 max passes through unchanged",
        expression={"$toInt": INT32_MAX},
        expected=INT32_MAX,
    ),
    ExpressionTestCase(
        "int32_min",
        msg="int32 min passes through unchanged",
        expression={"$toInt": INT32_MIN},
        expected=INT32_MIN,
    ),
]

# Property [Int64]: $toInt converts int64 values within int32 range; rejects out-of-range values.
TOINT_INT64_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_zero",
        msg="int64 zero converts to int32 0",
        expression={"$toInt": INT64_ZERO},
        expected=INT32_ZERO,
    ),
    ExpressionTestCase(
        "int64_one",
        msg="int64 1 converts to int32 1",
        expression={"$toInt": Int64(1)},
        expected=1,
    ),
    ExpressionTestCase(
        "int64_neg_one",
        msg="int64 -1 converts to int32 -1",
        expression={"$toInt": Int64(-1)},
        expected=-1,
    ),
    ExpressionTestCase(
        "int64_int32_max",
        msg="int64 equal to int32 max converts exactly",
        expression={"$toInt": Int64(INT32_MAX)},
        expected=INT32_MAX,
    ),
    ExpressionTestCase(
        "int64_int32_min",
        msg="int64 equal to int32 min converts exactly",
        expression={"$toInt": Int64(INT32_MIN)},
        expected=INT32_MIN,
    ),
    ExpressionTestCase(
        "int64_overflow",
        msg="int64 one above int32 max is a conversion failure",
        expression={"$toInt": Int64(INT32_MAX + 1)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "int64_underflow",
        msg="int64 one below int32 min is a conversion failure",
        expression={"$toInt": Int64(INT32_MIN - 1)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "int64_max",
        msg="int64 max is a conversion failure",
        expression={"$toInt": INT64_MAX},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "int64_min",
        msg="int64 min is a conversion failure",
        expression={"$toInt": INT64_MIN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOINT_NUMERIC_TESTS = (
    TOINT_NULL_MISSING_TESTS + TOINT_BOOL_TESTS + TOINT_INT32_TESTS + TOINT_INT64_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TOINT_NUMERIC_TESTS))
def test_toInt_numeric(collection, test: ExpressionTestCase):
    """$toInt converts null, bool, int32, and int64 inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
