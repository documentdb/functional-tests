"""$dateSubtract date edge cases: leap years, month clamping, boundaries, and non-date starts."""

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
from documentdb_tests.framework.error_codes import DATEADD_INVALID_LARGE_VALUE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DATE_MS_EPOCH,
    DATE_Y2K,
    DATE_YEAR_1,
    DATE_YEAR_1900,
    DATE_YEAR_9999,
    OID_EPOCH,
    OID_MAX_SIGNED32,
    OID_MIN_SIGNED32,
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Leap Year]: subtracting across February resolves leap-year day counts correctly.
DATESUBTRACT_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_year_feb28_sub_year",
        doc={"date": datetime(2001, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2000, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 28 when subtracting a year into a leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb29_sub_year",
        doc={"date": datetime(2020, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2019, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Feb 29 to Feb 28 subtracting a year into a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_sub_day_to_feb29",
        doc={"date": datetime(2000, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_mar1_sub_day",
        doc={"date": datetime(1999, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1999, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_mar29_sub_month",
        doc={"date": datetime(2020, 3, 29, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a month from Mar 29 to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "leap_year_365_days",
        doc={"date": datetime(2020, 12, 31, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not wrap the year when subtracting 365 days in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_365_days",
        doc={"date": datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2019, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should wrap to the prior year subtracting 365 days into a non-leap year",
    ),
]

# Property [Century Leap Year]: the divisible-by-100/400 leap rule is honored.
DATESUBTRACT_CENTURY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "century_non_leap_1900_mar1_sub_day",
        doc={"date": datetime(1900, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 28 in 1900, a non-leap century year",
    ),
    ExpressionTestCase(
        "century_leap_2000_mar1_sub_day",
        doc={"date": datetime(2000, 3, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should land on Feb 29 in 2000, a leap century year",
    ),
]

# Property [Month Clamping]: subtracting months or quarters clamps to the last valid day of the
# target month.
DATESUBTRACT_MONTH_CLAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mar31_sub_month_leap",
        doc={"date": datetime(2000, 3, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Mar 31 minus 1 month to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "mar31_sub_month_non_leap",
        doc={"date": datetime(2021, 3, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Mar 31 minus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "may31_sub_month",
        doc={"date": datetime(2000, 5, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp May 31 minus 1 month to Apr 30",
    ),
    ExpressionTestCase(
        "jul31_sub_month",
        doc={"date": datetime(2000, 7, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp Jul 31 minus 1 month to Jun 30",
    ),
    ExpressionTestCase(
        "jan31_sub_month_no_adjustment",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not adjust Jan 31 minus 1 month, landing on Dec 31",
    ),
    ExpressionTestCase(
        "dec31_sub_year_no_adjustment",
        doc={"date": datetime(2021, 12, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not adjust Dec 31 when subtracting a year",
    ),
    ExpressionTestCase(
        "apr30_sub_quarter",
        doc={"date": datetime(2021, 4, 30, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "quarter", "amount": 1}},
        expected=datetime(2021, 1, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract 1 quarter from Apr 30 to Jan 30",
    ),
    ExpressionTestCase(
        "large_positive_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 49}},
        expected=datetime(2016, 11, 30, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp a large positive month amount to end-of-month",
    ),
    ExpressionTestCase(
        "large_negative_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": -50}},
        expected=datetime(2025, 2, 28, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateSubtract should clamp a large negative month amount to end-of-month",
    ),
]

# Property [Boundary Crossing]: subtracting across day, month, and year boundaries carries
# correctly.
DATESUBTRACT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec31_sub_day",
        doc={"date": datetime(2001, 1, 1, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the year boundary from Jan 1 minus 1 day",
    ),
    ExpressionTestCase(
        "jan1_add_day",
        doc={"date": DATE_Y2K},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(2000, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the day boundary from Jan 1 with a negative amount",
    ),
    ExpressionTestCase(
        "dec31_sub_hour",
        doc={"date": datetime(2001, 1, 1, 1, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 2}},
        expected=datetime(2000, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the year boundary from Jan 1 minus 2 hours",
    ),
]

# Property [Historical And Future]: distant past and future start dates are handled.
DATESUBTRACT_HISTORICAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "historical_date",
        doc={"date": datetime(1910, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 10}},
        expected=datetime(1900, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle a 1910 historical date",
    ),
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 4, 10, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 100}},
        expected=datetime(1960, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle a pre-epoch 1960 date",
    ),
    ExpressionTestCase(
        "far_future",
        doc={"date": datetime(2200, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 100}},
        expected=datetime(2100, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle a far-future 2200 date",
    ),
    ExpressionTestCase(
        "large_year_amount",
        doc={"date": datetime(3000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1000}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle subtracting 1000 years",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": datetime(1901, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=DATE_YEAR_1900,
        msg="$dateSubtract should handle 1901 minus 1 year",
    ),
    ExpressionTestCase(
        "distant_future_month",
        doc={"date": datetime(2100, 7, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 6}},
        expected=datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should handle 2100 minus 6 months",
    ),
]

# Property [Epoch Crossing]: subtracting forward and backward across the Unix epoch is correct.
DATESUBTRACT_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch_sub_day",
        doc={"date": datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=DATE_EPOCH,
        msg="$dateSubtract should subtract a day to reach the epoch",
    ),
    ExpressionTestCase(
        "cross_epoch_back",
        doc={"date": DATE_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should cross the epoch backward to 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_to_epoch",
        doc={"date": datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=DATE_EPOCH,
        msg="$dateSubtract should cross the epoch forward from 1969 with a negative amount",
    ),
]

# Property [Date Limits]: subtracting near the minimum representable date is handled.
DATESUBTRACT_DATE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_min_date",
        doc={"date": datetime(1, 1, 1, 0, 0, 1, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "millisecond", "amount": 1}},
        expected=datetime(1, 1, 1, 0, 0, 0, 999000, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract 1 millisecond near the minimum date",
    ),
    ExpressionTestCase(
        "year_9999_sub_large_ms",
        doc={"date": DATE_YEAR_9999},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "millisecond",
                "amount": 253_402_300_799_999,
            }
        },
        expected=DATE_EPOCH,
        msg="$dateSubtract should reach the epoch from the max date with a large ms amount",
    ),
    ExpressionTestCase(
        "at_python_min_year",
        doc={"date": datetime(1, 1, 1, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 23}},
        expected=DATE_YEAR_1,
        msg="$dateSubtract should subtract 23 hours at year 1",
    ),
]

# Property [Unit Equivalence]: a smaller unit times its multiple equals the larger unit.
DATESUBTRACT_UNIT_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "millisecond_1000_equals_second_1",
        doc={"date": datetime(2000, 1, 1, 12, 0, 1, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "millisecond", "amount": 1000}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract of 1000 milliseconds should equal subtracting 1 second",
    ),
    ExpressionTestCase(
        "millisecond_precision_1ms",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "millisecond", "amount": 1}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should decrement by exactly 1 millisecond",
    ),
    ExpressionTestCase(
        "day_7_equals_week",
        doc={"date": datetime(2000, 6, 8, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 7}},
        expected=datetime(2000, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract of 7 days should equal subtracting 1 week",
    ),
    ExpressionTestCase(
        "month_12_equals_year",
        doc={"date": datetime(2001, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 12}},
        expected=datetime(2000, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract of 12 months should equal subtracting 1 year",
    ),
    ExpressionTestCase(
        "month_3_equals_quarter",
        doc={"date": datetime(2000, 9, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 3}},
        expected=datetime(2000, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract of 3 months should equal subtracting 1 quarter",
    ),
]

# Property [Timestamp Start Date]: a Timestamp or DatetimeMS start date is accepted and returns
# a Date.
DATESUBTRACT_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_startDate_day",
        doc={"date": ts_from_args(2021, 1, 1, 12, 10, 5)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2020, 12, 31, 12, 10, 5, tzinfo=timezone.utc),
        msg="$dateSubtract should accept a Timestamp start date and return a Date",
    ),
    ExpressionTestCase(
        "timestamp_startDate_second",
        doc={"date": ts_from_args(2000, 1, 1, 12, 0, 1)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a Timestamp start date",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": TS_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": -1}},
        expected=datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        msg="$dateSubtract should accept an epoch Timestamp start date",
    ),
    ExpressionTestCase(
        "date_ms_epoch_sub_day",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a day from an epoch DatetimeMS start date",
    ),
    ExpressionTestCase(
        "ts_max_s32_sub_second",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 6, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_max_u32_sub_second",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2106, 2, 7, 6, 28, 14, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a max unsigned 32-bit Timestamp",
    ),
]

# Property [ObjectId Start Date]: an ObjectId start date uses its embedded timestamp and
# returns a Date.
DATESUBTRACT_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_startDate_year",
        doc={"date": oid_from_args(2023, 7, 15, 22, 32, 25)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2022, 7, 15, 22, 32, 25, tzinfo=timezone.utc),
        msg="$dateSubtract should accept an ObjectId start date and return a Date",
    ),
    ExpressionTestCase(
        "objectid_startDate_second",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 26)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2022, 7, 15, 22, 32, 25, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_startDate_millisecond",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 26)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "millisecond", "amount": 500}},
        expected=datetime(2022, 7, 15, 22, 32, 25, 500000, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract sub-second precision from an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": OID_EPOCH},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should accept an epoch ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_max_signed32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 6, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract a second from a max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "objectid_high_bit_pre_epoch",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1901, 12, 12, 20, 45, 52, tzinfo=timezone.utc),
        msg="$dateSubtract should handle an ObjectId with the high timestamp bit set",
    ),
]

DATESUBTRACT_DATE_SUCCESS_TESTS = (
    DATESUBTRACT_LEAP_YEAR_TESTS
    + DATESUBTRACT_CENTURY_TESTS
    + DATESUBTRACT_MONTH_CLAMP_TESTS
    + DATESUBTRACT_BOUNDARY_TESTS
    + DATESUBTRACT_HISTORICAL_TESTS
    + DATESUBTRACT_EPOCH_TESTS
    + DATESUBTRACT_DATE_LIMIT_TESTS
    + DATESUBTRACT_UNIT_EQUIVALENCE_TESTS
    + DATESUBTRACT_TIMESTAMP_TESTS
    + DATESUBTRACT_OBJECTID_TESTS
)

# Property [Overflow]: an amount that pushes the result beyond the representable date range
# is rejected.
DATESUBTRACT_OVERFLOW_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_positive_month_overflow",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 30_000_000_000}
        },
        error_code=DATEADD_INVALID_LARGE_VALUE_ERROR,
        msg="$dateSubtract should reject a month amount that underflows the date range",
    ),
]

DATESUBTRACT_DATE_TESTS: list[ExpressionTestCase] = (
    DATESUBTRACT_DATE_SUCCESS_TESTS + DATESUBTRACT_OVERFLOW_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATESUBTRACT_DATE_TESTS))
def test_dateSubtract_dates(collection, test_case: ExpressionTestCase):
    """Test $dateSubtract date edge cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
