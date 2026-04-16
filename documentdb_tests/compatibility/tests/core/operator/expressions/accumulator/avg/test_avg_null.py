from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.avg.utils.avg_common import (  # noqa: E501
    AvgTest,
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
AVG_NULL_TESTS: list[AvgTest] = [
    AvgTest(
        "null_sole_operand",
        args=None,
        expected=None,
        msg="$avg should return null when the sole operand is null",
    ),
    AvgTest(
        "null_missing_sole",
        args=MISSING,
        expected=None,
        msg="$avg should return null when the sole operand is a missing field",
    ),
    AvgTest(
        "null_expr_returning_null",
        args={"$literal": None},
        expected=None,
        msg="$avg should return null when an expression returns null",
    ),
    AvgTest(
        "null_all_null",
        args=[None, None],
        expected=None,
        msg="$avg should return null when all operands are null",
    ),
    AvgTest(
        "null_all_missing",
        args=[MISSING, MISSING],
        expected=None,
        msg="$avg should return null when all operands are missing",
    ),
    AvgTest(
        "null_mixed_null_and_missing",
        args=[None, MISSING],
        expected=None,
        msg="$avg should return null when operands are a mix of null and missing",
    ),
    AvgTest(
        "null_mixed_missing_and_null",
        args=[MISSING, None],
        expected=None,
        msg="$avg should return null when operands are missing followed by null",
    ),
]

# Property [Null/Missing Exclusion]: null and missing values in a list are
# excluded from both sum and count, so they do not affect the average of
# the remaining numeric values.
AVG_NULL_EXCLUSION_TESTS: list[AvgTest] = [
    AvgTest(
        "null_excluded_from_list",
        args=[10, None, 20],
        expected=15.0,
        msg="$avg should exclude null from sum and count in a list",
    ),
    AvgTest(
        "null_missing_excluded_from_list",
        args=[10, MISSING, 20],
        expected=15.0,
        msg="$avg should exclude missing from sum and count in a list",
    ),
    AvgTest(
        "null_excluded_at_start",
        args=[None, 10, 20],
        expected=15.0,
        msg="$avg should exclude null at the start of a list",
    ),
    AvgTest(
        "null_excluded_at_end",
        args=[10, 20, None],
        expected=15.0,
        msg="$avg should exclude null at the end of a list",
    ),
    AvgTest(
        "null_missing_excluded_at_start",
        args=[MISSING, 10, 20],
        expected=15.0,
        msg="$avg should exclude missing at the start of a list",
    ),
    AvgTest(
        "null_missing_excluded_at_end",
        args=[10, 20, MISSING],
        expected=15.0,
        msg="$avg should exclude missing at the end of a list",
    ),
    AvgTest(
        "null_mixed_with_numeric",
        args=[MISSING, None, 30],
        expected=30.0,
        msg="$avg should exclude null and missing, averaging only numeric values",
    ),
    AvgTest(
        "null_excluded_at_all_positions",
        args=[None, 10, None, 20, None],
        expected=15.0,
        msg="$avg should exclude null at start, middle, and end simultaneously",
    ),
    AvgTest(
        "null_missing_excluded_at_all_positions",
        args=[MISSING, 10, MISSING, 20, MISSING],
        expected=15.0,
        msg="$avg should exclude missing at start, middle, and end simultaneously",
    ),
]

AVG_NULL_ALL_TESTS = AVG_NULL_TESTS + AVG_NULL_EXCLUSION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(AVG_NULL_ALL_TESTS))
def test_avg_null(collection, test_case: AvgTest):
    """Test $avg cases."""
    result = execute_expression(collection, {"$avg": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
