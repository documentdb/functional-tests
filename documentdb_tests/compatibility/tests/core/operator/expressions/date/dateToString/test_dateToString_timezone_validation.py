"""Tests for $dateToString null and invalid timezone handling."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import INVALID_TIMEZONE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Timezone]: a null timezone yields null.
DATETOSTRING_NULL_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_null",
        doc={"timezone": None},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        expected=None,
        msg="$dateToString should return null for a null timezone",
    ),
]

# Property [Invalid Timezone]: an unrecognized or malformed timezone string is rejected.
DATETOSTRING_INVALID_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_invalid_str",
        doc={"timezone": "NotATimezone"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToString should reject an unrecognized timezone string",
    ),
    ExpressionTestCase(
        "tz_empty",
        doc={"timezone": ""},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToString should reject an empty timezone string",
    ),
    ExpressionTestCase(
        "tz_nonexistent_olson",
        doc={"timezone": "America/Nowhere"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToString should reject a non-existent Olson timezone",
    ),
    ExpressionTestCase(
        "tz_3digit_hours_invalid",
        doc={"timezone": "+100:00"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToString should reject a three-digit hour offset",
    ),
    ExpressionTestCase(
        "tz_olson_wrong_case_lowercase",
        doc={"timezone": "america/new_york"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToString should reject an all-lowercase Olson name",
    ),
    ExpressionTestCase(
        "tz_olson_wrong_case_uppercase",
        doc={"timezone": "AMERICA/NEW_YORK"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToString should reject an all-uppercase Olson name",
    ),
]

DATETOSTRING_TZ_VALIDATION_TESTS: list[ExpressionTestCase] = (
    DATETOSTRING_NULL_TZ_TESTS + DATETOSTRING_INVALID_TZ_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_TZ_VALIDATION_TESTS))
def test_dateToString_timezone_validation(collection, test_case: ExpressionTestCase):
    """Test $dateToString null and invalid timezones."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
