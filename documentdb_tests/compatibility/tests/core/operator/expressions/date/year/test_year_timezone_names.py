"""Tests for $year named-timezone and abbreviation application, including DST and year crossings."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the calendar
# year is taken, which may cross a year boundary depending on the offset, while a DST
# transition within a year leaves the year unchanged.
YEAR_NAMED_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_utc_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "UTC"}},
        expected=2024,
        msg="$year should return 2024 for UTC with no year crossing",
    ),
    ExpressionTestCase(
        "tz_ny_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "America/New_York"}},
        expected=2024,
        msg="$year should return 2024 for America/New_York with no year crossing",
    ),
    ExpressionTestCase(
        "tz_tokyo_no_cross",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "Asia/Tokyo"}},
        expected=2024,
        msg="$year should return 2024 for Asia/Tokyo with no year crossing",
    ),
    ExpressionTestCase(
        "tz_ny_year_bwd",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "America/New_York"}},
        expected=2023,
        msg="$year should cross back to 2023 for America/New_York early on Jan 1",
    ),
    ExpressionTestCase(
        "tz_ny_year_stays",
        doc={"date": datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "America/New_York"}},
        expected=2024,
        msg="$year should stay in 2024 for America/New_York after the local new year",
    ),
    ExpressionTestCase(
        "tz_helsinki_year_fwd",
        doc={"date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "Europe/Helsinki"}},
        expected=2025,
        msg="$year should cross forward to 2025 for Europe/Helsinki late on Dec 31",
    ),
    ExpressionTestCase(
        "tz_kolkata_year_fwd",
        doc={"date": datetime(2024, 12, 31, 22, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "Asia/Kolkata"}},
        expected=2025,
        msg="$year should cross forward to 2025 for the half-hour Asia/Kolkata offset",
    ),
    ExpressionTestCase(
        "tz_la_year_bwd",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "America/Los_Angeles"}},
        expected=2023,
        msg="$year should cross back to 2023 for America/Los_Angeles early on Jan 1",
    ),
    ExpressionTestCase(
        "tz_ny_dst_spring",
        doc={"date": datetime(2024, 3, 10, 7, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "America/New_York"}},
        expected=2024,
        msg="$year should return 2024 across the America/New_York spring DST transition",
    ),
    ExpressionTestCase(
        "tz_ny_dst_fall",
        doc={"date": datetime(2024, 11, 3, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "America/New_York"}},
        expected=2024,
        msg="$year should return 2024 across the America/New_York fall DST transition",
    ),
    ExpressionTestCase(
        "tz_london_winter",
        doc={"date": datetime(2024, 12, 31, 23, 30, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "Europe/London"}},
        expected=2024,
        msg="$year should return 2024 for Europe/London in winter with no year crossing",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"date": datetime(2024, 12, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "Pacific/Apia"}},
        expected=2025,
        msg="$year should cross forward to 2025 for the +13 Pacific/Apia offset",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "EST"}},
        expected=2023,
        msg="$year should accept the EST abbreviation and cross back a year",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(YEAR_NAMED_ZONE_TESTS))
def test_year_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $year named-timezone and abbreviation application."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
