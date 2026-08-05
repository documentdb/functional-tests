# handle non numerics
from __future__ import annotations

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.bitwise.bitOr.utils.bitOr_common import (  # noqa: E501
    BitOrTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# In mongosh, whole-number literals (1.0) are sent as Int32; explicit Double types
# and fractional doubles are rejected. In Python, float values are always BSON Double,
# so all float inputs trigger TypeMismatch regardless of whether the value is whole.
BITOR_NON_NUMERIC_TESTS: list[BitOrTest] = [
    BitOrTest(
        "strings_error",
        args=["error", "should", "occur", 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitOr with string operands should raise TypeMismatch",
    ),
    BitOrTest(
        "double_whole_error",
        args=[7.0, 8],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitOr with a BSON Double operand should raise TypeMismatch",
    ),
    BitOrTest(
        "double_fractional_error",
        args=[1.0, 2.0, 3.1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitOr with a fractional double should raise TypeMismatch",
    ),
    BitOrTest(
        "nan_error",
        args=[1, 2, 3, math.nan],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitOr with NaN should raise TypeMismatch",
    ),
    BitOrTest(
        "inf_error",
        args=[1, 2, 3, math.inf],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitOr with positive infinity should raise TypeMismatch",
    ),
    BitOrTest(
        "negative_inf_error",
        args=[1, 2, 3, -math.inf],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitOr with negative infinity should raise TypeMismatch",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(BITOR_NON_NUMERIC_TESTS))
def test_bitOr_non_numeric(collection, test_case: BitOrTest):
    """Test $bitOr non-numeric input handling."""
    result = execute_expression(collection, {"$bitOr": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
