"""Tests for $isoDayOfWeek named-timezone and abbreviation application."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the ISO day
# is taken, which may cross a day boundary depending on the offset.
ISODAYOFWEEK_NAMED_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_ny_bwd",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=5,
        msg="$isoDayOfWeek should cross backward to Friday for America/New_York",
    ),
    ExpressionTestCase(
        "tz_gmt_no_cross",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "GMT",
            }
        },
        expected=6,
        msg="$isoDayOfWeek should return 6 for GMT with no day crossing",
    ),
    ExpressionTestCase(
        "tz_utc_no_cross",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=6,
        msg="$isoDayOfWeek should return 6 for UTC with no day crossing",
    ),
    ExpressionTestCase(
        "tz_london_winter_no_cross",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=1,
        msg="$isoDayOfWeek should return 1 for Europe/London in winter with no day crossing",
    ),
    ExpressionTestCase(
        "tz_apia_fwd",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=1,
        msg="$isoDayOfWeek should cross forward to Monday for Pacific/Apia (+13:00)",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, 3, 0, 0, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=7,
        msg="$isoDayOfWeek should accept the EST three-letter abbreviation and cross to Sunday",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ISODAYOFWEEK_NAMED_ZONE_TESTS))
def test_isoDayOfWeek_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $isoDayOfWeek named-timezone and abbreviation application."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
