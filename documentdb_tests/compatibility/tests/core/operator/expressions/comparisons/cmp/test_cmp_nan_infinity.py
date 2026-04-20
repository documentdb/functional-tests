"""
Tests for $cmp numeric edge cases.

Covers sign handling, Infinity comparisons, NaN ordering, and cross-type Decimal128 Infinity.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_neg", expression={"$cmp": [-1, -1]}, expected=0, msg="Negative equals negative"
    ),
    ExpressionTestCase(
        "pos_neg", expression={"$cmp": [1, -1]}, expected=1, msg="Positive > negative"
    ),
    ExpressionTestCase(
        "neg_pos", expression={"$cmp": [-1, 1]}, expected=-1, msg="Negative < positive"
    ),
]


NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan_vs_0", expression={"$cmp": [FLOAT_NAN, 0]}, expected=-1, msg="float NaN < 0"
    ),
    ExpressionTestCase(
        "dec_nan_vs_0",
        expression={"$cmp": [DECIMAL128_NAN, 0]},
        expected=-1,
        msg="Decimal128 NaN < 0",
    ),
    ExpressionTestCase(
        "float_nan_vs_neg_inf",
        expression={"$cmp": [FLOAT_NAN, FLOAT_NEGATIVE_INFINITY]},
        expected=-1,
        msg="float NaN < -Infinity",
    ),
    ExpressionTestCase(
        "float_nan_vs_null",
        expression={"$cmp": [FLOAT_NAN, None]},
        expected=1,
        msg="NaN (numeric type) > null",
    ),
]


INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_vs_neg_inf",
        expression={"$cmp": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=1,
        msg="Infinity > -Infinity",
    ),
    ExpressionTestCase(
        "inf_vs_one",
        expression={"$cmp": [FLOAT_INFINITY, 1]},
        expected=1,
        msg="Infinity > 1",
    ),
    ExpressionTestCase(
        "neg_inf_vs_one",
        expression={"$cmp": [FLOAT_NEGATIVE_INFINITY, 1]},
        expected=-1,
        msg="-Infinity < 1",
    ),
]


DEC128_CROSS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_inf_dec_inf",
        expression={"$cmp": [FLOAT_INFINITY, DECIMAL128_INFINITY]},
        expected=0,
        msg="Float Inf equals Decimal128 Inf",
    ),
    ExpressionTestCase(
        "float_neg_inf_dec_neg_inf",
        expression={"$cmp": [FLOAT_NEGATIVE_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=0,
        msg="Float -Inf equals Decimal128 -Inf",
    ),
    ExpressionTestCase(
        "float_inf_dec_neg_inf",
        expression={"$cmp": [FLOAT_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=1,
        msg="Float Inf > Decimal128 -Inf",
    ),
]

ALL_TESTS = SIGN_TESTS + NAN_TESTS + INFINITY_TESTS + DEC128_CROSS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cmp_numeric_edge_cases(collection, test):
    """Test $cmp sign handling, NaN ordering, Infinity, and cross-type Decimal128 Infinity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
