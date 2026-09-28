"""$toString null, boolean, int32, and int64 conversion tests."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
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

# Property [Null and Missing]: $toString returns null for null and missing inputs.
TOSTRING_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="$toString returns null for null input",
        expression={"$toString": None},
        expected=None,
    ),
    ExpressionTestCase(
        "missing",
        msg="$toString returns null for missing field",
        expression={"$toString": MISSING},
        expected=None,
    ),
]

# Property [Boolean Conversion]: true converts to "true", false converts to "false".
TOSTRING_BOOL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_true",
        msg="true converts to 'true'",
        expression={"$toString": True},
        expected="true",
    ),
    ExpressionTestCase(
        "bool_false",
        msg="false converts to 'false'",
        expression={"$toString": False},
        expected="false",
    ),
]

# Property [Int32 Conversion]: int32 values convert to their decimal string representation.
TOSTRING_INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_positive",
        msg="Positive int32 converts to its decimal string",
        expression={"$toString": 42},
        expected="42",
    ),
    ExpressionTestCase(
        "int32_zero",
        msg="int32 zero converts to '0'",
        expression={"$toString": INT32_ZERO},
        expected="0",
    ),
    ExpressionTestCase(
        "int32_negative",
        msg="Negative int32 converts to its decimal string",
        expression={"$toString": -1},
        expected="-1",
    ),
    ExpressionTestCase(
        "int32_min",
        msg="INT32_MIN converts to its decimal string",
        expression={"$toString": INT32_MIN},
        expected=str(INT32_MIN),
    ),
    ExpressionTestCase(
        "int32_min_plus_one",
        msg="INT32_MIN + 1 converts to its decimal string",
        expression={"$toString": INT32_MIN_PLUS_1},
        expected=str(INT32_MIN_PLUS_1),
    ),
    ExpressionTestCase(
        "int32_max",
        msg="INT32_MAX converts to its decimal string",
        expression={"$toString": INT32_MAX},
        expected=str(INT32_MAX),
    ),
    ExpressionTestCase(
        "int32_max_minus_one",
        msg="INT32_MAX - 1 converts to its decimal string",
        expression={"$toString": INT32_MAX_MINUS_1},
        expected=str(INT32_MAX_MINUS_1),
    ),
]

# Property [Int64 Conversion]: int64 values convert to their decimal string representation;
# int32 and int64 produce identical strings for the same numeric value.
TOSTRING_INT64_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_positive",
        msg="Positive int64 converts to its decimal string",
        expression={"$toString": Int64(42)},
        expected="42",
    ),
    ExpressionTestCase(
        "int64_zero",
        msg="int64 zero converts to '0'",
        expression={"$toString": INT64_ZERO},
        expected="0",
    ),
    ExpressionTestCase(
        "int64_negative",
        msg="Negative int64 converts to its decimal string",
        expression={"$toString": Int64(-1)},
        expected="-1",
    ),
    ExpressionTestCase(
        "int64_beyond_int32_max",
        msg="int64 just beyond INT32_MAX converts to '2147483648'",
        expression={"$toString": INT32_OVERFLOW},
        expected="2147483648",
    ),
    ExpressionTestCase(
        "int64_beyond_int32_min",
        msg="int64 just beyond INT32_MIN converts to '-2147483649'",
        expression={"$toString": INT32_UNDERFLOW},
        expected="-2147483649",
    ),
    ExpressionTestCase(
        "int64_min",
        msg="INT64_MIN converts to its decimal string",
        expression={"$toString": INT64_MIN},
        expected=str(INT64_MIN),
    ),
    ExpressionTestCase(
        "int64_min_plus_one",
        msg="INT64_MIN + 1 converts to its decimal string",
        expression={"$toString": INT64_MIN_PLUS_1},
        expected=str(INT64_MIN_PLUS_1),
    ),
    ExpressionTestCase(
        "int64_max",
        msg="INT64_MAX converts to its decimal string",
        expression={"$toString": INT64_MAX},
        expected=str(INT64_MAX),
    ),
    ExpressionTestCase(
        "int64_max_minus_one",
        msg="INT64_MAX - 1 converts to its decimal string",
        expression={"$toString": INT64_MAX_MINUS_1},
        expected=str(INT64_MAX_MINUS_1),
    ),
]

TOSTRING_NUMERIC_TESTS = with_convert_variants(
    TOSTRING_NULL_MISSING_TESTS + TOSTRING_BOOL_TESTS + TOSTRING_INT32_TESTS + TOSTRING_INT64_TESTS,
    "$toString",
    "string",
)


@pytest.mark.parametrize("test", pytest_params(TOSTRING_NUMERIC_TESTS))
def test_toString_numeric(collection, test: ExpressionTestCase):
    """$toString converts null, bool, int32, and int64 inputs to strings."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
