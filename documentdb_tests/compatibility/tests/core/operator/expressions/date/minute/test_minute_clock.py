"""Tests for $minute extraction across the hour, calendar boundaries, and year range."""

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

# Property [Minute Extraction]: $minute returns the minute component (0-59) of a UTC date.
MINUTE_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minute_0",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=0,
        msg="$minute should return 0 for the top of the hour",
    ),
    ExpressionTestCase(
        "minute_1",
        doc={"date": datetime(2024, 6, 15, 12, 1, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=1,
        msg="$minute should return 1 for one minute past the hour",
    ),
    ExpressionTestCase(
        "minute_15",
        doc={"date": datetime(2024, 6, 15, 12, 15, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=15,
        msg="$minute should return 15 at quarter past the hour",
    ),
    ExpressionTestCase(
        "minute_30",
        doc={"date": datetime(2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=30,
        msg="$minute should return 30 at half past the hour",
    ),
    ExpressionTestCase(
        "minute_45",
        doc={"date": datetime(2024, 6, 15, 12, 45, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=45,
        msg="$minute should return 45 at quarter to the hour",
    ),
    ExpressionTestCase(
        "minute_59",
        doc={"date": datetime(2024, 6, 15, 12, 59, 59, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=59,
        msg="$minute should return 59 for the last minute of the hour",
    ),
]

# Property [Calendar Boundaries]: year edges, leap-year Feb 29, and sub-second precision
# resolve to the correct minute.
MINUTE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_moment_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=0,
        msg="$minute should return 0 for the first moment of the year",
    ),
    ExpressionTestCase(
        "last_moment_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=59,
        msg="$minute should return 59 for the last moment of the year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29",
        doc={"date": datetime(2024, 2, 29, 15, 30, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=30,
        msg="$minute should return 30 for Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 15, 30, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=30,
        msg="$minute should return 30 for Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "millisecond_before_next_minute",
        doc={"date": datetime(2024, 6, 15, 12, 29, 59, 999000, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=29,
        msg="$minute should return 29 one millisecond before the next minute",
    ),
    ExpressionTestCase(
        "millisecond_after_minute_start",
        doc={"date": datetime(2024, 6, 15, 12, 30, 0, 1000, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=30,
        msg="$minute should return 30 one millisecond after the minute starts",
    ),
    ExpressionTestCase(
        "millisecond_mid_minute",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=30,
        msg="$minute should return 30 for a mid-minute instant with milliseconds",
    ),
    ExpressionTestCase(
        "millisecond_at_hour_boundary",
        doc={"date": datetime(2024, 6, 15, 12, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=59,
        msg="$minute should return 59 one millisecond before the next hour",
    ),
    ExpressionTestCase(
        "millisecond_after_hour_start",
        doc={"date": datetime(2024, 6, 15, 13, 0, 0, 1000, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=0,
        msg="$minute should return 0 one millisecond after the hour starts",
    ),
]

# Property [Year Range]: the minute component is correct across a wide span of years.
MINUTE_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 8, 45, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=45,
        msg="$minute should return 45 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$minute": "$date"},
        expected=0,
        msg="$minute should return 0 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=59,
        msg="$minute should return 59 for the last moment of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 14, 22, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=22,
        msg="$minute should return 22 for a date in the year 2099",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": DATE_YEAR_9999},
        expression={"$minute": "$date"},
        expected=59,
        msg="$minute should return 59 for the last representable year 9999",
    ),
]

# Property [Pre-Epoch]: negative-millisecond dates before 1970 resolve to the correct minute.
MINUTE_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 14, 37, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=37,
        msg="$minute should return 37 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=0,
        msg="$minute should return 0 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=59,
        msg="$minute should return 59 for the last moment before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=0,
        msg="$minute should return 0 for the first moment of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1952_leap",
        doc={"date": datetime(1952, 2, 29, 7, 22, 0, tzinfo=timezone.utc)},
        expression={"$minute": "$date"},
        expected=22,
        msg="$minute should return 22 for Feb 29 in the pre-epoch leap year 1952",
    ),
]

MINUTE_CLOCK_TESTS: list[ExpressionTestCase] = (
    MINUTE_EXTRACTION_TESTS + MINUTE_BOUNDARY_TESTS + MINUTE_YEAR_TESTS + MINUTE_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MINUTE_CLOCK_TESTS))
def test_minute_clock(collection, test_case: ExpressionTestCase):
    """Test $minute extraction across the hour, calendar boundaries, and year range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
