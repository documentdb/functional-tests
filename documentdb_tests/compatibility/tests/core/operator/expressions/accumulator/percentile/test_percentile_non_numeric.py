"""Non-numeric input handling for the $percentile expression operator.

$percentile considers only numeric values, ignoring non-numeric entries, and
returns [null] when no numeric value remains. Captured against MongoDB 8.3.4.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.percentile.utils.percentile_common import (  # noqa: E501
    PercentileTest,
    percentile_spec,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Numeric Handling]: non-numeric entries are excluded; an input
# with no numeric values yields [null].
PERCENTILE_NON_NUMERIC_TESTS: list[PercentileTest] = [
    PercentileTest(
        "nonnum_ignored",
        spec=percentile_spec({"$literal": [10, "x", 20, True, 30]}, [0.5]),
        expected=[20.0],
        msg="$percentile should ignore non-numeric entries and use the numeric set [10,20,30]",
    ),
    PercentileTest(
        "nonnum_all_non_numeric",
        spec=percentile_spec({"$literal": ["a", "b"]}, [0.5]),
        expected=[None],
        msg="$percentile over all-non-numeric input should return [null]",
    ),
    PercentileTest(
        "nonnum_all_null",
        spec=percentile_spec({"$literal": [None, None]}, [0.5]),
        expected=[None],
        msg="$percentile over all-null input should return [null]",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(PERCENTILE_NON_NUMERIC_TESTS))
def test_percentile_non_numeric(collection, test_case: PercentileTest):
    """Test $percentile non-numeric input handling."""
    result = execute_expression(collection, {"$percentile": test_case.spec})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
