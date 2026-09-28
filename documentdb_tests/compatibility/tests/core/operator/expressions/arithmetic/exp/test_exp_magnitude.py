"""Tests for $exp core exponentiation values, including signed zero."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Exponent Value]: $exp returns e raised to the input power.
EXP_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_int32",
        doc={"value": 1},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(2.718281828459045),
        msg="$exp should return e for int32 one",
    ),
    ExpressionTestCase(
        "positive_int64",
        doc={"value": Int64(1)},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(2.718281828459045),
        msg="$exp should return e for int64 one",
    ),
    ExpressionTestCase(
        "positive_double",
        doc={"value": 1.5},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(4.4816890703380645),
        msg="$exp should return e raised to 1.5 for double 1.5",
    ),
    ExpressionTestCase(
        "positive_decimal",
        doc={"value": Decimal128("1")},
        expression={"$exp": ["$value"]},
        expected=Decimal128("2.718281828459045235360287471352662"),
        msg="$exp should return e for decimal128 one",
    ),
    ExpressionTestCase(
        "negative_int32",
        doc={"value": -1},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(0.36787944117144233),
        msg="$exp should return e raised to -1 for int32 negative one",
    ),
    ExpressionTestCase(
        "negative_int64",
        doc={"value": Int64(-1)},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(0.36787944117144233),
        msg="$exp should return e raised to -1 for int64 negative one",
    ),
    ExpressionTestCase(
        "negative_double",
        doc={"value": -1.5},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(0.22313016014842982),
        msg="$exp should return e raised to -1.5 for double -1.5",
    ),
    ExpressionTestCase(
        "negative_decimal",
        doc={"value": Decimal128("-1")},
        expression={"$exp": ["$value"]},
        expected=Decimal128("0.3678794411714423215955237701614609"),
        msg="$exp should return e raised to -1 for decimal128 negative one",
    ),
]

# Property [Zero]: $exp of any zero, including negative zero, returns one.
EXP_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_int32",
        doc={"value": 0},
        expression={"$exp": ["$value"]},
        expected=1.0,
        msg="$exp should return one for int32 zero",
    ),
    ExpressionTestCase(
        "zero_int64",
        doc={"value": INT64_ZERO},
        expression={"$exp": ["$value"]},
        expected=1.0,
        msg="$exp should return one for int64 zero",
    ),
    ExpressionTestCase(
        "zero_double",
        doc={"value": DOUBLE_ZERO},
        expression={"$exp": ["$value"]},
        expected=1.0,
        msg="$exp should return one for double zero",
    ),
    ExpressionTestCase(
        "negative_zero_double",
        doc={"value": DOUBLE_NEGATIVE_ZERO},
        expression={"$exp": ["$value"]},
        expected=1.0,
        msg="$exp should return one for negative zero double",
    ),
    ExpressionTestCase(
        "zero_decimal",
        doc={"value": DECIMAL128_ZERO},
        expression={"$exp": ["$value"]},
        expected=Decimal128("1"),
        msg="$exp should return one for decimal128 zero",
    ),
    ExpressionTestCase(
        "negative_zero_decimal",
        doc={"value": DECIMAL128_NEGATIVE_ZERO},
        expression={"$exp": ["$value"]},
        expected=Decimal128("1"),
        msg="$exp should return one for negative zero decimal128",
    ),
]

EXP_MAGNITUDE_ALL_TESTS = EXP_VALUE_TESTS + EXP_ZERO_TESTS


@pytest.mark.parametrize("test_case", pytest_params(EXP_MAGNITUDE_ALL_TESTS))
def test_exp_magnitude(collection, test_case: ExpressionTestCase):
    """Test $exp exponentiation value and signed-zero cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
