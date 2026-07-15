"""
Double and Decimal128 boundary tests for $mod expression.

Covers negative zero sign preservation, infinity divisors, near-max and
min-subnormal doubles, and Decimal128 precision/boundary values (max, min,
large/small exponent) as the dividend.
"""

import pytest
from bson import Decimal128

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
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
)

MOD_DOUBLE_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "negative_zero_double_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DOUBLE_NEGATIVE_ZERO, "divisor": 3},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="Should preserve sign for negative zero double dividend",
    ),
    ExpressionTestCase(
        "negative_zero_decimal_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_NEGATIVE_ZERO, "divisor": Decimal128("3")},
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="Should preserve sign for negative zero decimal128 dividend",
    ),
    ExpressionTestCase(
        "inf_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": FLOAT_INFINITY},
        expected=10.0,
        msg="Should return dividend when divisor is infinity",
    ),
    ExpressionTestCase(
        "huge_modulo",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DOUBLE_NEAR_MAX, "divisor": 7},
        expected=3.0,
        msg="Should handle near-max double as dividend",
    ),
    ExpressionTestCase(
        "min_subnormal_modulo",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DOUBLE_MIN_SUBNORMAL, "divisor": 3},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="Should handle min subnormal double as dividend",
    ),
    ExpressionTestCase(
        "decimal_precision",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": Decimal128("10.5"), "divisor": Decimal128("3.2")},
        expected=Decimal128("0.9"),
        msg="Should preserve decimal128 precision",
    ),
    ExpressionTestCase(
        "decimal_max_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_MAX, "divisor": Decimal128("3")},
        expected=Decimal128("0"),
        msg="Should handle Decimal128 max value as dividend",
    ),
    ExpressionTestCase(
        "decimal_min_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_MIN, "divisor": Decimal128("3")},
        expected=Decimal128("-0"),
        msg="Should handle Decimal128 min value as dividend",
    ),
    ExpressionTestCase(
        "decimal_large_exponent_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_LARGE_EXPONENT, "divisor": Decimal128("3")},
        expected=Decimal128("1"),
        msg="Should handle Decimal128 large exponent as dividend",
    ),
    ExpressionTestCase(
        "decimal_small_exponent_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_SMALL_EXPONENT, "divisor": Decimal128("3")},
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="Should handle Decimal128 small exponent as dividend",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_DOUBLE_DECIMAL_BOUNDARY_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_DOUBLE_DECIMAL_BOUNDARY_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
