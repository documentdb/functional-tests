"""
arithmetic $sigmoid tests.

Core numeric type/value matrix for $sigmoid using both literal (inline) and
inserted document field arguments: zeros, unit values, and large-magnitude
saturation across int32, int64, double, and decimal128.
"""

import pytest
from bson import (
    Decimal128,
    Int64,
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
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

SIGMOID_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        expression={"$sigmoid": 0},
        expected=0.5,
        msg="sigmoid(0) = 0.5 (int32 input)",
    ),
    ExpressionTestCase(
        "int64_zero",
        expression={"$sigmoid": Int64(0)},
        expected=0.5,
        msg="sigmoid(0) = 0.5 (int64 input)",
    ),
    ExpressionTestCase(
        "double_zero",
        expression={"$sigmoid": 0.0},
        expected=0.5,
        msg="sigmoid(0.0) = 0.5",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        expression={"$sigmoid": DOUBLE_NEGATIVE_ZERO},
        expected=0.5,
        msg="sigmoid(-0.0) = 0.5",
    ),
    ExpressionTestCase(
        "decimal_zero",
        expression={"$sigmoid": Decimal128("0")},
        expected=Decimal128("0.5"),
        msg="sigmoid(decimal 0) = 0.5",
    ),
    ExpressionTestCase(
        "decimal_negative_zero",
        expression={"$sigmoid": Decimal128("-0")},
        expected=Decimal128("0.5"),
        msg="sigmoid(decimal -0) = 0.5",
    ),
    ExpressionTestCase(
        "int32_one",
        expression={"$sigmoid": 1},
        expected=pytest.approx(0.7310585786300049),
        msg="sigmoid(1) ~= 0.7311 (int32 input)",
    ),
    ExpressionTestCase(
        "int64_one",
        expression={"$sigmoid": Int64(1)},
        expected=pytest.approx(0.7310585786300049),
        msg="sigmoid(1) ~= 0.7311 (int64 input)",
    ),
    ExpressionTestCase(
        "double_one",
        expression={"$sigmoid": 1.0},
        expected=pytest.approx(0.7310585786300049),
        msg="sigmoid(1.0) ~= 0.7311",
    ),
    ExpressionTestCase(
        "decimal_one",
        expression={"$sigmoid": Decimal128("1")},
        expected=Decimal128("0.7310585786300048792511592418218362"),
        msg="sigmoid(decimal 1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "int32_neg_one",
        expression={"$sigmoid": -1},
        expected=pytest.approx(0.2689414213699951),
        msg="sigmoid(-1) ~= 0.2689 (int32 input)",
    ),
    ExpressionTestCase(
        "int64_neg_one",
        expression={"$sigmoid": Int64(-1)},
        expected=pytest.approx(0.2689414213699951),
        msg="sigmoid(-1) ~= 0.2689 (int64 input)",
    ),
    ExpressionTestCase(
        "double_neg_one",
        expression={"$sigmoid": -1.0},
        expected=pytest.approx(0.2689414213699951),
        msg="sigmoid(-1.0) ~= 0.2689",
    ),
    ExpressionTestCase(
        "decimal_neg_one",
        expression={"$sigmoid": Decimal128("-1")},
        expected=Decimal128("0.2689414213699951207488407581781638"),
        msg="sigmoid(decimal -1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "int32_ten",
        expression={"$sigmoid": 10},
        expected=pytest.approx(0.9999546021312976),
        msg="sigmoid(10) ~= 0.99995",
    ),
    ExpressionTestCase(
        "double_large_pos",
        expression={"$sigmoid": 1e10},
        expected=1.0,
        msg="large positive double (1e10) saturates to 1.0",
    ),
    ExpressionTestCase(
        "int32_max",
        expression={"$sigmoid": INT32_MAX},
        expected=1.0,
        msg="int32 max saturates to 1.0",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        expression={"$sigmoid": INT32_MAX_MINUS_1},
        expected=1.0,
        msg="int32 max-1 saturates to 1.0",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$sigmoid": INT64_MAX},
        expected=1.0,
        msg="int64 max saturates to 1.0",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        expression={"$sigmoid": INT64_MAX_MINUS_1},
        expected=1.0,
        msg="int64 max-1 saturates to 1.0",
    ),
    ExpressionTestCase(
        "int32_neg_ten",
        expression={"$sigmoid": -10},
        expected=pytest.approx(0.000045397868702434395),
        msg="sigmoid(-10) ~= 4.54e-5",
    ),
    ExpressionTestCase(
        "double_large_neg",
        expression={"$sigmoid": -1e10},
        expected=0.0,
        msg="large negative double (-1e10) saturates to 0.0",
    ),
    ExpressionTestCase(
        "int32_min",
        expression={"$sigmoid": INT32_MIN},
        expected=0.0,
        msg="int32 min saturates to 0.0",
    ),
    ExpressionTestCase(
        "int32_min_plus_1",
        expression={"$sigmoid": INT32_MIN_PLUS_1},
        expected=0.0,
        msg="int32 min+1 saturates to 0.0",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$sigmoid": INT64_MIN},
        expected=0.0,
        msg="int64 min saturates to 0.0",
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        expression={"$sigmoid": INT64_MIN_PLUS_1},
        expected=0.0,
        msg="int64 min+1 saturates to 0.0",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$sigmoid": DOUBLE_MIN_SUBNORMAL},
        expected=0.5,
        msg="smallest subnormal double ~= 0, sigmoid = 0.5",
    ),
    ExpressionTestCase(
        "double_near_min",
        expression={"$sigmoid": DOUBLE_NEAR_MIN},
        expected=0.5,
        msg="tiny double (1e-308) ~= 0, sigmoid = 0.5",
    ),
    ExpressionTestCase(
        "double_near_max",
        expression={"$sigmoid": DOUBLE_NEAR_MAX},
        expected=1.0,
        msg="huge double (1e308) saturates to 1.0",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        expression={"$sigmoid": DOUBLE_MAX_SAFE_INTEGER},
        expected=1.0,
        msg="2^53 max-safe-integer saturates to 1.0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIGMOID_LITERAL_TESTS))
def test_sigmoid_literal(collection, test):
    """Test $sigmoid with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


SIGMOID_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_one",
        expression={"$sigmoid": "$value"},
        doc={"value": 1},
        expected=pytest.approx(0.7310585786300049),
        msg="sigmoid(1) ~= 0.7311 (int32 input)",
    ),
    ExpressionTestCase(
        "int64_neg_one",
        expression={"$sigmoid": "$value"},
        doc={"value": Int64(-1)},
        expected=pytest.approx(0.2689414213699951),
        msg="sigmoid(-1) ~= 0.2689 (int64 input)",
    ),
    ExpressionTestCase(
        "double_zero",
        expression={"$sigmoid": "$value"},
        doc={"value": 0.0},
        expected=0.5,
        msg="sigmoid(0.0) = 0.5",
    ),
    ExpressionTestCase(
        "decimal_one",
        expression={"$sigmoid": "$value"},
        doc={"value": Decimal128("1")},
        expected=Decimal128("0.7310585786300048792511592418218362"),
        msg="sigmoid(decimal 1) to 34-digit precision",
    ),
    ExpressionTestCase(
        "int32_max",
        expression={"$sigmoid": "$value"},
        doc={"value": INT32_MAX},
        expected=1.0,
        msg="int32 max saturates to 1.0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIGMOID_INSERT_TESTS))
def test_sigmoid_insert(collection, test):
    """Test $sigmoid with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
