"""$dateTrunc with ObjectId/Timestamp inputs, timezone offsets, DST, boundaries, and extremes."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DATE_MS_BEFORE_EPOCH,
    DATE_MS_EPOCH,
    DATE_YEAR_1900,
    OID_MAX_SIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [ObjectId And Timestamp Input]: ObjectId and Timestamp inputs are truncated by their
# embedded time.
DATETRUNC_OID_TS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_trunc_day",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the day",
    ),
    ExpressionTestCase(
        "oid_trunc_hour",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the hour",
    ),
    ExpressionTestCase(
        "oid_trunc_month",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the month",
    ),
    ExpressionTestCase(
        "oid_trunc_year",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId to the year",
    ),
    ExpressionTestCase(
        "oid_with_tz",
        doc={"date": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "UTC"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an ObjectId with a timezone",
    ),
    ExpressionTestCase(
        "ts_trunc_day",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the day",
    ),
    ExpressionTestCase(
        "ts_trunc_hour",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the hour",
    ),
    ExpressionTestCase(
        "ts_trunc_month",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the month",
    ),
    ExpressionTestCase(
        "ts_trunc_year",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp to the year",
    ),
    ExpressionTestCase(
        "ts_with_tz",
        doc={"date": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "UTC"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a Timestamp with a timezone",
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

# Property [Boundary Idempotence]: a date already at a unit boundary is returned unchanged.
DATETRUNC_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_at_boundary",
        doc={"date": datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a year boundary",
    ),
    ExpressionTestCase(
        "month_at_boundary",
        doc={"date": datetime(2021, 6, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2021, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a month boundary",
    ),
    ExpressionTestCase(
        "day_at_boundary",
        doc={"date": datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a day boundary",
    ),
    ExpressionTestCase(
        "hour_at_boundary",
        doc={"date": datetime(2021, 6, 15, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at an hour boundary",
    ),
    ExpressionTestCase(
        "minute_at_boundary",
        doc={"date": datetime(2021, 6, 15, 10, 30, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "minute"}},
        expected=datetime(2021, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a minute boundary",
    ),
    ExpressionTestCase(
        "second_at_boundary",
        doc={"date": datetime(2021, 6, 15, 10, 30, 45, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "second"}},
        expected=datetime(2021, 6, 15, 10, 30, 45, tzinfo=timezone.utc),
        msg="$dateTrunc should return the date unchanged at a second boundary",
    ),
]

# Property [End Of Period]: a date at the end of a period truncates to that period's start.
DATETRUNC_END_OF_PERIOD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_end",
        doc={"date": datetime(2021, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the last millisecond of a year to the year start",
    ),
    ExpressionTestCase(
        "quarter_end_q1",
        doc={"date": datetime(2021, 3, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the end of Q1 to the Q1 start",
    ),
    ExpressionTestCase(
        "quarter_start_q2",
        doc={"date": datetime(2021, 4, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2021, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should return the Q2 start at the exact boundary",
    ),
    ExpressionTestCase(
        "day_end",
        doc={"date": datetime(2021, 6, 15, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2021, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate the last millisecond of a day to the day start",
    ),
]

# Property [Epoch And Distant Dates]: epoch, pre-epoch, distant past, and distant future dates
# truncate correctly, including from ObjectId and Timestamp inputs.
DATETRUNC_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"date": datetime(1970, 1, 1, 12, 30, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch-day date",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"date": datetime(1969, 6, 15, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(1969, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a pre-epoch date",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": datetime(1900, 3, 15, 8, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=DATE_YEAR_1900,
        msg="$dateTrunc should truncate a distant past date",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"date": datetime(2100, 7, 20, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(2100, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a distant future date",
    ),
    ExpressionTestCase(
        "oid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 12, 30, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch ObjectId",
    ),
    ExpressionTestCase(
        "ts_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 12, 30, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch Timestamp",
    ),
    ExpressionTestCase(
        "oid_future",
        doc={"date": oid_from_args(2035, 7, 20, 15, 0, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2035, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a future ObjectId",
    ),
    ExpressionTestCase(
        "ts_future",
        doc={"date": ts_from_args(2100, 7, 20, 15, 0, 0)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a future Timestamp",
    ),
]

# Property [Leap Year]: leap-day dates truncate correctly, including century leap-year rules.
DATETRUNC_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_day_trunc_day",
        doc={"date": datetime(2020, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2020, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a leap day to the day start",
    ),
    ExpressionTestCase(
        "leap_day_trunc_month",
        doc={"date": datetime(2020, 2, 29, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2020, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a leap day to the month start",
    ),
    ExpressionTestCase(
        "century_non_leap_1900_trunc_month",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(1900, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a 1900 February date to the month start",
    ),
    ExpressionTestCase(
        "century_leap_2000_trunc_month",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2000, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a 2000 leap day to the month start",
    ),
]

# Property [Far Future]: dates in year 9999 truncate correctly.
DATETRUNC_FAR_FUTURE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "far_future_year",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(9999, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a year 9999 date to the year start",
    ),
    ExpressionTestCase(
        "far_future_quarter",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "quarter"}},
        expected=datetime(9999, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a year 9999 date to the Q4 start",
    ),
]

# Property [DatetimeMS And Numeric Boundaries]: DatetimeMS, max Timestamp, and signed-boundary
# ObjectId inputs truncate correctly.
DATETRUNC_NUMERIC_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch_trunc_day",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=DATE_EPOCH,
        msg="$dateTrunc should truncate an epoch DatetimeMS to the day",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch_trunc_day",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a pre-epoch DatetimeMS to the day",
    ),
    ExpressionTestCase(
        "ts_max_s32_trunc_day",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2038, 1, 19, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a max signed 32-bit Timestamp to the day",
    ),
    ExpressionTestCase(
        "ts_max_u32_trunc_month",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "month"}},
        expected=datetime(2106, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a max unsigned 32-bit Timestamp to the month",
    ),
    ExpressionTestCase(
        "oid_max_signed32_trunc_day",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=datetime(2038, 1, 19, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a max signed 32-bit ObjectId to the day",
    ),
    ExpressionTestCase(
        "oid_high_bit_trunc_year",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateTrunc": {"date": "$date", "unit": "year"}},
        expected=datetime(1901, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate a high-bit ObjectId to the year",
    ),
]

DATETRUNC_TYPE_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_OID_TS_TESTS
    + DATETRUNC_TIMEZONE_TESTS
    + DATETRUNC_DST_DAY_TESTS
    + DATETRUNC_DST_SUBDAY_TESTS
    + DATETRUNC_BOUNDARY_TESTS
    + DATETRUNC_END_OF_PERIOD_TESTS
    + DATETRUNC_EPOCH_TESTS
    + DATETRUNC_LEAP_YEAR_TESTS
    + DATETRUNC_FAR_FUTURE_TESTS
    + DATETRUNC_NUMERIC_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_TYPE_TESTS))
def test_dateTrunc_types(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc date-typed inputs, timezones, and boundaries."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
