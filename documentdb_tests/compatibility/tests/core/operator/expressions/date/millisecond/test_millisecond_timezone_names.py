"""Tests for $millisecond named-timezone application, including DST and fractional-offset zones."""

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

# Property [Named Zones]: a named zone or abbreviation shifts the instant for parsing, but the
# millisecond is unchanged across whole-hour, fractional-offset, and DST-transition zones.
MILLISECOND_OLSON_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_dt_utc",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 25, 37, 456000, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=456,
        msg="$millisecond should return 456 for UTC",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 25, 37, 456000, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 25, 37, 456000, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata",
        expression={
            "$millisecond": {
                "date": datetime(2024, 3, 31, 20, 0, 37, 456000, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu",
        expression={
            "$millisecond": {
                "date": datetime(2024, 8, 31, 23, 0, 37, 456000, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_spring",
        expression={
            "$millisecond": {
                "date": datetime(2024, 3, 10, 7, 17, 53, 789000, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=789,
        msg="$millisecond should leave the millisecond at 789 across the spring DST transition",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for Europe/London in summer (BST +1)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_pacific_apia",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=456,
        msg="$millisecond should leave the millisecond at 456 for Pacific/Apia",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$millisecond": {
                "date": datetime(2024, 7, 15, 12, 0, 0, 456000, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=456,
        msg="$millisecond should accept the EST three-letter abbreviation",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MILLISECOND_OLSON_DATETIME_TESTS))
def test_millisecond_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $millisecond named-timezone application across zones, DST, and fractional offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
