from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.median.utils.median_common import (  # noqa: E501
    MedianTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: if the sole operand is null, or missing, the
# result is null. If all values in a list are null or missing the result is
# null.
MEDIAN_NULL_TESTS: list[MedianTest] = [
    MedianTest(
        "null_sole_operand",
        args=None,
        expected=None,
        msg="$median should return null when the sole operand is null",
    ),
    MedianTest(
        "null_missing_sole",
        args=MISSING,
        expected=None,
        msg="$median should return null when the sole operand is a missing field",
    ),
    MedianTest(
        "null_expr_returning_null",
        args={"$literal": None},
        expected=None,
        msg="$median should return null when an expression returns null",
    ),
    MedianTest(
        "null_all_null",
        args=[None, None],
        expected=None,
        msg="$median should return null when all operands are null",
    ),
    MedianTest(
        "null_all_missing",
        args=[MISSING, MISSING],
        expected=None,
        msg="$median should return null when all operands are missing",
    ),
    MedianTest(
        "null_mixed_null_and_missing",
        args=[None, MISSING],
        expected=None,
        msg="$median should return null when operands are a mix of null and missing",
    ),
]

# Property [Null/Missing Exclusion]: null, missing, and non-numeric values in
# a list are excluded, so they do not affect the median of the remaining numeric
# values.
MEDIAN_NULL_EXCLUSION_TESTS: list[MedianTest] = [
    MedianTest(
        "null_excluded_from_list",
        args=[10, None, 20],
        expected=15.0,
        msg="$median should exclude null from calculation in a list",
    ),
    MedianTest(
        "null_missing_excluded_from_list",
        args=[10, MISSING, 20],
        expected=15.0,
        msg="$median should exclude missing from calculation in a list",
    ),
    MedianTest(
        "null_excluded_at_start",
        args=[None, 10, 20],
        expected=15.0,
        msg="$median should exclude null at the start of a list",
    ),
    MedianTest(
        "null_excluded_at_end",
        args=[10, 20, None],
        expected=15.0,
        msg="$median should exclude null at the end of a list",
    ),
    MedianTest(
        "null_missing_excluded_at_start",
        args=[MISSING, 10, 20],
        expected=15.0,
        msg="$median should exclude missing at the start of a list",
    ),
    MedianTest(
        "null_missing_excluded_at_end",
        args=[10, 20, MISSING],
        expected=15.0,
        msg="$median should exclude missing at the end of a list",
    ),
    MedianTest(
        "null_mixed_with_numeric",
        args=[MISSING, None, 30],
        expected=30.0,
        msg="$median should exclude null and missing, finding median of remaining values",
    ),
    MedianTest(
        "non_numeric_excluded",
        args=["hello", None, 10, 20, "world", MISSING],
        expected=15.0,
        msg="$median should exclude non-numeric strings along with null and missing",
    ),
]

MEDIAN_NULL_ALL_TESTS = MEDIAN_NULL_TESTS + MEDIAN_NULL_EXCLUSION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MEDIAN_NULL_ALL_TESTS))
def test_median_null(collection, test_case: MedianTest):
    """Test $median cases."""
    result = execute_expression(
        collection, {"$median": {"input": test_case.args, "method": "approximate"}}
    )
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
