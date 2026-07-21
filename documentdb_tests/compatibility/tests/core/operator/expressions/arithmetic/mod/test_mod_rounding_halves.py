"""
Rounding-precision tests for $mod expression near the 0.5 boundary.

Verifies double and Decimal128 precision is preserved for dividends just
below and just above a half value.
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
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
)

MOD_ROUNDING_HALVES_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "just_below_half_mod_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DOUBLE_JUST_BELOW_HALF, "divisor": 1},
        expected=pytest.approx(0.4999999999999994),
        msg="Should preserve precision near 0.5 boundary",
    ),
    ExpressionTestCase(
        "just_above_half_mod_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DOUBLE_JUST_ABOVE_HALF, "divisor": 1},
        expected=pytest.approx(0.500000001),
        msg="Should preserve precision just above 0.5",
    ),
    ExpressionTestCase(
        "decimal_just_below_half_mod_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_JUST_BELOW_HALF, "divisor": Decimal128("1")},
        expected=Decimal128("0.4999999999999999999999999999999999"),
        msg="Should preserve decimal precision near 0.5",
    ),
    ExpressionTestCase(
        "decimal_just_above_half_mod_one",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_JUST_ABOVE_HALF, "divisor": Decimal128("1")},
        expected=Decimal128("0.5000000000000000000000000000000001"),
        msg="Should preserve decimal precision just above 0.5",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_ROUNDING_HALVES_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_ROUNDING_HALVES_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
