"""Tests for $isoWeek named-timezone and abbreviation application."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the ISO week
# is taken, which may cross a week boundary depending on the offset.
ISOWEEK_NAMED_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_ny_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "America/New_York"}},
        expected=24,
        msg="$isoWeek should return 24 for America/New_York with no week crossing",
    ),
    ExpressionTestCase(
        "tz_london_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "Europe/London"}},
        expected=24,
        msg="$isoWeek should return 24 for Europe/London with no week crossing",
    ),
    ExpressionTestCase(
        "tz_gmt_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "GMT"}},
        expected=24,
        msg="$isoWeek should return 24 for GMT with no week crossing",
    ),
    ExpressionTestCase(
        "tz_utc_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "UTC"}},
        expected=24,
        msg="$isoWeek should return 24 for UTC with no week crossing",
    ),
    ExpressionTestCase(
        "tz_asia_tokyo",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "Asia/Tokyo"}},
        expected=24,
        msg="$isoWeek should return 24 for Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_asia_kolkata",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "Asia/Kolkata"}},
        expected=24,
        msg="$isoWeek should return 24 for Asia/Kolkata",
    ),
    ExpressionTestCase(
        "tz_pacific_apia_fwd",
        doc={"date": datetime(2024, 1, 7, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "Pacific/Apia"}},
        expected=2,
        msg="$isoWeek should cross forward into week 2 for Pacific/Apia",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        doc={"date": datetime(2024, 1, 8, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "EST"}},
        expected=1,
        msg="$isoWeek should accept the EST abbreviation and cross back into week 1",
    ),
    ExpressionTestCase(
        "tz_utc_datetime_input",
        doc={"date": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoWeek": {"date": "$date", "timezone": "UTC"}},
        expected=3,
        msg="$isoWeek should return 3 for a mid-January date in UTC",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEK_NAMED_ZONE_TESTS))
def test_isoWeek_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $isoWeek named-timezone and abbreviation application."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
