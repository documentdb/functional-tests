"""$dateTrunc timezone handling: named zones, numeric offsets, and DST transitions."""

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

# Property [Timezone Extremes]: out-of-range two-digit offsets and additional named zones are
# accepted.
DATETRUNC_TIMEZONE_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_over60_minutes_positive",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+05:70"}},
        expected=datetime(2021, 6, 15, 11, 50, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a +05:70 offset with over-60 minutes",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_negative",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-05:70"}},
        expected=datetime(2021, 6, 15, 11, 10, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a -05:70 offset with over-60 minutes",
    ),
    ExpressionTestCase(
        "tz_over24_hours_positive",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+25:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a +25:00 offset with over-24 hours",
    ),
    ExpressionTestCase(
        "tz_over24_hours_negative",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-25:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a -25:00 offset with over-24 hours",
    ),
    ExpressionTestCase(
        "tz_max_valid_positive",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+99:99"}},
        expected=datetime(2021, 6, 15, 11, 21, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the maximum two-digit +99:99 offset",
    ),
    ExpressionTestCase(
        "tz_max_valid_negative",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-99:99"}},
        expected=datetime(2021, 6, 15, 11, 39, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the maximum two-digit -99:99 offset",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "Pacific/Apia"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the Pacific/Apia named zone",
    ),
    ExpressionTestCase(
        "tz_offset_45min",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+05:45"}},
        expected=datetime(2021, 6, 15, 11, 15, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a +05:45 offset with 45 minutes",
    ),
    ExpressionTestCase(
        "tz_offset_half_hour_west",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-02:30"}},
        expected=datetime(2021, 6, 15, 11, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a -02:30 half-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_max_east",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+14:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the +14:00 maximum east offset",
    ),
    ExpressionTestCase(
        "tz_offset_max_west",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-11:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the -11:00 maximum west offset",
    ),
]

# Property [Timezone Offset]: named zones and numeric offsets shift the truncation boundary.
DATETRUNC_TIMEZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_shifts_day",
        doc={"date": datetime(2021, 3, 20, 2, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "-05:00"}},
        expected=datetime(2021, 3, 19, 5, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should shift the day boundary with a negative offset",
    ),
    ExpressionTestCase(
        "tz_gmt",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "GMT"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the GMT timezone",
    ),
    ExpressionTestCase(
        "tz_utc",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "UTC"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the UTC timezone",
    ),
    ExpressionTestCase(
        "tz_offset_half_hour_east",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "+05:30"}},
        expected=datetime(2021, 6, 14, 18, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate with a +05:30 offset",
    ),
    ExpressionTestCase(
        "tz_zero_offset",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "+00:00"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should treat a +00:00 offset as UTC",
    ),
    ExpressionTestCase(
        "tz_offset_no_colon",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "-0500"}},
        expected=datetime(2021, 6, 15, 5, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a no-colon offset format",
    ),
    ExpressionTestCase(
        "tz_offset_hour_only",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "+03"}},
        expected=datetime(2021, 6, 14, 21, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an hour-only offset format",
    ),
    ExpressionTestCase(
        "tz_kolkata_day",
        doc={"date": datetime(2021, 6, 15, 20, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "Asia/Kolkata"}},
        expected=datetime(2021, 6, 15, 18, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should handle a half-hour named zone for day truncation",
    ),
]

# Property [DST Day Truncation]: day truncation in a DST zone accounts for the transition.
DATETRUNC_DST_DAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dst_spring_forward_day",
        doc={"date": datetime(2021, 3, 14, 7, 30, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "America/New_York"}},
        expected=datetime(2021, 3, 14, 5, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should handle DST spring-forward day truncation",
    ),
    ExpressionTestCase(
        "dst_fall_back_day",
        doc={"date": datetime(2021, 11, 7, 6, 30, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "America/New_York"}},
        expected=datetime(2021, 11, 7, 4, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should handle DST fall-back day truncation",
    ),
]

# Property [DST Sub-Day Units]: hour and minute truncation are unaffected by DST transitions.
DATETRUNC_DST_SUBDAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dst_spring_hour_trunc",
        doc={"date": datetime(2021, 3, 14, 7, 30, 0, tzinfo=timezone.utc)},
        expression={
            "$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "America/New_York"}
        },
        expected=datetime(2021, 3, 14, 7, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the hour across DST spring-forward without adjustment",
    ),
    ExpressionTestCase(
        "dst_spring_minute_trunc",
        doc={"date": datetime(2021, 3, 14, 7, 0, 30, tzinfo=timezone.utc)},
        expression={
            "$dateTrunc": {"date": "$date", "unit": "minute", "timezone": "America/New_York"}
        },
        expected=datetime(2021, 3, 14, 7, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the minute across DST spring-forward without adjustment",
    ),
    ExpressionTestCase(
        "dst_fall_back_hour_trunc",
        doc={"date": datetime(2021, 11, 7, 6, 30, 0, tzinfo=timezone.utc)},
        expression={
            "$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "America/New_York"}
        },
        expected=datetime(2021, 11, 7, 6, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the hour across DST fall-back without adjustment",
    ),
]

DATETRUNC_TIMEZONE_ALL_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_TIMEZONE_ACCEPT_TESTS
    + DATETRUNC_TIMEZONE_TESTS
    + DATETRUNC_DST_DAY_TESTS
    + DATETRUNC_DST_SUBDAY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_TIMEZONE_ALL_TESTS))
def test_dateTrunc_timezone(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc shifts the truncation boundary by timezone and DST."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
