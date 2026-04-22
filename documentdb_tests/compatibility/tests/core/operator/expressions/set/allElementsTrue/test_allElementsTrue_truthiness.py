"""
Tests for $allElementsTrue truthiness — divergent behavior only.

Common single-element truthiness is tested in test_set_common_truthiness.py.
This file covers multi-element arrays and empty array where $allElementsTrue
differs from $anyElementTrue.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.set.allElementsTrue.utils.allElementsTrue_utils import (  # noqa: E501
    AllElementsTrueTest,
    build_expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# ---------------------------------------------------------------------------
# Empty array — vacuous truth (differs from $anyElementTrue which returns false)
# ---------------------------------------------------------------------------


def test_allElementsTrue_empty_array(collection):
    """Test $allElementsTrue with empty array returns true (vacuous truth)."""
    result = execute_expression(collection, {"$allElementsTrue": [[]]})
    assert_expression_result(result, expected=True, msg="Empty array should return true")


# ---------------------------------------------------------------------------
# Multi-element mixed arrays — all must be truthy
# ---------------------------------------------------------------------------
MULTI_ELEMENT_TESTS: list[AllElementsTrueTest] = [
    AllElementsTrueTest(
        "nan_with_zero",
        array=[FLOAT_NAN, 0],
        expected=False,
        msg="Should return false for NaN combined with zero",
    ),
    AllElementsTrueTest(
        "nan_with_null",
        array=[FLOAT_NAN, None],
        expected=False,
        msg="Should return false for NaN combined with null",
    ),
    AllElementsTrueTest(
        "nan_both",
        array=[FLOAT_NAN, DECIMAL128_NAN],
        expected=True,
        msg="Should return true for both NaN types",
    ),
    AllElementsTrueTest(
        "inf_with_zero",
        array=[FLOAT_INFINITY, 0],
        expected=False,
        msg="Should return false for Infinity combined with zero",
    ),
    AllElementsTrueTest(
        "truthy_with_neg_zero",
        array=[1, DOUBLE_NEGATIVE_ZERO],
        expected=False,
        msg="Should return false for truthy with -0.0",
    ),
    AllElementsTrueTest(
        "neg_zero_both",
        array=[DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        expected=False,
        msg="Should return false for both neg zeros",
    ),
    AllElementsTrueTest(
        "decimal_1_0_truthy",
        array=[Decimal128("1.0")],
        expected=True,
        msg="Should return true for Decimal128 1.0",
    ),
    AllElementsTrueTest(
        "decimal_1_many_zeros_truthy",
        array=[Decimal128("1.00000000000000000000000000000000")],
        expected=True,
        msg="Should return true for Decimal128 1 with trailing zeros",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTI_ELEMENT_TESTS))
def test_allElementsTrue_multi_element(collection, test):
    """Test $allElementsTrue with multi-element arrays (divergent from $anyElementTrue)."""
    result = execute_expression(collection, build_expr(test))
    assert_expression_result(result, expected=test.expected, msg=test.msg)
