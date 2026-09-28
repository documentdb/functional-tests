"""Tests for $dateToParts named/Olson timezones, abbreviations, and DST."""

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

# Property [Named Zones]: an Olson name or abbreviation applies the zone offset, including DST.
DATETOPARTS_TZ_NAMED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_europe_london",
        doc={"timezone": "Europe/London"},
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
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the Europe/London Olson name",
    ),
    ExpressionTestCase(
        "tz_europe_london_bst",
        doc={"timezone": "Europe/London"},
        expression={
            "$dateToParts": {
                "date": datetime(2020, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2020,
            "month": 7,
            "day": 1,
            "hour": 13,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply the summer BST offset for Europe/London",
    ),
    ExpressionTestCase(
        "tz_asia_tokyo",
        doc={"timezone": "Asia/Tokyo"},
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
            "hour": 21,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the Asia/Tokyo Olson name",
    ),
    ExpressionTestCase(
        "tz_asia_kolkata",
        doc={"timezone": "Asia/Kolkata"},
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
            "hour": 17,
            "minute": 30,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply the Asia/Kolkata half-hour offset",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"timezone": "Pacific/Apia"},
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
            "hour": 2,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the Pacific/Apia Olson name",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        doc={"timezone": "EST"},
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
            "hour": 7,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept the EST three-letter abbreviation",
    ),
    ExpressionTestCase(
        "tz_dst_summer",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 7,
            "day": 1,
            "hour": 8,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply the summer DST offset",
    ),
    ExpressionTestCase(
        "tz_dst_winter",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected={
            "year": 2024,
            "month": 1,
            "day": 1,
            "hour": 7,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should apply the winter standard offset",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_TZ_NAMED_TESTS))
def test_dateToParts_timezone_names(collection, test_case: ExpressionTestCase):
    """Test $dateToParts named timezones."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
