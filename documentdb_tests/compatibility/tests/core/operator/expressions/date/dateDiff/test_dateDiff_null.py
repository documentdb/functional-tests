"""$dateDiff null and missing propagation: a null or missing operand returns null."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    MISSING,
)

# Property [Null Handling]: a null literal for startDate, endDate, or unit returns null.
DATEDIFF_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_startDate",
        expression={
            "$dateDiff": {
                "startDate": None,
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=None,
        msg="$dateDiff should return null for a null startDate",
    ),
    ExpressionTestCase(
        "null_endDate",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": None,
                "unit": "day",
            }
        },
        expected=None,
        msg="$dateDiff should return null for a null endDate",
    ),
    ExpressionTestCase(
        "null_unit",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": None,
            }
        },
        expected=None,
        msg="$dateDiff should return null for a null unit",
    ),
]

# Property [Missing Field Reference]: a missing startDate, endDate, unit, timezone, or
# startOfWeek field reference returns null.
DATEDIFF_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_startDate_ref",
        expression={
            "$dateDiff": {
                "startDate": MISSING,
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=None,
        msg="$dateDiff should return null for a missing startDate field reference",
    ),
    ExpressionTestCase(
        "missing_endDate_ref",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": MISSING,
                "unit": "day",
            }
        },
        expected=None,
        msg="$dateDiff should return null for a missing endDate field reference",
    ),
    ExpressionTestCase(
        "missing_unit_ref",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": MISSING,
            }
        },
        expected=None,
        msg="$dateDiff should return null for a missing unit field reference",
    ),
    ExpressionTestCase(
        "missing_timezone_ref",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": MISSING,
            }
        },
        expected=None,
        msg="$dateDiff should return null for a missing timezone field reference",
    ),
    ExpressionTestCase(
        "missing_startOfWeek_ref",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": MISSING,
            }
        },
        expected=None,
        msg="$dateDiff should return null for a missing startOfWeek field reference",
    ),
]

DATEDIFF_NULL_MISSING_TESTS: list[ExpressionTestCase] = DATEDIFF_NULL_TESTS + DATEDIFF_MISSING_TESTS


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_NULL_MISSING_TESTS))
def test_dateDiff_null(collection, test_case: ExpressionTestCase):
    """Test $dateDiff returns null for null literals and missing field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
