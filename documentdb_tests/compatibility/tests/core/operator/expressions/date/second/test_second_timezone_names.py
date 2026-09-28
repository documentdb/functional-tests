"""Tests for $second named-timezone application, including DST and fractional-offset zones."""

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
# second is unchanged across whole-hour, fractional-offset, and DST-transition zones.
SECOND_OLSON_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_dt_utc",
        expression={
            "$second": {
                "date": datetime(2024, 7, 15, 12, 25, 37, tzinfo=timezone.utc),
                "timezone": "UTC",
            }
        },
        expected=37,
        msg="$second should return 37 for UTC",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny",
        expression={
            "$second": {
                "date": datetime(2024, 7, 15, 12, 25, 37, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=37,
        msg="$second should leave the second at 37 for America/New_York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_tokyo",
        expression={
            "$second": {
                "date": datetime(2024, 7, 15, 12, 25, 37, tzinfo=timezone.utc),
                "timezone": "Asia/Tokyo",
            }
        },
        expected=37,
        msg="$second should leave the second at 37 for Asia/Tokyo",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kolkata",
        expression={
            "$second": {
                "date": datetime(2024, 3, 31, 20, 0, 37, tzinfo=timezone.utc),
                "timezone": "Asia/Kolkata",
            }
        },
        expected=37,
        msg="$second should leave the second at 37 for Asia/Kolkata (+05:30)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_kathmandu",
        expression={
            "$second": {
                "date": datetime(2024, 8, 31, 23, 0, 37, tzinfo=timezone.utc),
                "timezone": "Asia/Kathmandu",
            }
        },
        expected=37,
        msg="$second should leave the second at 37 for Asia/Kathmandu (+05:45)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_spring",
        expression={
            "$second": {
                "date": datetime(2024, 3, 10, 7, 17, 53, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=53,
        msg="$second should leave the second at 53 across the spring DST transition in New York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_ny_dst_fall",
        expression={
            "$second": {
                "date": datetime(2024, 11, 3, 6, 42, 8, tzinfo=timezone.utc),
                "timezone": "America/New_York",
            }
        },
        expected=8,
        msg="$second should leave the second at 8 across the fall DST transition in New York",
    ),
    ExpressionTestCase(
        "tz_olson_dt_london_bst",
        expression={
            "$second": {
                "date": datetime(2024, 7, 15, 12, 0, 37, tzinfo=timezone.utc),
                "timezone": "Europe/London",
            }
        },
        expected=37,
        msg="$second should leave the second at 37 for Europe/London in summer (BST +1)",
    ),
    ExpressionTestCase(
        "tz_olson_dt_pacific_apia",
        expression={
            "$second": {
                "date": datetime(2024, 7, 15, 12, 0, 37, tzinfo=timezone.utc),
                "timezone": "Pacific/Apia",
            }
        },
        expected=37,
        msg="$second should leave the second at 37 for Pacific/Apia",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        expression={
            "$second": {
                "date": datetime(2024, 7, 15, 12, 0, 37, tzinfo=timezone.utc),
                "timezone": "EST",
            }
        },
        expected=37,
        msg="$second should accept the EST three-letter abbreviation",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SECOND_OLSON_DATETIME_TESTS))
def test_second_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $second named-timezone application across zones, DST, and fractional offsets."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
