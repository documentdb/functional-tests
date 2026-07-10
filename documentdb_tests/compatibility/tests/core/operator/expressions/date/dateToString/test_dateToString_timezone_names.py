"""Tests for $dateToString with named and abbreviated timezones, including DST."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Named Timezones]: named and abbreviated timezones apply the correct offset, including
# DST rules.
DATETOSTRING_NAMED_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_gmt",
        doc={"timezone": "GMT"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y-%m-%d",
                "timezone": "$timezone",
            }
        },
        expected="2024-06-15",
        msg="$dateToString should accept the GMT timezone",
    ),
    ExpressionTestCase(
        "tz_utc",
        doc={"timezone": "UTC"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y-%m-%d",
                "timezone": "$timezone",
            }
        },
        expected="2024-06-15",
        msg="$dateToString should accept the UTC timezone",
    ),
    ExpressionTestCase(
        "tz_europe_london",
        doc={"timezone": "Europe/London"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="12:00",
        msg="$dateToString should apply the winter offset for Europe/London",
    ),
    ExpressionTestCase(
        "tz_europe_london_bst",
        doc={"timezone": "Europe/London"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="13:00",
        msg="$dateToString should apply the BST summer offset for Europe/London",
    ),
    ExpressionTestCase(
        "tz_asia_tokyo",
        doc={"timezone": "Asia/Tokyo"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="21:00",
        msg="$dateToString should apply the Asia/Tokyo offset",
    ),
    ExpressionTestCase(
        "tz_asia_kolkata",
        doc={"timezone": "Asia/Kolkata"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="17:30",
        msg="$dateToString should apply the Asia/Kolkata half-hour offset",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"timezone": "Pacific/Apia"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%Y-%m-%d %H:%M",
                "timezone": "$timezone",
            }
        },
        expected="2020-01-02 02:00",
        msg="$dateToString should apply the Pacific/Apia offset",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        doc={"timezone": "EST"},
        expression={
            "$dateToString": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M",
                "timezone": "$timezone",
            }
        },
        expected="07:00",
        msg="$dateToString should accept the EST three-letter abbreviation",
    ),
    ExpressionTestCase(
        "tz_dst_summer",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M%z",
                "timezone": "$timezone",
            }
        },
        expected="08:00-0400",
        msg="$dateToString should apply the summer DST offset for America/New_York",
    ),
    ExpressionTestCase(
        "tz_dst_winter",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "format": "%H:%M%z",
                "timezone": "$timezone",
            }
        },
        expected="07:00-0500",
        msg="$dateToString should apply the winter standard offset for America/New_York",
    ),
    ExpressionTestCase(
        "tz_ny_time",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateToString": {
                "date": datetime(2014, 1, 1, 8, 15, 39, 736000, tzinfo=timezone.utc),
                "format": "%H:%M:%S:%L%z",
                "timezone": "$timezone",
            }
        },
        expected="03:15:39:736-0500",
        msg="$dateToString should apply America/New_York to a full time format",
    ),
    ExpressionTestCase(
        "tz_Z_ny",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateToString": {
                "date": datetime(2014, 1, 1, 8, 15, 39, 736000, tzinfo=timezone.utc),
                "format": "%Z",
                "timezone": "$timezone",
            }
        },
        expected="-300",
        msg="$dateToString should format %Z as offset minutes for America/New_York",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_NAMED_TZ_TESTS))
def test_dateToString_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $dateToString with named timezones."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
