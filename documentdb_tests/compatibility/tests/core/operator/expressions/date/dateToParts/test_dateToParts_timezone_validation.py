"""Tests for $dateToParts null, missing, invalid, and non-string timezone validation."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    INVALID_TIMEZONE_ERROR,
    INVALID_TIMEZONE_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null and Missing Timezone]: a null or missing timezone yields null.
DATETOPARTS_TZ_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_null",
        doc={"timezone": None},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        expected=None,
        msg="$dateToParts should return null for a null timezone",
    ),
    ExpressionTestCase(
        "missing_timezone_ref",
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "timezone": MISSING,
            }
        },
        expected=None,
        msg="$dateToParts should return null when the timezone references a missing field",
    ),
    ExpressionTestCase(
        "missing_timezone_from_field",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date", "timezone": "$tz"}},
        expected=None,
        msg="$dateToParts should return null when the timezone field reference is missing",
    ),
]

# Property [Invalid Timezone String]: an unrecognized timezone string is rejected.
DATETOPARTS_TZ_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_3digit_hours",
        doc={"timezone": "+100:00"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToParts should reject a three-digit hour offset",
    ),
    ExpressionTestCase(
        "tz_olson_lowercase",
        doc={"timezone": "america/new_york"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToParts should reject an all-lowercase Olson name",
    ),
    ExpressionTestCase(
        "tz_olson_uppercase",
        doc={"timezone": "AMERICA/NEW_YORK"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToParts should reject an all-uppercase Olson name",
    ),
    ExpressionTestCase(
        "tz_invalid_str",
        doc={"timezone": "NotATimezone"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToParts should reject an arbitrary timezone string",
    ),
    ExpressionTestCase(
        "tz_empty",
        doc={"timezone": ""},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToParts should reject an empty timezone string",
    ),
    ExpressionTestCase(
        "tz_nonexistent_olson",
        doc={"timezone": "America/Nowhere"},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateToParts should reject a non-existent Olson name",
    ),
]

# Property [Timezone Type Rejection]: a timezone that is not a string or null is rejected.
DATETOPARTS_TZ_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_type_{tid}",
        doc={"timezone": val},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateToParts should reject {tid} as a timezone",
    )
    for tid, val in [
        ("int", 5),
        ("double", 1.0),
        ("int64", Int64(5)),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("object", {"tz": "UTC"}),
        ("array", ["UTC"]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex(".*")),
        ("javascript", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

DATETOPARTS_TZ_VALIDATION_TESTS: list[ExpressionTestCase] = (
    DATETOPARTS_TZ_NULL_MISSING_TESTS
    + DATETOPARTS_TZ_STRING_ERROR_TESTS
    + DATETOPARTS_TZ_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_TZ_VALIDATION_TESTS))
def test_dateToParts_timezone_validation(collection, test_case: ExpressionTestCase):
    """Test $dateToParts timezone validation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
