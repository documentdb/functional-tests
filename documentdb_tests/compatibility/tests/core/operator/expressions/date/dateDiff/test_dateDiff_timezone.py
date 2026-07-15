"""$dateDiff timezone handling: offsets, DST, startOfWeek values, and unit gating."""

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
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Valid Timezone]: a valid Olson id or syntactically valid UTC offset is accepted,
# including numerically out-of-range but well-formed offsets.
DATEDIFF_TIMEZONE_VALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": tz,
            }
        },
        expected=Int64(152),
        msg=f"$dateDiff should accept the {tz} timezone",
    )
    for tid, tz in [
        ("utc", "UTC"),
        ("gmt", "GMT"),
        ("olson_ny", "America/New_York"),
        ("asia_kolkata", "Asia/Kolkata"),
        ("pacific_apia", "Pacific/Apia"),
        ("offset_colon", "+05:30"),
        ("offset_neg", "-05:00"),
        ("offset_no_colon", "+0530"),
        ("offset_short", "+03"),
        ("offset_zero", "+00:00"),
        ("offset_45min", "+05:45"),
        ("offset_max_east", "+14:00"),
        ("offset_max_west", "-11:00"),
        ("offset_half_hour_west", "-02:30"),
        ("offset_over60_minutes_positive", "+05:70"),
        ("offset_over60_minutes_negative", "-05:70"),
        ("offset_over24_hours_positive", "+25:00"),
        ("offset_over24_hours_negative", "-25:00"),
        ("offset_max_valid_positive", "+99:99"),
        ("offset_max_valid_negative", "-99:99"),
    ]
]

# Property [Timezone Boundary Effect]: the timezone shifts the local wall clock, changing
# which unit boundaries are crossed.
DATEDIFF_TIMEZONE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_plus14_year",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 12, 31, 11, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2022, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
                "unit": "year",
                "timezone": "+14:00",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should not cross the year boundary in a +14:00 timezone",
    ),
    ExpressionTestCase(
        "tz_minus11_day",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": "-11:00",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should cross the day boundary in a -11:00 timezone",
    ),
    ExpressionTestCase(
        "tz_hour_only_day",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": "+03",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should cross the day boundary in an hour-only offset timezone",
    ),
    ExpressionTestCase(
        "tz_year_boundary",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2022, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
                "unit": "year",
                "timezone": "+02:00",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should not cross the year boundary when the timezone shifts both dates "
        "into the same year",
    ),
    ExpressionTestCase(
        "tz_day_boundary",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 23, 30, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 2, 0, 30, 0, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": "+05:30",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should not cross the day boundary when the timezone shifts both dates "
        "into the same day",
    ),
]

# Property [DST Behavior]: day and larger units track wall-clock time across DST, while
# sub-day units count absolute elapsed time.
DATEDIFF_TIMEZONE_DST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dst_spring_hour",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 14, 6, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 14, 8, 0, 0, tzinfo=timezone.utc),
                "unit": "hour",
                "timezone": "America/New_York",
            }
        },
        expected=Int64(2),
        msg="$dateDiff should count absolute hours across spring-forward",
    ),
    ExpressionTestCase(
        "dst_fall_hour",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 11, 7, 5, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 11, 7, 7, 0, 0, tzinfo=timezone.utc),
                "unit": "hour",
                "timezone": "America/New_York",
            }
        },
        expected=Int64(2),
        msg="$dateDiff should count absolute hours across fall-back",
    ),
    ExpressionTestCase(
        "dst_day_unaffected",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 13, 12, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 15, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": "America/New_York",
            }
        },
        expected=Int64(2),
        msg="$dateDiff should count two days across a DST transition",
    ),
    ExpressionTestCase(
        "dst_spring_minute_no_adjust",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 14, 6, 59, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 14, 7, 0, 0, tzinfo=timezone.utc),
                "unit": "minute",
                "timezone": "America/New_York",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should not DST-adjust a minute count",
    ),
    ExpressionTestCase(
        "dst_spring_second_no_adjust",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 14, 6, 59, 59, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 14, 7, 0, 0, tzinfo=timezone.utc),
                "unit": "second",
                "timezone": "America/New_York",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should not DST-adjust a second count",
    ),
]

# Property [StartOfWeek Value]: startOfWeek accepts full and abbreviated day names
# case-insensitively.
DATEDIFF_STARTOFWEEK_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"sow_{tid}",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": sow,
            }
        },
        expected=Int64(4),
        msg=f"$dateDiff should accept the {sow} startOfWeek value",
    )
    for tid, sow in [
        ("mixed_case_Monday", "Monday"),
        ("uppercase_MONDAY", "MONDAY"),
        ("lowercase_monday", "monday"),
        ("abbrev_mon", "mon"),
        ("abbrev_MON", "MON"),
        ("mixed_case_Friday", "Friday"),
        ("uppercase_FRIDAY", "FRIDAY"),
        ("abbrev_FRI", "FRI"),
    ]
]

# Property [Null Timezone]: a null timezone returns null.
DATEDIFF_TIMEZONE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_null",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": None,
            }
        },
        expected=None,
        msg="$dateDiff should return null when the timezone is null",
    ),
]

# Property [StartOfWeek Unit Gating]: startOfWeek is only consulted for the week unit, so with
# any other unit it is ignored and not even validated.
DATEDIFF_STARTOFWEEK_GATING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_ignored_day_unit",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 31, tzinfo=timezone.utc),
                "unit": "day",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(30),
        msg="$dateDiff should ignore startOfWeek for a non-week unit",
    ),
    ExpressionTestCase(
        "sow_invalid_ignored_day_unit",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 31, tzinfo=timezone.utc),
                "unit": "day",
                "startOfWeek": "notaday",
            }
        },
        expected=Int64(30),
        msg="$dateDiff should not validate startOfWeek for a non-week unit",
    ),
]

DATEDIFF_TIMEZONE_TESTS: list[ExpressionTestCase] = (
    DATEDIFF_TIMEZONE_VALID_TESTS
    + DATEDIFF_TIMEZONE_BOUNDARY_TESTS
    + DATEDIFF_TIMEZONE_DST_TESTS
    + DATEDIFF_STARTOFWEEK_VALUE_TESTS
    + DATEDIFF_TIMEZONE_NULL_TESTS
    + DATEDIFF_STARTOFWEEK_GATING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_TIMEZONE_TESTS))
def test_dateDiff_timezone(collection, test_case: ExpressionTestCase):
    """Test $dateDiff applies timezone and startOfWeek to the local wall clock."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
