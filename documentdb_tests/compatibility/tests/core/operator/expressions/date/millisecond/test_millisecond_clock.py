"""Tests for $millisecond extraction across the second, calendar boundaries, and year range."""

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
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_YEAR_9999,
)

# Property [Millisecond Extraction]: $millisecond returns the millisecond component (0-999)
# of a UTC date.
MILLISECOND_EXTRACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ms_0",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 0, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 at the top of the second",
    ),
    ExpressionTestCase(
        "ms_1",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 1000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=1,
        msg="$millisecond should return 1 for one millisecond past the second",
    ),
    ExpressionTestCase(
        "ms_2",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 2000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=2,
        msg="$millisecond should return 2 for two milliseconds past the second",
    ),
    ExpressionTestCase(
        "ms_10",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 10000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=10,
        msg="$millisecond should return a two-digit millisecond value",
    ),
    ExpressionTestCase(
        "ms_99",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 99000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=99,
        msg="$millisecond should return the last two-digit millisecond value",
    ),
    ExpressionTestCase(
        "ms_100",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 100000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=100,
        msg="$millisecond should return the first three-digit millisecond value",
    ),
    ExpressionTestCase(
        "ms_250",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 250000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=250,
        msg="$millisecond should return 250 for a quarter-second instant",
    ),
    ExpressionTestCase(
        "ms_498",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 498000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=498,
        msg="$millisecond should return 498 just below the half-second",
    ),
    ExpressionTestCase(
        "ms_499",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 499000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=499,
        msg="$millisecond should return 499 one millisecond below the half-second",
    ),
    ExpressionTestCase(
        "ms_500",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 500000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=500,
        msg="$millisecond should return 500 at the half-second",
    ),
    ExpressionTestCase(
        "ms_501",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 501000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=501,
        msg="$millisecond should return 501 one millisecond above the half-second",
    ),
    ExpressionTestCase(
        "ms_750",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 750000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=750,
        msg="$millisecond should return 750 for a three-quarter-second instant",
    ),
    ExpressionTestCase(
        "ms_998",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 998000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=998,
        msg="$millisecond should return 998 one millisecond below the maximum",
    ),
    ExpressionTestCase(
        "ms_999",
        doc={"date": datetime(2024, 6, 15, 12, 30, 30, 999000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=999,
        msg="$millisecond should return the maximum millisecond value 999",
    ),
]

# Property [Calendar Boundaries]: year edges, leap-year Feb 29, and second and minute boundaries
# resolve to the correct millisecond.
MILLISECOND_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_moment_of_year",
        doc={"date": datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the first moment of the year",
    ),
    ExpressionTestCase(
        "last_ms_of_year",
        doc={"date": datetime(2024, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=999,
        msg="$millisecond should return 999 for the last millisecond of the year",
    ),
    ExpressionTestCase(
        "leap_year_feb_29",
        doc={"date": datetime(2024, 2, 29, 15, 30, 42, 123000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=123,
        msg="$millisecond should return the sub-second value for Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_year_feb_28",
        doc={"date": datetime(2023, 2, 28, 15, 30, 42, 123000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=123,
        msg="$millisecond should return the sub-second value for Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "ms_at_second_boundary",
        doc={"date": datetime(2024, 6, 15, 12, 30, 59, 999000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=999,
        msg="$millisecond should return 999 one millisecond before the next second",
    ),
    ExpressionTestCase(
        "ms_after_second_start",
        doc={"date": datetime(2024, 6, 15, 12, 31, 0, 1000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=1,
        msg="$millisecond should return 1 one millisecond after the minute starts",
    ),
    ExpressionTestCase(
        "ms_at_midnight",
        doc={"date": datetime(2024, 6, 15, 0, 0, 0, 500000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=500,
        msg="$millisecond should return 500 for a mid-second instant at midnight",
    ),
]

# Property [Year Range]: the millisecond component is correct across a wide span of years.
MILLISECOND_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_2000",
        doc={"date": datetime(2000, 1, 1, 8, 45, 33, 456000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=456,
        msg="$millisecond should return 456 for a date in the year 2000",
    ),
    ExpressionTestCase(
        "year_1970_epoch",
        doc={"date": DATE_EPOCH},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the Unix epoch",
    ),
    ExpressionTestCase(
        "year_1999",
        doc={"date": datetime(1999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=999,
        msg="$millisecond should return 999 for the last moment of 1999",
    ),
    ExpressionTestCase(
        "year_2099",
        doc={"date": datetime(2099, 7, 15, 14, 22, 11, 789000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=789,
        msg="$millisecond should return 789 for a date in the year 2099",
    ),
    ExpressionTestCase(
        "year_9999",
        doc={"date": DATE_YEAR_9999},
        expression={"$millisecond": "$date"},
        expected=999,
        msg="$millisecond should return 999 for the last representable year 9999",
    ),
]

# Property [Pre-Epoch]: negative-millisecond dates before 1970 resolve to the correct
# millisecond.
MILLISECOND_PRE_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_1960",
        doc={"date": datetime(1960, 3, 15, 14, 37, 22, 333000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=333,
        msg="$millisecond should return 333 for a pre-epoch date in 1960",
    ),
    ExpressionTestCase(
        "pre_epoch_1900",
        doc={"date": datetime(1900, 7, 4, 0, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for a pre-epoch date in 1900",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_dec",
        doc={"date": DATE_BEFORE_EPOCH},
        expression={"$millisecond": "$date"},
        expected=999,
        msg="$millisecond should return 999 for the last millisecond before the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch_1969_jan",
        doc={"date": datetime(1969, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=0,
        msg="$millisecond should return 0 for the first moment of 1969",
    ),
    ExpressionTestCase(
        "pre_epoch_1952_leap",
        doc={"date": datetime(1952, 2, 29, 7, 22, 48, 567000, tzinfo=timezone.utc)},
        expression={"$millisecond": "$date"},
        expected=567,
        msg="$millisecond should return 567 for Feb 29 in the pre-epoch leap year 1952",
    ),
]

MILLISECOND_CLOCK_TESTS: list[ExpressionTestCase] = (
    MILLISECOND_EXTRACTION_TESTS
    + MILLISECOND_BOUNDARY_TESTS
    + MILLISECOND_YEAR_TESTS
    + MILLISECOND_PRE_EPOCH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MILLISECOND_CLOCK_TESTS))
def test_millisecond_clock(collection, test_case: ExpressionTestCase):
    """Test $millisecond extraction across the second, calendar boundaries, and year range."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
