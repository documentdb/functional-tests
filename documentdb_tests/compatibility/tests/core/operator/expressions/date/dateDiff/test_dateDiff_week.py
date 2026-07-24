"""$dateDiff week counting: week boundaries crossed relative to startOfWeek."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Week Counting]: the difference counts week boundaries crossed relative to
# startOfWeek, defaulting to Sunday.
DATEDIFF_WEEK_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "jan_default_sun",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should count January weeks from the default Sunday start",
    ),
    ExpressionTestCase(
        "jan_monday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count January weeks from a Monday start",
    ),
    ExpressionTestCase(
        "jan_friday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "fri",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count January weeks from a Friday start",
    ),
    ExpressionTestCase(
        "feb_default_sun",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 2, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 28, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count February weeks from the default Sunday start",
    ),
    ExpressionTestCase(
        "feb_monday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 2, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 28, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(3),
        msg="$dateDiff should count February weeks from a Monday start",
    ),
    ExpressionTestCase(
        "feb_friday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 2, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 28, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "fri",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count February weeks from a Friday start",
    ),
    ExpressionTestCase(
        "mar_default_sun",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 31, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count March weeks from the default Sunday start",
    ),
    ExpressionTestCase(
        "mar_monday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count March weeks from a Monday start",
    ),
    ExpressionTestCase(
        "mar_friday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "fri",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count March weeks from a Friday start",
    ),
    ExpressionTestCase(
        "cross_year_week",
        expression={
            "$dateDiff": {
                "startDate": datetime(2020, 12, 28, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 4, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one week across the year boundary",
    ),
    ExpressionTestCase(
        "cross_month_week",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 25, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 8, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(2),
        msg="$dateDiff should count two weeks across the month boundary",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_WEEK_TESTS))
def test_dateDiff_week(collection, test_case: ExpressionTestCase):
    """Test $dateDiff counts week boundaries relative to the configured start of week."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
