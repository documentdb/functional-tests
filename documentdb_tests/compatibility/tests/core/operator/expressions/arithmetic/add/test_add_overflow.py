"""Tests for $add integer and double overflow and underflow promotion."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_FROM_INT64_MAX,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
)

# Property [Int32 Overflow]: when an int32 result exceeds the int32 range, $add promotes to
# int64.
ADD_INT32_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_overflow",
        doc={"a": INT32_MAX, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=Int64(INT32_OVERFLOW),
        msg="$add should promote to int64 when the int32 result overflows INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_underflow",
        doc={"a": INT32_MIN, "b": -1},
        expression={"$add": ["$a", "$b"]},
        expected=Int64(INT32_UNDERFLOW),
        msg="$add should promote to int64 when the int32 result underflows INT32_MIN",
    ),
]

# Property [Int64 Overflow]: when an int64 result exceeds the int64 range, $add promotes to
# double.
ADD_INT64_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_overflow",
        doc={"a": INT64_MAX, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=pytest.approx(DOUBLE_FROM_INT64_MAX),
        msg="$add should promote to double when the int64 result overflows INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_underflow",
        doc={"a": INT64_MIN, "b": -1},
        expression={"$add": ["$a", "$b"]},
        expected=pytest.approx(-DOUBLE_FROM_INT64_MAX),
        msg="$add should promote to double when the int64 result underflows INT64_MIN",
    ),
]

# Property [Double Overflow]: when a double result exceeds the double range, $add returns
# infinity.
ADD_DOUBLE_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_overflow",
        doc={"a": 1e308, "b": 1e308},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$add should return positive infinity on double overflow",
    ),
    ExpressionTestCase(
        "double_underflow",
        doc={"a": -1e308, "b": -1e308},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$add should return negative infinity on double underflow",
    ),
]

ADD_OVERFLOW_ALL_TESTS = (
    ADD_INT32_OVERFLOW_TESTS + ADD_INT64_OVERFLOW_TESTS + ADD_DOUBLE_OVERFLOW_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ADD_OVERFLOW_ALL_TESTS))
def test_add_overflow(collection, test_case: ExpressionTestCase):
    """Test $add integer and double overflow and underflow cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
