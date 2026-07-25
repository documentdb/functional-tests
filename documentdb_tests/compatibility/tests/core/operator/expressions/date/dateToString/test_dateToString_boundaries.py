"""Tests for $dateToString formatting at calendar, range, and year-limit boundaries."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import DATETOSTRING_YEAR_RANGE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DATE_LEAP_FEB29,
    DATE_MS_BEFORE_EPOCH,
    DATE_MS_EPOCH,
    DATE_MS_MAX,
    DATE_MS_MIN,
    DATE_MS_YEAR_10000,
    DATE_YEAR_1900,
)

# Property [Leap Year]: February 29 and day-of-year formatting reflect leap and non-leap years.
DATETOSTRING_LEAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_feb29",
        doc={"date": datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%Y-%m-%d",
            }
        },
        expected="2024-02-29",
        msg="$dateToString should format February 29 in a leap year",
    ),
    ExpressionTestCase(
        "leap_j_feb29",
        doc={"date": datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%j",
            }
        },
        expected="060",
        msg="$dateToString should format the day of year for February 29",
    ),
    ExpressionTestCase(
        "leap_j_dec31",
        doc={"date": datetime(2024, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%j",
            }
        },
        expected="366",
        msg="$dateToString should format day 366 for December 31 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_j_dec31",
        doc={"date": datetime(2023, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%j",
            }
        },
        expected="365",
        msg="$dateToString should format day 365 for December 31 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_feb29_2000",
        doc={"date": DATE_LEAP_FEB29},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%Y-%m-%d",
            }
        },
        expected="2000-02-29",
        msg="$dateToString should format February 29 in the leap century year 2000",
    ),
    ExpressionTestCase(
        "non_leap_century_1900",
        doc={"date": datetime(1900, 2, 28, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%Y-%m-%d",
            }
        },
        expected="1900-02-28",
        msg="$dateToString should format February 28 in the non-leap century year 1900",
    ),
]

# Property [Date Range]: dates across the epoch and into the distant past and future are formatted.
DATETOSTRING_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"date": DATE_EPOCH},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1970-01-01",
        msg="$dateToString should format the Unix epoch",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"date": datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%Y-%m-%d",
            }
        },
        expected="1969-12-31",
        msg="$dateToString should format a pre-epoch date",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": DATE_YEAR_1900},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1900-01-01",
        msg="$dateToString should format a distant past date",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"date": datetime(2100, 12, 31, 0, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "format": "%Y-%m-%d",
            }
        },
        expected="2100-12-31",
        msg="$dateToString should format a distant future date",
    ),
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1970-01-01",
        msg="$dateToString should format a DatetimeMS at the epoch",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1969-12-31",
        msg="$dateToString should format a DatetimeMS just before the epoch",
    ),
]

# Property [Year Range Error]: a date whose year falls outside the formattable range is rejected.
DATETOSTRING_YEAR_RANGE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_range_year_10000",
        doc={"date": DATE_MS_YEAR_10000},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        error_code=DATETOSTRING_YEAR_RANGE_ERROR,
        msg="$dateToString should reject a date in year 10000",
    ),
    ExpressionTestCase(
        "year_range_ms_max",
        doc={"date": DATE_MS_MAX},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        error_code=DATETOSTRING_YEAR_RANGE_ERROR,
        msg="$dateToString should reject the maximum DatetimeMS value",
    ),
    ExpressionTestCase(
        "year_range_ms_min",
        doc={"date": DATE_MS_MIN},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        error_code=DATETOSTRING_YEAR_RANGE_ERROR,
        msg="$dateToString should reject the minimum DatetimeMS value",
    ),
]

DATETOSTRING_BOUNDARY_TESTS: list[ExpressionTestCase] = (
    DATETOSTRING_LEAP_TESTS + DATETOSTRING_RANGE_TESTS + DATETOSTRING_YEAR_RANGE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_BOUNDARY_TESTS))
def test_dateToString_boundaries(collection, test_case: ExpressionTestCase):
    """Test $dateToString at calendar and range boundaries."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
