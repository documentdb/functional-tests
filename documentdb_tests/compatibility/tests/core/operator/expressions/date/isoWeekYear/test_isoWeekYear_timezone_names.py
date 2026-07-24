"""Tests for $isoWeekYear named-timezone and abbreviation application."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant before the ISO
# week-numbering year is taken, which may cross a year boundary depending on the offset.
ISOWEEKYEAR_NAMED_ZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_ny_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "America/New_York"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for America/New_York with no year crossing",
    ),
    ExpressionTestCase(
        "tz_london_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "Europe/London"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for Europe/London with no year crossing",
    ),
    ExpressionTestCase(
        "tz_gmt_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "GMT"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for GMT with no year crossing",
    ),
    ExpressionTestCase(
        "tz_utc_no_cross",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "UTC"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for UTC with no year crossing",
    ),
    ExpressionTestCase(
        "tz_asia_tokyo",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "Asia/Tokyo"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_asia_kolkata",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "Asia/Kolkata"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for Asia/Kolkata",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "Pacific/Apia"}},
        expected=Int64(2024),
        msg="$isoWeekYear should return 2024 for Pacific/Apia",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation_cross",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "EST"}},
        expected=Int64(2023),
        msg="$isoWeekYear should accept the EST abbreviation and cross back a year",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEKYEAR_NAMED_ZONE_TESTS))
def test_isoWeekYear_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $isoWeekYear named-timezone and abbreviation application."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
