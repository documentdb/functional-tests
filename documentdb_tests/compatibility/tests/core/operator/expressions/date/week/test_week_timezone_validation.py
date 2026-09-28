"""Tests for $week timezone validation and null-timezone propagation."""

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

# Property [Timezone Validation]: unparseable zone strings, wrong-typed timezones, and null
# timezones are rejected or propagate null.
WEEK_TIMEZONE_VALIDATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "invalid_tz_olson",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "Not/A_Timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$week should reject an unparseable timezone string",
    ),
    ExpressionTestCase(
        "invalid_tz_nonexistent_olson",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "America/Nowhere"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$week should reject a non-existent Olson timezone",
    ),
    ExpressionTestCase(
        "invalid_tz_offset_format",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "25:00"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$week should reject an unsigned out-of-range offset string",
    ),
    ExpressionTestCase(
        "invalid_tz_numeric_string",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "123"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$week should reject a bare numeric timezone string",
    ),
    ExpressionTestCase(
        "invalid_tz_empty_string",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": ""}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$week should reject an empty-string timezone",
    ),
    ExpressionTestCase(
        "invalid_tz_olson_lowercase",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "america/new_york"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$week should reject an all-lowercase Olson name",
    ),
    ExpressionTestCase(
        "invalid_tz_olson_uppercase",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "AMERICA/NEW_YORK"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$week should reject an all-uppercase Olson name",
    ),
    *[
        ExpressionTestCase(
            f"invalid_tz_{tid}",
            doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
            expression={"$week": {"date": "$date", "timezone": val}},
            error_code=INVALID_TIMEZONE_TYPE_ERROR,
            msg=f"$week should reject a {tid} timezone",
        )
        for tid, val in [
            ("int", 5),
            ("int64", Int64(5)),
            ("double", 3.14),
            ("decimal128", Decimal128("5")),
            ("bool", True),
            ("object", {"tz": "UTC"}),
            ("array", ["UTC"]),
            ("datetime", datetime(2024, 6, 15, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    ExpressionTestCase(
        "null_tz",
        doc={"date": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": None}},
        expected=None,
        msg="$week should return null for a null timezone",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(WEEK_TIMEZONE_VALIDATION_TESTS))
def test_week_timezone_validation(collection, test_case: ExpressionTestCase):
    """Test $week timezone validation and null-timezone propagation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
