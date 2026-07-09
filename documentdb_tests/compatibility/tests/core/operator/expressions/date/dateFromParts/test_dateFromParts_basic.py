"""Tests for $dateFromParts arguments, null/missing, defaults, boundaries, and carry-over."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    DATEFROMPARTS_MISSING_YEAR_ERROR,
    DATEFROMPARTS_MIXING_ERROR,
    DATEFROMPARTS_MIXING_ISO_WITH_CALENDAR_ERROR,
    DATEFROMPARTS_NON_OBJECT_ERROR,
    DATEFROMPARTS_UNKNOWN_FIELD_ERROR,
    DATEFROMPARTS_YEAR_OUT_OF_RANGE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DATE_LEAP_FEB29,
    DATE_YEAR_1,
    DATE_YEAR_9999,
    MISSING,
)

# Property [Argument Handling]: a date is built from either calendar fields or ISO week-date fields.
DATEFROMPARTS_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_only",
        doc={"year": 2017},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should build a date from year alone",
    ),
    ExpressionTestCase(
        "calendar_all",
        doc={
            "year": 2017,
            "month": 2,
            "day": 8,
            "hour": 12,
            "minute": 30,
            "second": 45,
            "millisecond": 123,
        },
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "hour": "$hour",
                "minute": "$minute",
                "second": "$second",
                "millisecond": "$millisecond",
            }
        },
        expected=datetime(2017, 2, 8, 12, 30, 45, 123000, tzinfo=timezone.utc),
        msg="$dateFromParts should build a date from all calendar fields",
    ),
    ExpressionTestCase(
        "iso_year_only",
        doc={"isoWeekYear": 2017},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        expected=datetime(2017, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should build a date from isoWeekYear alone",
    ),
    ExpressionTestCase(
        "iso_all",
        doc={"isoWeekYear": 2017, "isoWeek": 6, "isoDayOfWeek": 3, "hour": 12},
        expression={
            "$dateFromParts": {
                "isoWeekYear": "$isoWeekYear",
                "isoWeek": "$isoWeek",
                "isoDayOfWeek": "$isoDayOfWeek",
                "hour": "$hour",
            }
        },
        expected=datetime(2017, 2, 8, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should build a date from all ISO week-date fields",
    ),
]

# Property [Field System Mixing]: combining calendar fields with ISO week-date fields is rejected.
DATEFROMPARTS_MIXING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mix_year_isoWeekYear",
        doc={"year": 2017, "isoWeekYear": 2017},
        expression={"$dateFromParts": {"year": "$year", "isoWeekYear": "$isoWeekYear"}},
        error_code=DATEFROMPARTS_MIXING_ERROR,
        msg="$dateFromParts should reject mixing year with isoWeekYear",
    ),
    ExpressionTestCase(
        "mix_year_isoWeek",
        doc={"year": 2017, "isoWeek": 6},
        expression={"$dateFromParts": {"year": "$year", "isoWeek": "$isoWeek"}},
        error_code=DATEFROMPARTS_MIXING_ERROR,
        msg="$dateFromParts should reject mixing year with isoWeek",
    ),
    ExpressionTestCase(
        "mix_isoWeekYear_month",
        doc={"isoWeekYear": 2017, "month": 2},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear", "month": "$month"}},
        error_code=DATEFROMPARTS_MIXING_ISO_WITH_CALENDAR_ERROR,
        msg="$dateFromParts should reject mixing isoWeekYear with calendar month",
    ),
]

# Property [Argument Validation]: a missing year, unknown field, or non-object argument is rejected.
DATEFROMPARTS_ARG_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_both",
        expression={"$dateFromParts": {"month": 2, "day": 8}},
        error_code=DATEFROMPARTS_MISSING_YEAR_ERROR,
        msg="$dateFromParts should reject an argument with neither year nor isoWeekYear",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$dateFromParts": {}},
        error_code=DATEFROMPARTS_MISSING_YEAR_ERROR,
        msg="$dateFromParts should reject an empty object argument",
    ),
    ExpressionTestCase(
        "unknown_field",
        expression={"$dateFromParts": {"year": 2017, "foo": 1}},
        error_code=DATEFROMPARTS_UNKNOWN_FIELD_ERROR,
        msg="$dateFromParts should reject an unknown field",
    ),
    ExpressionTestCase(
        "non_object_str",
        expression={"$dateFromParts": "string"},
        error_code=DATEFROMPARTS_NON_OBJECT_ERROR,
        msg="$dateFromParts should reject a string argument",
    ),
    ExpressionTestCase(
        "non_object_arr",
        expression={"$dateFromParts": [1, 2]},
        error_code=DATEFROMPARTS_NON_OBJECT_ERROR,
        msg="$dateFromParts should reject an array argument",
    ),
    ExpressionTestCase(
        "non_object_num",
        expression={"$dateFromParts": 123},
        error_code=DATEFROMPARTS_NON_OBJECT_ERROR,
        msg="$dateFromParts should reject a numeric argument",
    ),
]

# Property [Null Handling]: a null value for any field returns null.
DATEFROMPARTS_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_year",
        doc={"year": None},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=None,
        msg="$dateFromParts should return null for a null year",
    ),
    ExpressionTestCase(
        "null_month",
        doc={"year": 2017, "month": None},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        expected=None,
        msg="$dateFromParts should return null for a null month",
    ),
    ExpressionTestCase(
        "null_day",
        doc={"year": 2020, "day": None},
        expression={"$dateFromParts": {"year": "$year", "day": "$day"}},
        expected=None,
        msg="$dateFromParts should return null for a null day",
    ),
    ExpressionTestCase(
        "null_hour",
        doc={"year": 2020, "hour": None},
        expression={"$dateFromParts": {"year": "$year", "hour": "$hour"}},
        expected=None,
        msg="$dateFromParts should return null for a null hour",
    ),
    ExpressionTestCase(
        "null_minute",
        doc={"year": 2020, "minute": None},
        expression={"$dateFromParts": {"year": "$year", "minute": "$minute"}},
        expected=None,
        msg="$dateFromParts should return null for a null minute",
    ),
    ExpressionTestCase(
        "null_second",
        doc={"year": 2020, "second": None},
        expression={"$dateFromParts": {"year": "$year", "second": "$second"}},
        expected=None,
        msg="$dateFromParts should return null for a null second",
    ),
    ExpressionTestCase(
        "null_millisecond",
        doc={"year": 2020, "millisecond": None},
        expression={"$dateFromParts": {"year": "$year", "millisecond": "$millisecond"}},
        expected=None,
        msg="$dateFromParts should return null for a null millisecond",
    ),
    ExpressionTestCase(
        "null_isoWeekYear",
        doc={"isoWeekYear": None},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        expected=None,
        msg="$dateFromParts should return null for a null isoWeekYear",
    ),
]

# Property [Missing Field Reference]: a missing field reference for any field returns null.
DATEFROMPARTS_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_year_ref",
        expression={"$dateFromParts": {"year": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing year field reference",
    ),
    ExpressionTestCase(
        "missing_month_ref",
        expression={"$dateFromParts": {"year": 2020, "month": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing month field reference",
    ),
    ExpressionTestCase(
        "missing_day_ref",
        expression={"$dateFromParts": {"year": 2020, "day": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing day field reference",
    ),
    ExpressionTestCase(
        "missing_hour_ref",
        expression={"$dateFromParts": {"year": 2020, "hour": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing hour field reference",
    ),
    ExpressionTestCase(
        "missing_minute_ref",
        expression={"$dateFromParts": {"year": 2020, "minute": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing minute field reference",
    ),
    ExpressionTestCase(
        "missing_second_ref",
        expression={"$dateFromParts": {"year": 2020, "second": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing second field reference",
    ),
    ExpressionTestCase(
        "missing_millisecond_ref",
        expression={"$dateFromParts": {"year": 2020, "millisecond": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing millisecond field reference",
    ),
    ExpressionTestCase(
        "missing_isoWeekYear_ref",
        expression={"$dateFromParts": {"isoWeekYear": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing isoWeekYear field reference",
    ),
    ExpressionTestCase(
        "missing_isoWeek_ref",
        expression={"$dateFromParts": {"isoWeekYear": 2020, "isoWeek": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing isoWeek field reference",
    ),
    ExpressionTestCase(
        "missing_isoDayOfWeek_ref",
        expression={"$dateFromParts": {"isoWeekYear": 2020, "isoDayOfWeek": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing isoDayOfWeek field reference",
    ),
]

# Property [Default Values]: omitted optional fields default to the start of their range.
DATEFROMPARTS_DEFAULT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "default_all_optional",
        doc={"year": 2024},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should default all optional calendar fields to their minimum",
    ),
    ExpressionTestCase(
        "default_month_day",
        doc={"year": 2020, "month": 6},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        expected=datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should default day and time when only year and month are given",
    ),
    ExpressionTestCase(
        "default_day",
        doc={"year": 2020, "month": 6, "day": 15},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2020, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should default the time when only the date is given",
    ),
    ExpressionTestCase(
        "default_hour",
        doc={"year": 2020, "month": 6, "day": 15, "hour": 10},
        expression={
            "$dateFromParts": {"year": "$year", "month": "$month", "day": "$day", "hour": "$hour"}
        },
        expected=datetime(2020, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should default minute, second, and millisecond",
    ),
    ExpressionTestCase(
        "default_minute",
        doc={"year": 2020, "month": 6, "day": 15, "hour": 10, "minute": 30},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "hour": "$hour",
                "minute": "$minute",
            }
        },
        expected=datetime(2020, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should default second and millisecond",
    ),
    ExpressionTestCase(
        "default_second",
        doc={"year": 2020, "month": 6, "day": 15, "hour": 10, "minute": 30, "second": 45},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "hour": "$hour",
                "minute": "$minute",
                "second": "$second",
            }
        },
        expected=datetime(2020, 6, 15, 10, 30, 45, tzinfo=timezone.utc),
        msg="$dateFromParts should default millisecond",
    ),
    ExpressionTestCase(
        "iso_default_week_dow",
        doc={"isoWeekYear": 2020},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear"}},
        expected=datetime(2019, 12, 30, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should default isoWeek and isoDayOfWeek to 1",
    ),
    ExpressionTestCase(
        "iso_default_dow",
        doc={"isoWeekYear": 2020, "isoWeek": 10},
        expression={"$dateFromParts": {"isoWeekYear": "$isoWeekYear", "isoWeek": "$isoWeek"}},
        expected=datetime(2020, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should default isoDayOfWeek to 1",
    ),
]

# Property [Date Construction]: dates are built correctly across the epoch and distant past/future.
DATEFROMPARTS_CALENDAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "with_ms",
        doc={"year": 2024, "month": 1, "day": 1, "millisecond": 500},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "millisecond": "$millisecond",
            }
        },
        expected=datetime(2024, 1, 1, 0, 0, 0, 500000, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the millisecond component",
    ),
    ExpressionTestCase(
        "epoch",
        doc={"year": 1970, "month": 1, "day": 1},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=DATE_EPOCH,
        msg="$dateFromParts should build the Unix epoch",
    ),
    ExpressionTestCase(
        "iso_epoch",
        doc={"isoWeekYear": 1970, "isoWeek": 1, "isoDayOfWeek": 4},
        expression={
            "$dateFromParts": {
                "isoWeekYear": "$isoWeekYear",
                "isoWeek": "$isoWeek",
                "isoDayOfWeek": "$isoDayOfWeek",
            }
        },
        expected=DATE_EPOCH,
        msg="$dateFromParts should build the Unix epoch from ISO fields",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"year": 1969, "month": 12, "day": 31},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should build a pre-epoch date",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"year": 1900, "month": 6, "day": 15},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(1900, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should build a distant past date",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"year": 2100, "month": 3, "day": 1},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2100, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should build a distant future date",
    ),
]

# Property [Year Range]: a year within [1, 9999] is accepted; a year outside it is rejected.
DATEFROMPARTS_YEAR_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_min",
        doc={"year": 1},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=DATE_YEAR_1,
        msg="$dateFromParts should accept the minimum year",
    ),
    ExpressionTestCase(
        "year_max",
        doc={"year": 9999},
        expression={"$dateFromParts": {"year": "$year"}},
        expected=datetime(9999, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept the maximum year",
    ),
    ExpressionTestCase(
        "year_max_full",
        doc={
            "year": 9999,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "millisecond": 999,
        },
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "hour": "$hour",
                "minute": "$minute",
                "second": "$second",
                "millisecond": "$millisecond",
            }
        },
        expected=DATE_YEAR_9999,
        msg="$dateFromParts should build the maximum representable date",
    ),
    ExpressionTestCase(
        "year_zero",
        doc={"year": 0},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_YEAR_OUT_OF_RANGE_ERROR,
        msg="$dateFromParts should reject year zero as out of range",
    ),
    ExpressionTestCase(
        "year_10000",
        doc={"year": 10000},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_YEAR_OUT_OF_RANGE_ERROR,
        msg="$dateFromParts should reject a year above the maximum",
    ),
    ExpressionTestCase(
        "year_negative",
        doc={"year": -1},
        expression={"$dateFromParts": {"year": "$year"}},
        error_code=DATEFROMPARTS_YEAR_OUT_OF_RANGE_ERROR,
        msg="$dateFromParts should reject a negative year",
    ),
]

# Property [Out-of-Range Carry]: an out-of-range field value carries or borrows into adjacent
# fields.
DATEFROMPARTS_CARRY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "month_overflow",
        doc={"year": 2017, "month": 14, "day": 1, "hour": 12},
        expression={
            "$dateFromParts": {"year": "$year", "month": "$month", "day": "$day", "hour": "$hour"}
        },
        expected=datetime(2018, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry a month above 12 into the next year",
    ),
    ExpressionTestCase(
        "month_underflow",
        doc={"year": 2017, "month": 0, "day": 1, "hour": 12},
        expression={
            "$dateFromParts": {"year": "$year", "month": "$month", "day": "$day", "hour": "$hour"}
        },
        expected=datetime(2016, 12, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should borrow a month below 1 from the previous year",
    ),
    ExpressionTestCase(
        "negative_month",
        doc={"year": 2017, "month": -10},
        expression={"$dateFromParts": {"year": "$year", "month": "$month"}},
        expected=datetime(2016, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should borrow a negative month from the previous year",
    ),
    ExpressionTestCase(
        "day_overflow",
        doc={"year": 2024, "month": 1, "day": 32},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry a day past the month end into the next month",
    ),
    ExpressionTestCase(
        "day_underflow",
        doc={"year": 2024, "month": 3, "day": 0},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should borrow a day below 1 from the previous month",
    ),
    ExpressionTestCase(
        "apr31_carry",
        doc={"year": 2020, "month": 4, "day": 31},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2020, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry day 31 of a 30-day month into the next month",
    ),
    ExpressionTestCase(
        "year_boundary_dec31_to_jan1",
        doc={"year": 2020, "month": 12, "day": 32},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry across the year boundary from December",
    ),
    ExpressionTestCase(
        "hour_overflow",
        doc={"year": 2024, "month": 1, "day": 1, "hour": 25},
        expression={
            "$dateFromParts": {"year": "$year", "month": "$month", "day": "$day", "hour": "$hour"}
        },
        expected=datetime(2024, 1, 2, 1, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry an hour above 23 into the next day",
    ),
    ExpressionTestCase(
        "minute_overflow",
        doc={"year": 2020, "month": 1, "day": 1, "hour": 0, "minute": 61},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "hour": "$hour",
                "minute": "$minute",
            }
        },
        expected=datetime(2020, 1, 1, 1, 1, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry a minute above 59 into the next hour",
    ),
    ExpressionTestCase(
        "minute_underflow",
        doc={"year": 2020, "month": 1, "day": 1, "hour": 0, "minute": -1},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "hour": "$hour",
                "minute": "$minute",
            }
        },
        expected=datetime(2019, 12, 31, 23, 59, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should borrow a negative minute from the previous hour",
    ),
    ExpressionTestCase(
        "second_overflow",
        doc={"year": 2020, "month": 1, "day": 1, "second": 61},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "second": "$second",
            }
        },
        expected=datetime(2020, 1, 1, 0, 1, 1, tzinfo=timezone.utc),
        msg="$dateFromParts should carry a second above 59 into the next minute",
    ),
    ExpressionTestCase(
        "ms_overflow",
        doc={"year": 2020, "month": 1, "day": 1, "millisecond": 1000},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "millisecond": "$millisecond",
            }
        },
        expected=datetime(2020, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        msg="$dateFromParts should carry a millisecond above 999 into the next second",
    ),
    ExpressionTestCase(
        "ms_underflow",
        doc={"year": 2020, "month": 1, "day": 1, "millisecond": -1},
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "millisecond": "$millisecond",
            }
        },
        expected=datetime(2019, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
        msg="$dateFromParts should borrow a negative millisecond from the previous second",
    ),
    ExpressionTestCase(
        "cascade_carry",
        doc={
            "year": 2020,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "millisecond": 1000,
        },
        expression={
            "$dateFromParts": {
                "year": "$year",
                "month": "$month",
                "day": "$day",
                "hour": "$hour",
                "minute": "$minute",
                "second": "$second",
                "millisecond": "$millisecond",
            }
        },
        expected=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should cascade a carry across every field into the next year",
    ),
    ExpressionTestCase(
        "day_366_leap",
        doc={"year": 2020, "month": 1, "day": 366},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2020, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should place day 366 on December 31 of a leap year",
    ),
    ExpressionTestCase(
        "day_366_non_leap",
        doc={"year": 2021, "month": 1, "day": 366},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry day 366 into the next year for a non-leap year",
    ),
]

# Property [Leap Year]: February 29 is valid in leap years and carries into March otherwise.
DATEFROMPARTS_LEAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_feb29",
        doc={"year": 2020, "month": 2, "day": 29},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2020, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept February 29 in a leap year",
    ),
    ExpressionTestCase(
        "leap_feb29_2024",
        doc={"year": 2024, "month": 2, "day": 29},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept February 29 in another leap year",
    ),
    ExpressionTestCase(
        "non_leap_feb29_carry",
        doc={"year": 2021, "month": 2, "day": 29},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2021, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry February 29 into March for a non-leap year",
    ),
    ExpressionTestCase(
        "leap_feb30_carry",
        doc={"year": 2020, "month": 2, "day": 30},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2020, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry February 30 into March in a leap year",
    ),
    ExpressionTestCase(
        "century_non_leap_1900",
        doc={"year": 1900, "month": 2, "day": 29},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(1900, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should treat 1900 as a non-leap year (divisible by 100, not 400)",
    ),
    ExpressionTestCase(
        "century_non_leap_2100",
        doc={"year": 2100, "month": 2, "day": 29},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=datetime(2100, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should treat 2100 as a non-leap year",
    ),
    ExpressionTestCase(
        "century_leap_2000",
        doc={"year": 2000, "month": 2, "day": 29},
        expression={"$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}},
        expected=DATE_LEAP_FEB29,
        msg="$dateFromParts should treat 2000 as a leap year (divisible by 400)",
    ),
]

# Property [ISO Week Carry]: out-of-range ISO week and day-of-week values carry across boundaries.
DATEFROMPARTS_ISO_CARRY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "iso_week_53_valid",
        doc={"isoWeekYear": 2020, "isoWeek": 53, "isoDayOfWeek": 1},
        expression={
            "$dateFromParts": {
                "isoWeekYear": "$isoWeekYear",
                "isoWeek": "$isoWeek",
                "isoDayOfWeek": "$isoDayOfWeek",
            }
        },
        expected=datetime(2020, 12, 28, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept ISO week 53 in a 53-week year",
    ),
    ExpressionTestCase(
        "iso_week_53_carry",
        doc={"isoWeekYear": 2021, "isoWeek": 53, "isoDayOfWeek": 1},
        expression={
            "$dateFromParts": {
                "isoWeekYear": "$isoWeekYear",
                "isoWeek": "$isoWeek",
                "isoDayOfWeek": "$isoDayOfWeek",
            }
        },
        expected=datetime(2022, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry ISO week 53 into the next year for a 52-week year",
    ),
    ExpressionTestCase(
        "iso_dow_0_carry",
        doc={"isoWeekYear": 2020, "isoWeek": 1, "isoDayOfWeek": 0},
        expression={
            "$dateFromParts": {
                "isoWeekYear": "$isoWeekYear",
                "isoWeek": "$isoWeek",
                "isoDayOfWeek": "$isoDayOfWeek",
            }
        },
        expected=datetime(2019, 12, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should borrow ISO day-of-week 0 from the previous week",
    ),
    ExpressionTestCase(
        "iso_dow_8_carry",
        doc={"isoWeekYear": 2020, "isoWeek": 1, "isoDayOfWeek": 8},
        expression={
            "$dateFromParts": {
                "isoWeekYear": "$isoWeekYear",
                "isoWeek": "$isoWeek",
                "isoDayOfWeek": "$isoDayOfWeek",
            }
        },
        expected=datetime(2020, 1, 6, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should carry ISO day-of-week 8 into the next week",
    ),
]

DATEFROMPARTS_BASIC_TESTS: list[ExpressionTestCase] = (
    DATEFROMPARTS_ARG_TESTS
    + DATEFROMPARTS_MIXING_TESTS
    + DATEFROMPARTS_ARG_ERROR_TESTS
    + DATEFROMPARTS_NULL_TESTS
    + DATEFROMPARTS_MISSING_TESTS
    + DATEFROMPARTS_DEFAULT_TESTS
    + DATEFROMPARTS_CALENDAR_TESTS
    + DATEFROMPARTS_YEAR_BOUNDARY_TESTS
    + DATEFROMPARTS_CARRY_TESTS
    + DATEFROMPARTS_LEAP_TESTS
    + DATEFROMPARTS_ISO_CARRY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMPARTS_BASIC_TESTS))
def test_dateFromParts_basic(collection, test_case: ExpressionTestCase):
    """Test $dateFromParts basic operations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
