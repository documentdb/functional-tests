"""Tests for $year calendar-year extraction across the calendar, leap years, and the year range."""

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
from documentdb_tests.framework.test_constants import DATE_EPOCH, DATE_YEAR_9999

# Property [Year Extraction]: $year returns the calendar year, so every instant from the first
# to the last moment of a year maps to that year regardless of month, day, or sub-second.
YEAR_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2024",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for a mid-2024 date",
    ),
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2000,
        msg="$year should return 2000 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=1999,
        msg="$year should return 1999 for the last second of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2099,
        msg="$year should return 2099 for a mid-2099 date",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": DATE_YEAR_9999},
        expression={"$year": "$date"},
        expected=9999,
        msg="$year should return 9999 for the maximum representable datetime",
    ),
    ExpressionTestCase(
        "first_moment_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for the first moment of 2024",
    ),
    ExpressionTestCase(
        "last_moment_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for the last second of 2024",
    ),
    ExpressionTestCase(
        "millisecond_before_year_end",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 one millisecond before the end of 2024",
    ),
    ExpressionTestCase(
        "millisecond_after_year_start",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 one millisecond after the start of 2024",
    ),
    ExpressionTestCase(
        "millisecond_mid_year",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for a mid-year instant with sub-second precision",
    ),
]

# Property [Leap Years]: the calendar year is correct on and around leap day.
YEAR_LEAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_year_feb_29_2024",
        doc={"date": datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2024,
        msg="$year should return 2024 for leap day 2024",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=2023,
        msg="$year should return 2023 for Feb 28 of the non-leap year 2023",
    ),
]

# Property [Pre-Epoch]: dates at and before the 1970 epoch return their correct calendar year.
YEAR_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch_1970",
        doc={"date": DATE_EPOCH},
        expression={"$year": "$date"},
        expected=1970,
        msg="$year should return 1970 for the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=1969,
        msg="$year should return 1969 for the last second before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=1969,
        msg="$year should return 1969 for the first moment of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=1960,
        msg="$year should return 1960 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=1900,
        msg="$year should return 1900 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1952_leap",
        doc={"date": datetime(1952, 2, 29, 6, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": "$date"},
        expected=1952,
        msg="$year should return 1952 for leap day of the pre-epoch leap year 1952",
    ),
]

# Property [Extended Range]: computed instants beyond the native datetime range resolve to the
# correct calendar year, including the millisecond before the epoch, BCE/year-zero dates, and
# years far past the datetime maximum of 9999.
YEAR_EXTENDED_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch_ms_zero",
        expression={"$year": {"$add": [DATE_EPOCH, 0]}},
        expected=1970,
        msg="$year should return 1970 at the epoch millisecond",
    ),
    ExpressionTestCase(
        "ms_negative_one",
        expression={"$year": {"$add": [DATE_EPOCH, -1]}},
        expected=1969,
        msg="$year should return 1969 one millisecond before the epoch",
    ),
    ExpressionTestCase(
        "far_future_year_10000",
        expression={"$year": {"$add": [DATE_EPOCH, 253_402_300_800_000]}},
        expected=10000,
        msg="$year should return 10000 for the first instant of year 10000",
    ),
    ExpressionTestCase(
        "far_past_year_0",
        expression={"$year": {"$subtract": [DATE_EPOCH, 62_167_219_200_000]}},
        expected=0,
        msg="$year should return 0 for the first instant of year 0",
    ),
    ExpressionTestCase(
        "deep_past_bce",
        expression={"$year": {"$subtract": [DATE_EPOCH, 3_217_862_400_000_000]}},
        expected=-100000,
        msg="$year should return a negative year for a deep BCE instant",
    ),
    ExpressionTestCase(
        "deep_future",
        expression={"$year": {"$add": [DATE_EPOCH, 3_093_527_980_800_000]}},
        expected=100000,
        msg="$year should return 100000 for a deep-future instant",
    ),
]

YEAR_CALENDAR_TESTS: list[ExpressionTestCase] = (
    YEAR_EXTRACTION_TESTS + YEAR_LEAP_TESTS + YEAR_PRE_EPOCH_TESTS + YEAR_EXTENDED_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(YEAR_CALENDAR_TESTS))
def test_year_calendar(collection, test_case: ExpressionTestCase):
    """Test $year extraction across the calendar, leap years, pre-epoch, and extended range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
