"""Tests for $dateToParts unusual offsets, day/year boundary shifts, and ISO with timezone."""

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

# Property [Unusual Offsets]: an out-of-range but syntactically valid offset is accepted.
DATETOPARTS_TZ_UNUSUAL_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_over60_minutes_positive",
        doc={"timezone": "+05:70"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 1,
            "day": 1,
            "hour": 18,
            "minute": 10,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a positive offset with over 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_negative",
        doc={"timezone": "-05:70"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 1,
            "day": 1,
            "hour": 5,
            "minute": 50,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a negative offset with over 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over24_hours_positive",
        doc={"timezone": "+25:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 1,
            "day": 2,
            "hour": 13,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a positive offset with over 24 hours",
    ),
    ExpressionTestCase(
        "tz_over24_hours_negative",
        doc={"timezone": "-25:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2019,
            "month": 12,
            "day": 31,
            "hour": 11,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a negative offset with over 24 hours",
    ),
    ExpressionTestCase(
        "tz_max_valid_positive",
        doc={"timezone": "+99:99"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 1,
            "day": 5,
            "hour": 16,
            "minute": 39,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the max two-digit positive offset",
    ),
    ExpressionTestCase(
        "tz_max_valid_negative",
        doc={"timezone": "-99:99"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2019,
            "month": 12,
            "day": 28,
            "hour": 7,
            "minute": 21,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the max two-digit negative offset",
    ),
]

# Property [Day And Year Shifts]: an offset can move the extracted date across day and year
# boundaries.
DATETOPARTS_TZ_SHIFT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_year_cross_fwd",
        doc={"timezone": "+02:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2025,
            "month": 1,
            "day": 1,
            "hour": 1,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should cross forward over a year boundary",
    ),
    ExpressionTestCase(
        "tz_year_cross_bwd",
        doc={"timezone": "-05:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2023,
            "month": 12,
            "day": 31,
            "hour": 21,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should cross backward over a year boundary",
    ),
]

# Property [ISO With Timezone]: iso8601 and a timezone combine.
DATETOPARTS_ISO_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "iso_with_tz",
        doc={"timezone": "-05:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2023,
            "isoWeek": 52,
            "isoDayOfWeek": 7,
            "hour": 21,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should return ISO parts after applying a timezone",
    ),
]

DATETOPARTS_TZ_OFFSET_EDGE_TESTS: list[ExpressionTestCase] = (
    DATETOPARTS_TZ_UNUSUAL_OFFSET_TESTS + DATETOPARTS_TZ_SHIFT_TESTS + DATETOPARTS_ISO_TZ_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_TZ_OFFSET_EDGE_TESTS))
def test_dateToParts_timezone_offset_edge_cases(collection, test_case: ExpressionTestCase):
    """Test $dateToParts offset edge cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
