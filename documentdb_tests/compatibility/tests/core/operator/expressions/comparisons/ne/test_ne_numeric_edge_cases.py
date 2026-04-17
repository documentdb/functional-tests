"""
Tests for $ne numeric edge cases.

Covers sign handling, Infinity comparisons, and cross-type Decimal128 Infinity.
Numeric equivalence across types, negative zero, and NaN equality are tested in
/core/bson_types/test_bson_types_ordering.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)

SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_neg", expression={"$ne": [-1, -1]}, expected=False, msg="Negative equals negative"
    ),
    ExpressionTestCase(
        "pos_neg", expression={"$ne": [1, -1]}, expected=True, msg="Positive not equal to negative"
    ),
    ExpressionTestCase(
        "neg_pos", expression={"$ne": [-1, 1]}, expected=True, msg="Negative not equal to positive"
    ),
]


INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_neg_inf",
        expression={"$ne": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=True,
        msg="Infinity not equal to -Infinity",
    ),
    ExpressionTestCase(
        "inf_one",
        expression={"$ne": [FLOAT_INFINITY, 1]},
        expected=True,
        msg="Infinity not equal to 1",
    ),
    ExpressionTestCase(
        "neg_inf_one",
        expression={"$ne": [FLOAT_NEGATIVE_INFINITY, 1]},
        expected=True,
        msg="-Infinity not equal to 1",
    ),
]


DEC128_CROSS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec_inf_dec_neg_inf",
        expression={"$ne": [DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=True,
        msg="Decimal128 Inf not equal to Decimal128 -Inf",
    ),
    ExpressionTestCase(
        "float_inf_dec_inf",
        expression={"$ne": [FLOAT_INFINITY, DECIMAL128_INFINITY]},
        expected=False,
        msg="Float Inf equals Decimal128 Inf",
    ),
    ExpressionTestCase(
        "float_neg_inf_dec_neg_inf",
        expression={"$ne": [FLOAT_NEGATIVE_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=False,
        msg="Float -Inf equals Decimal128 -Inf",
    ),
    ExpressionTestCase(
        "float_inf_dec_neg_inf",
        expression={"$ne": [FLOAT_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=True,
        msg="Float Inf not equal to Decimal128 -Inf",
    ),
    ExpressionTestCase(
        "float_neg_inf_dec_inf",
        expression={"$ne": [FLOAT_NEGATIVE_INFINITY, DECIMAL128_INFINITY]},
        expected=True,
        msg="Float -Inf not equal to Decimal128 Inf",
    ),
]

ALL_TESTS = SIGN_TESTS + INFINITY_TESTS + DEC128_CROSS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ne_numeric_edge_cases(collection, test):
    """Test $ne sign handling, Infinity, and cross-type Decimal128 Infinity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
