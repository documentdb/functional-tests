"""
Representative BSON comparison engine wiring tests for $lte.

A small sample of cross-type and special value comparisons to confirm $lte
delegates to the BSON comparison engine correctly. Not an exhaustive matrix —
full BSON ordering coverage lives in /core/data_types/bson_types/.
"""

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_NEGATIVE_ZERO, FLOAT_NAN

BSON_WIRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "number_lte_string", expression={"$lte": [1, "a"]}, expected=True, msg="number <= string"
    ),
    ExpressionTestCase(
        "string_not_lte_number",
        expression={"$lte": ["a", 1]},
        expected=False,
        msg="string not <= number",
    ),
    ExpressionTestCase(
        "minkey_lte_number",
        expression={"$lte": [MinKey(), 1]},
        expected=True,
        msg="MinKey <= number",
    ),
    ExpressionTestCase(
        "maxkey_not_lte_number",
        expression={"$lte": [MaxKey(), 1]},
        expected=False,
        msg="MaxKey not <= number",
    ),
    ExpressionTestCase(
        "int_lte_equivalent_long",
        expression={"$lte": [1, Int64(1)]},
        expected=True,
        msg="int(1) <= long(1)",
    ),
    ExpressionTestCase(
        "int_lte_equivalent_decimal",
        expression={"$lte": [1, Decimal128("1")]},
        expected=True,
        msg="int(1) <= decimal(1)",
    ),
    ExpressionTestCase(
        "neg_zero_lte_zero",
        expression={"$lte": [DOUBLE_NEGATIVE_ZERO, 0.0]},
        expected=True,
        msg="-0.0 <= 0.0",
    ),
    ExpressionTestCase(
        "nan_lte_nan",
        expression={"$lte": [FLOAT_NAN, FLOAT_NAN]},
        expected=True,
        msg="NaN <= NaN (equal)",
    ),
    ExpressionTestCase(
        "nan_lte_zero", expression={"$lte": [FLOAT_NAN, 0]}, expected=True, msg="NaN <= 0"
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSON_WIRING_TESTS))
def test_lte_bson_wiring(collection, test):
    """Smoke test: confirm $lte is wired to the BSON comparison engine."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
