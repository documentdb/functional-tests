"""Tests for $week named-timezone and abbreviation application, including DST and week crossings."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the week is
# taken, which may cross a week or year boundary depending on the offset, while a DST transition
# within a week leaves the week unchanged.
WEEK_NAMED_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_utc_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "UTC"}},
        expected=28,
        msg="$week should return 28 for UTC with no week crossing",
    ),
    ExpressionTestCase(
        "tz_ny_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "America/New_York"}},
        expected=28,
        msg="$week should return 28 for America/New_York with no week crossing",
    ),
    ExpressionTestCase(
        "tz_tokyo_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "Asia/Tokyo"}},
        expected=28,
        msg="$week should return 28 for Asia/Tokyo with no week crossing",
    ),
    ExpressionTestCase(
        "tz_tokyo_week_fwd",
        doc={"date": datetime(2024, 1, 6, 22, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "Asia/Tokyo"}},
        expected=1,
        msg="$week should cross forward to week 1 for Asia/Tokyo late on the Saturday",
    ),
    ExpressionTestCase(
        "tz_la_week_bwd",
        doc={"date": datetime(2024, 1, 7, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "America/Los_Angeles"}},
        expected=0,
        msg="$week should cross back to week 0 for America/Los_Angeles early on the Sunday",
    ),
    ExpressionTestCase(
        "tz_ny_year_bwd",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "America/New_York"}},
        expected=53,
        msg="$week should cross back into the prior year's week 53 for America/New_York on Jan 1",
    ),
    ExpressionTestCase(
        "tz_ny_year_stays",
        doc={"date": datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "America/New_York"}},
        expected=0,
        msg="$week should stay in week 0 for America/New_York after the local new year",
    ),
    ExpressionTestCase(
        "tz_helsinki_year_fwd",
        doc={"date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "Europe/Helsinki"}},
        expected=0,
        msg="$week should cross forward into the next year's week 0 for Europe/Helsinki",
    ),
    ExpressionTestCase(
        "tz_kolkata_week_fwd",
        doc={"date": datetime(2024, 1, 6, 20, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "Asia/Kolkata"}},
        expected=1,
        msg="$week should cross forward to week 1 for the half-hour Asia/Kolkata offset",
    ),
    ExpressionTestCase(
        "tz_ny_dst_spring",
        doc={"date": datetime(2024, 3, 10, 7, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "America/New_York"}},
        expected=10,
        msg="$week should return 10 across the America/New_York spring DST transition",
    ),
    ExpressionTestCase(
        "tz_ny_dst_fall",
        doc={"date": datetime(2024, 11, 3, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "America/New_York"}},
        expected=44,
        msg="$week should return 44 across the America/New_York fall DST transition",
    ),
    ExpressionTestCase(
        "tz_london_bst",
        doc={"date": datetime(2024, 6, 29, 23, 30, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "Europe/London"}},
        expected=26,
        msg="$week should return 26 for Europe/London in summer under BST",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"date": datetime(2024, 1, 6, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "Pacific/Apia"}},
        expected=1,
        msg="$week should cross forward to week 1 for the +13 Pacific/Apia offset",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        doc={"date": datetime(2024, 1, 7, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "EST"}},
        expected=0,
        msg="$week should accept the EST abbreviation and cross back to week 0",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(WEEK_NAMED_ZONE_TESTS))
def test_week_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $week named-timezone and abbreviation application."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
