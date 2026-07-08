"""$dateAdd date edge cases: leap years, month clamping, boundaries, and non-date starts."""

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
    DATE_YEAR_1900,
    DATE_YEAR_9999,
    OID_EPOCH,
    OID_MAX_SIGNED32,
    OID_MIN_SIGNED32,
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Leap Year]: adding across February resolves leap-year day counts correctly.
DATEADD_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_year_feb29_add_year",
        doc={"date": datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2001, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Feb 29 to Feb 28 when adding a year into a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_add_day_to_feb28",
        doc={"date": datetime(2000, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should land on Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb28_add_day",
        doc={"date": datetime(1999, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1999, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should roll to Mar 1 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_feb29_add_month",
        doc={"date": datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 3, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add a month from Feb 29 to Mar 29",
    ),
    ExpressionTestCase(
        "leap_year_feb27_add_2days",
        doc={"date": datetime(2020, 2, 27, 14, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 2}},
        expected=datetime(2020, 2, 29, 14, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should land on Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb27_add_2days",
        doc={"date": datetime(2021, 2, 27, 14, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 2}},
        expected=datetime(2021, 3, 1, 14, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should roll to Mar 1 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_365_days",
        doc={"date": datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2020, 12, 31, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should not wrap the year when adding 365 days in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_365_days",
        doc={"date": datetime(2019, 1, 1, 15, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 365}},
        expected=datetime(2020, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should wrap to the next year when adding 365 days in a non-leap year",
    ),
]

# Property [Century Leap Year]: the divisible-by-100/400 leap rule is honored.
DATEADD_CENTURY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "century_non_leap_1900_feb28_add_day",
        doc={"date": datetime(1900, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1900, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should roll to Mar 1 in 1900, a non-leap century year",
    ),
    ExpressionTestCase(
        "century_leap_2000_feb28_add_day",
        doc={"date": datetime(2000, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should land on Feb 29 in 2000, a leap century year",
    ),
]

# Property [Month Clamping]: adding months or quarters clamps to the last valid day of the
# target month.
DATEADD_MONTH_CLAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "jan31_add_month_leap",
        doc={"date": datetime(2020, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 31 plus 1 month to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "jan31_add_month_non_leap",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 31 plus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "jan29_add_month_non_leap",
        doc={"date": datetime(2021, 1, 29, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 29 plus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "oct31_add_month",
        doc={"date": datetime(2020, 10, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 11, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Oct 31 plus 1 month to Nov 30",
    ),
    ExpressionTestCase(
        "mar31_add_month",
        doc={"date": datetime(2000, 3, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Mar 31 plus 1 month to Apr 30",
    ),
    ExpressionTestCase(
        "may31_add_month",
        doc={"date": datetime(2000, 5, 31, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2000, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp May 31 plus 1 month to Jun 30",
    ),
    ExpressionTestCase(
        "aug31_add_month",
        doc={"date": datetime(2020, 8, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 1}},
        expected=datetime(2020, 9, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Aug 31 plus 1 month to Sep 30",
    ),
    ExpressionTestCase(
        "dec31_add_year_no_adjustment",
        doc={"date": datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2021, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should not adjust Dec 31 when adding a year",
    ),
    ExpressionTestCase(
        "mar31_subtract_month_leap",
        doc={"date": datetime(2020, 3, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -1}},
        expected=datetime(2020, 2, 29, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Mar 31 minus 1 month to Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "mar31_subtract_month_non_leap",
        doc={"date": datetime(2021, 3, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -1}},
        expected=datetime(2021, 2, 28, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Mar 31 minus 1 month to Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "jan31_subtract_month_no_adjustment",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -1}},
        expected=datetime(2020, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should not adjust Jan 31 minus 1 month, landing on Dec 31",
    ),
    ExpressionTestCase(
        "jan31_add_quarter",
        doc={"date": datetime(2021, 1, 31, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "quarter", "amount": 1}},
        expected=datetime(2021, 4, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should clamp Jan 31 plus 1 quarter to Apr 30",
    ),
    ExpressionTestCase(
        "quarter_subtract",
        doc={"date": datetime(2021, 4, 30, 10, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "quarter", "amount": -1}},
        expected=datetime(2021, 1, 30, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should subtract 1 quarter",
    ),
    ExpressionTestCase(
        "large_positive_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 49}},
        expected=datetime(2025, 1, 31, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateAdd should clamp a large positive month amount to end-of-month",
    ),
    ExpressionTestCase(
        "large_negative_month",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, 10000, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -49}},
        expected=datetime(2016, 11, 30, 12, 10, 5, 10000, tzinfo=timezone.utc),
        msg="$dateAdd should clamp a large negative month amount to end-of-month",
    ),
]

# Property [Boundary Crossing]: adding across day, month, and year boundaries carries correctly.
DATEADD_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec31_add_day",
        doc={"date": datetime(2000, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2001, 1, 1, 23, 59, 59, tzinfo=timezone.utc),
        msg="$dateAdd should cross the year boundary from Dec 31 plus 1 day",
    ),
    ExpressionTestCase(
        "jan1_subtract_day",
        doc={"date": DATE_Y2K},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(1999, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should cross the year boundary from Jan 1 minus 1 day",
    ),
    ExpressionTestCase(
        "dec31_add_hour",
        doc={"date": datetime(2000, 12, 31, 23, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "hour", "amount": 2}},
        expected=datetime(2001, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should cross the year boundary from Dec 31 plus 2 hours",
    ),
]

# Property [Historical And Future]: distant past and future start dates are handled.
DATEADD_HISTORICAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "historical_date",
        doc={"date": datetime(1900, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 10}},
        expected=datetime(1910, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle a 1900 historical date",
    ),
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 100}},
        expected=datetime(1960, 4, 10, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle a pre-epoch 1960 date",
    ),
    ExpressionTestCase(
        "far_future",
        doc={"date": datetime(2100, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 100}},
        expected=datetime(2200, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle a far-future 2100 date",
    ),
    ExpressionTestCase(
        "large_year_amount",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1000}},
        expected=datetime(3000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle adding 1000 years",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": DATE_YEAR_1900},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(1901, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle 1900 plus 1 year",
    ),
    ExpressionTestCase(
        "distant_future_month",
        doc={"date": datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 6}},
        expected=datetime(2100, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should handle 2100 plus 6 months",
    ),
]

# Property [Epoch Crossing]: adding forward and backward across the Unix epoch is correct.
DATEADD_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch_add_day",
        doc={"date": DATE_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add a day to the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_add_day",
        doc={"date": datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=DATE_EPOCH,
        msg="$dateAdd should cross the epoch forward from 1969",
    ),
    ExpressionTestCase(
        "cross_epoch_back",
        doc={"date": DATE_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": -1}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should cross the epoch backward to 1969",
    ),
]

# Property [Date Limits]: adding near the maximum representable date is handled.
DATEADD_DATE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_max_date",
        doc={"date": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 1}},
        expected=datetime(9999, 12, 31, 23, 59, 59, 1000, tzinfo=timezone.utc),
        msg="$dateAdd should add 1 millisecond near the maximum date",
    ),
    ExpressionTestCase(
        "epoch_plus_large_ms",
        doc={"date": DATE_EPOCH},
        expression={
            "$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 253_402_300_799_999}
        },
        expected=DATE_YEAR_9999,
        msg="$dateAdd should reach the near-maximum date from the epoch with a large ms amount",
    ),
    ExpressionTestCase(
        "at_python_max_year",
        doc={"date": datetime(9999, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "hour", "amount": 23}},
        expected=datetime(9999, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 23 hours at year 9999",
    ),
]

# Property [Unit Equivalence]: a smaller unit times its multiple equals the larger unit.
DATEADD_UNIT_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "millisecond_1000_equals_second_1",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 1000}},
        expected=datetime(2000, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
        msg="$dateAdd of 1000 milliseconds should equal adding 1 second",
    ),
    ExpressionTestCase(
        "millisecond_precision_1ms",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 1}},
        expected=datetime(2000, 1, 1, 12, 0, 0, 1000, tzinfo=timezone.utc),
        msg="$dateAdd should increment by exactly 1 millisecond",
    ),
    ExpressionTestCase(
        "day_7_equals_week",
        doc={"date": datetime(2000, 6, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 7}},
        expected=datetime(2000, 6, 8, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd of 7 days should equal adding 1 week",
    ),
    ExpressionTestCase(
        "month_12_equals_year",
        doc={"date": datetime(2000, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 12}},
        expected=datetime(2001, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd of 12 months should equal adding 1 year",
    ),
    ExpressionTestCase(
        "month_3_equals_quarter",
        doc={"date": datetime(2000, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 3}},
        expected=datetime(2000, 9, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd of 3 months should equal adding 1 quarter",
    ),
]

# Property [Timestamp Start Date]: a Timestamp or DatetimeMS start date is accepted and returns
# a Date.
DATEADD_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timestamp_startDate_day",
        doc={"date": ts_from_args(2020, 12, 31, 12, 10, 5)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(2021, 1, 1, 12, 10, 5, tzinfo=timezone.utc),
        msg="$dateAdd should accept a Timestamp start date and return a Date",
    ),
    ExpressionTestCase(
        "timestamp_startDate_second",
        doc={"date": ts_from_args(2000, 1, 1, 12, 0, 0)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2000, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a Timestamp start date",
    ),
    ExpressionTestCase(
        "timestamp_epoch",
        doc={"date": TS_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        msg="$dateAdd should accept an epoch Timestamp start date",
    ),
    ExpressionTestCase(
        "date_ms_epoch_add_day",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add a day to an epoch DatetimeMS start date",
    ),
    ExpressionTestCase(
        "ts_max_s32_add_second",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 8, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a max signed 32-bit Timestamp",
    ),
    ExpressionTestCase(
        "ts_max_u32_add_second",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2106, 2, 7, 6, 28, 16, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a max unsigned 32-bit Timestamp",
    ),
]

# Property [ObjectId Start Date]: an ObjectId start date uses its embedded timestamp and
# returns a Date.
DATEADD_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_startDate_day",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 25)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2023, 7, 15, 22, 32, 25, tzinfo=timezone.utc),
        msg="$dateAdd should accept an ObjectId start date and return a Date",
    ),
    ExpressionTestCase(
        "objectid_startDate_second",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 25)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2022, 7, 15, 22, 32, 26, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_startDate_millisecond",
        doc={"date": oid_from_args(2022, 7, 15, 22, 32, 25)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 500}},
        expected=datetime(2022, 7, 15, 22, 32, 25, 500000, tzinfo=timezone.utc),
        msg="$dateAdd should add sub-second precision to an ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_epoch",
        doc={"date": OID_EPOCH},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept an epoch ObjectId start date",
    ),
    ExpressionTestCase(
        "objectid_max_signed32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 1}},
        expected=datetime(2038, 1, 19, 3, 14, 8, tzinfo=timezone.utc),
        msg="$dateAdd should add a second to a max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "objectid_high_bit_pre_epoch",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=datetime(1901, 12, 14, 20, 45, 52, tzinfo=timezone.utc),
        msg="$dateAdd should handle an ObjectId with the high timestamp bit set",
    ),
]

DATEADD_DATE_SUCCESS_TESTS = (
    DATEADD_LEAP_YEAR_TESTS
    + DATEADD_CENTURY_TESTS
    + DATEADD_MONTH_CLAMP_TESTS
    + DATEADD_BOUNDARY_TESTS
    + DATEADD_HISTORICAL_TESTS
    + DATEADD_EPOCH_TESTS
    + DATEADD_DATE_LIMIT_TESTS
    + DATEADD_UNIT_EQUIVALENCE_TESTS
    + DATEADD_TIMESTAMP_TESTS
    + DATEADD_OBJECTID_TESTS
)

# Property [Overflow]: an amount that pushes the result beyond the representable date range
# is rejected.
DATEADD_OVERFLOW_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_negative_month_overflow",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -30_000_000_000}},
        error_code=DATEADD_INVALID_LARGE_VALUE_ERROR,
        msg="$dateAdd should reject a month amount that overflows the representable date range",
    ),
]

DATEADD_DATE_TESTS: list[ExpressionTestCase] = (
    DATEADD_DATE_SUCCESS_TESTS + DATEADD_OVERFLOW_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_DATE_TESTS))
def test_dateAdd_dates(collection, test_case: ExpressionTestCase):
    """Test $dateAdd date edge cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
