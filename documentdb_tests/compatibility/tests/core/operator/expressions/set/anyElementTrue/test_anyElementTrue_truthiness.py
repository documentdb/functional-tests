"""
Tests for $anyElementTrue truthiness — divergent behavior only.

Common single-element truthiness is tested in test_set_common_truthiness.py.
This file covers multi-element arrays and empty array where $anyElementTrue
differs from $allElementsTrue.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.set.anyElementTrue.utils.anyElementTrue_utils import (  # noqa: E501
    AnyElementTrueTest,
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
# Empty array — returns false (differs from $allElementsTrue which returns true)
# ---------------------------------------------------------------------------


def test_anyElementTrue_empty_array(collection):
    """Test $anyElementTrue with empty array returns false."""
    result = execute_expression(collection, {"$anyElementTrue": [[]]})
    assert_expression_result(result, expected=False, msg="Empty array should return false")


# ---------------------------------------------------------------------------
# Multi-element mixed arrays — any truthy is enough
# ---------------------------------------------------------------------------
MULTI_ELEMENT_TESTS: list[AnyElementTrueTest] = [
    AnyElementTrueTest(
        "nan_with_zero",
        array=[FLOAT_NAN, 0],
        expected=True,
        msg="Should return true for NaN combined with zero",
    ),
    AnyElementTrueTest(
        "nan_with_null",
        array=[FLOAT_NAN, None],
        expected=True,
        msg="Should return true for NaN combined with null",
    ),
    AnyElementTrueTest(
        "nan_both",
        array=[FLOAT_NAN, DECIMAL128_NAN],
        expected=True,
        msg="Should return true for both NaN types",
    ),
    AnyElementTrueTest(
        "inf_with_zero",
        array=[FLOAT_INFINITY, 0],
        expected=True,
        msg="Should return true for Infinity combined with zero",
    ),
    AnyElementTrueTest(
        "truthy_with_neg_zero",
        array=[1, DOUBLE_NEGATIVE_ZERO],
        expected=True,
        msg="Should return true for truthy with -0.0",
    ),
    AnyElementTrueTest(
        "neg_zero_both",
        array=[DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        expected=False,
        msg="Should return false for both neg zeros",
    ),
    AnyElementTrueTest(
        "decimal_1_0_truthy",
        array=[Decimal128("1.0")],
        expected=True,
        msg="Should return true for Decimal128 1.0",
    ),
    AnyElementTrueTest(
        "decimal_1_many_zeros_truthy",
        array=[Decimal128("1.00000000000000000000000000000000")],
        expected=True,
        msg="Should return true for Decimal128 1 with trailing zeros",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTI_ELEMENT_TESTS))
def test_anyElementTrue_multi_element(collection, test):
    """Test $anyElementTrue with multi-element arrays (divergent from $allElementsTrue)."""
    result = execute_expression(collection, build_expr(test))
    assert_expression_result(result, expected=test.expected, msg=test.msg)
