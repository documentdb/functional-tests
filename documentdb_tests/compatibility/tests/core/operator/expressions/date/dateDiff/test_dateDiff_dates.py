"""$dateDiff sign handling, unit boundary counting, quarter counting, and week counting."""

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
from documentdb_tests.framework.test_constants import DATE_YEAR_1, INT64_ZERO

# Property [Sign Handling]: the difference is positive when endDate follows startDate,
# negative when it precedes, and zero when they are equal.
DATEDIFF_SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_diff",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(152),
        msg="$dateDiff should return a positive difference when endDate follows startDate",
    ),
    ExpressionTestCase(
        "negative_diff",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(-152),
        msg="$dateDiff should return a negative difference when endDate precedes startDate",
    ),
    ExpressionTestCase(
        "zero_diff",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should return zero when startDate equals endDate",
    ),
    ExpressionTestCase(
        "negative_year",
        expression={
            "$dateDiff": {
                "startDate": datetime(2022, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "year",
            }
        },
        expected=Int64(-1),
        msg="$dateDiff should return a negative year difference",
    ),
    ExpressionTestCase(
        "negative_month",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 6, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(-5),
        msg="$dateDiff should return a negative month difference",
    ),
]

# Property [Boundary Counting]: the difference counts unit boundaries crossed, not elapsed
# whole units, so sub-unit remainders do not change the count.
DATEDIFF_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_exact",
        expression={
            "$dateDiff": {
                "startDate": datetime(2010, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2011, 1, 1, tzinfo=timezone.utc),
                "unit": "year",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one year boundary for an exact year",
    ),
    ExpressionTestCase(
        "year_18m_still_1",
        expression={
            "$dateDiff": {
                "startDate": datetime(2010, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2011, 6, 30, tzinfo=timezone.utc),
                "unit": "year",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one year boundary for eighteen months",
    ),
    ExpressionTestCase(
        "month_12",
        expression={
            "$dateDiff": {
                "startDate": datetime(2010, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2011, 1, 1, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(12),
        msg="$dateDiff should count twelve month boundaries for one year",
    ),
    ExpressionTestCase(
        "month_60d_is_1",
        expression={
            "$dateDiff": {
                "startDate": datetime(2010, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2010, 4, 30, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one month boundary within sixty days",
    ),
    ExpressionTestCase(
        "day_365",
        expression={
            "$dateDiff": {
                "startDate": datetime(2010, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2011, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(365),
        msg="$dateDiff should count 365 days across a non-leap year",
    ),
    ExpressionTestCase(
        "day_60",
        expression={
            "$dateDiff": {
                "startDate": datetime(2010, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2010, 4, 30, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(60),
        msg="$dateDiff should count sixty days from March to April",
    ),
    ExpressionTestCase(
        "day_546",
        expression={
            "$dateDiff": {
                "startDate": datetime(2010, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2011, 7, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(546),
        msg="$dateDiff should count 546 days across eighteen months",
    ),
    ExpressionTestCase(
        "day_no_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 23, 59, 59, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should count zero days within a single calendar day",
    ),
    ExpressionTestCase(
        "day_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 23, 59, 59, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 2, 0, 0, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one day when crossing midnight by seconds",
    ),
    ExpressionTestCase(
        "hour_no_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 0, 59, 59, tzinfo=timezone.utc),
                "unit": "hour",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should count zero hours within a single hour",
    ),
    ExpressionTestCase(
        "hour_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 59, 59, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 1, 0, 1, tzinfo=timezone.utc),
                "unit": "hour",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one hour when crossing the hour boundary by seconds",
    ),
    ExpressionTestCase(
        "minute_no_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 0, 0, 59, tzinfo=timezone.utc),
                "unit": "minute",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should count zero minutes within a single minute",
    ),
    ExpressionTestCase(
        "minute_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 59, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 0, 1, 1, tzinfo=timezone.utc),
                "unit": "minute",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one minute when crossing the minute boundary by seconds",
    ),
    ExpressionTestCase(
        "second_no_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 0, 0, 0, 999000, tzinfo=timezone.utc),
                "unit": "second",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should count zero seconds within a single second",
    ),
    ExpressionTestCase(
        "second_cross",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 0, 999000, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 0, 0, 1, 1000, tzinfo=timezone.utc),
                "unit": "second",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one second when crossing the second boundary by milliseconds",
    ),
    ExpressionTestCase(
        "millisecond_1",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
                "unit": "millisecond",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one millisecond",
    ),
    ExpressionTestCase(
        "large_year_range",
        expression={
            "$dateDiff": {
                "startDate": DATE_YEAR_1,
                "endDate": datetime(9999, 12, 31, tzinfo=timezone.utc),
                "unit": "year",
            }
        },
        expected=Int64(9998),
        msg="$dateDiff should count years across the full representable range",
    ),
    ExpressionTestCase(
        "large_day_range",
        expression={
            "$dateDiff": {
                "startDate": DATE_YEAR_1,
                "endDate": datetime(9999, 12, 31, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(3_652_058),
        msg="$dateDiff should count days across the full representable range",
    ),
]

# Property [Quarter Counting]: the difference counts quarter boundaries crossed.
DATEDIFF_QUARTER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "quarter_still_q1",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 31, tzinfo=timezone.utc),
                "unit": "quarter",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should count zero quarters within the first quarter",
    ),
    ExpressionTestCase(
        "quarter_cross_q2",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 4, 1, tzinfo=timezone.utc),
                "unit": "quarter",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one quarter when crossing into the second quarter",
    ),
    ExpressionTestCase(
        "quarter_3",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 12, 31, tzinfo=timezone.utc),
                "unit": "quarter",
            }
        },
        expected=Int64(3),
        msg="$dateDiff should count three quarters within a year",
    ),
    ExpressionTestCase(
        "quarter_4",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2022, 1, 1, tzinfo=timezone.utc),
                "unit": "quarter",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count four quarters across a year",
    ),
    ExpressionTestCase(
        "quarter_negative",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 4, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "quarter",
            }
        },
        expected=Int64(-1),
        msg="$dateDiff should return a negative quarter difference",
    ),
]

# Property [Week Counting]: the difference counts week boundaries crossed relative to
# startOfWeek, defaulting to Sunday.
DATEDIFF_WEEK_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "jan_default_sun",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should count January weeks from the default Sunday start",
    ),
    ExpressionTestCase(
        "jan_monday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count January weeks from a Monday start",
    ),
    ExpressionTestCase(
        "jan_friday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "fri",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count January weeks from a Friday start",
    ),
    ExpressionTestCase(
        "feb_default_sun",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 2, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 28, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count February weeks from the default Sunday start",
    ),
    ExpressionTestCase(
        "feb_monday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 2, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 28, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(3),
        msg="$dateDiff should count February weeks from a Monday start",
    ),
    ExpressionTestCase(
        "feb_friday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 2, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 28, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "fri",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count February weeks from a Friday start",
    ),
    ExpressionTestCase(
        "mar_default_sun",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 31, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count March weeks from the default Sunday start",
    ),
    ExpressionTestCase(
        "mar_monday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count March weeks from a Monday start",
    ),
    ExpressionTestCase(
        "mar_friday",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 3, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "fri",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should count March weeks from a Friday start",
    ),
    ExpressionTestCase(
        "cross_year_week",
        expression={
            "$dateDiff": {
                "startDate": datetime(2020, 12, 28, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 4, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one week across the year boundary",
    ),
    ExpressionTestCase(
        "cross_month_week",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 25, tzinfo=timezone.utc),
                "endDate": datetime(2021, 2, 8, tzinfo=timezone.utc),
                "unit": "week",
            }
        },
        expected=Int64(2),
        msg="$dateDiff should count two weeks across the month boundary",
    ),
]

DATEDIFF_DATE_TESTS = (
    DATEDIFF_SIGN_TESTS + DATEDIFF_BOUNDARY_TESTS + DATEDIFF_QUARTER_TESTS + DATEDIFF_WEEK_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_DATE_TESTS))
def test_dateDiff_dates(collection, test_case: ExpressionTestCase):
    """Test $dateDiff sign handling and unit boundary counting."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
