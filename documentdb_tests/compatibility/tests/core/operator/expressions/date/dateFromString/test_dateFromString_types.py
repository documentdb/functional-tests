"""Tests for $dateFromString type validation of the dateString, format, and timezone fields."""

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
    CONVERSION_FAILURE_ERROR,
    DATEFROMSTRING_INVALID_FORMAT_TYPE_ERROR,
    INVALID_TIMEZONE_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
)

# Property [dateString Type Rejection]: any non-string, non-null dateString fails conversion.
DATEFROMSTRING_DATESTRING_TYPE_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"dateString_type_{tid}",
            doc={"dateString": val},
            expression={"$dateFromString": {"dateString": "$dateString"}},
            error_code=CONVERSION_FAILURE_ERROR,
            msg=f"$dateFromString should reject a {tid} dateString",
        )
        for tid, val in [
            ("int32", 123),
            ("int64", Int64(123)),
            ("double", 1.5),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("object", {"a": 1}),
            ("array", [1, 2]),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("objectid", ObjectId("000000000000000000000000")),
            ("timestamp", Timestamp(0, 1)),
            ("binary", Binary(b"\x01")),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    ExpressionTestCase(
        "dateString_decimal128_infinity",
        doc={"dateString": DECIMAL128_INFINITY},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject a Decimal128 infinity dateString",
    ),
    ExpressionTestCase(
        "dateString_decimal128_neg_infinity",
        doc={"dateString": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject a Decimal128 negative-infinity dateString",
    ),
]

# Property [format Type Rejection]: any non-string, non-null format is rejected as an invalid type.
DATEFROMSTRING_FORMAT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"format_type_{tid}",
        doc={"format": val},
        expression={"$dateFromString": {"dateString": "2024-01-01", "format": "$format"}},
        error_code=DATEFROMSTRING_INVALID_FORMAT_TYPE_ERROR,
        msg=f"$dateFromString should reject a {tid} format",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("object", {"f": "%Y"}),
        ("array", ["%Y"]),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("000000000000000000000000")),
        ("timestamp", Timestamp(0, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [timezone Type Rejection]: any non-string, non-null timezone is rejected as an invalid
# type.
DATEFROMSTRING_TIMEZONE_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"timezone_type_{tid}",
        doc={"timezone": val},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateFromString should reject a {tid} timezone",
    )
    for tid, val in [
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 5.0),
        ("decimal128", Decimal128("5")),
        ("bool", True),
        ("object", {"tz": "UTC"}),
        ("array", ["UTC"]),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("000000000000000000000000")),
        ("timestamp", Timestamp(0, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

DATEFROMSTRING_TYPE_TESTS: list[ExpressionTestCase] = (
    DATEFROMSTRING_DATESTRING_TYPE_TESTS
    + DATEFROMSTRING_FORMAT_TYPE_TESTS
    + DATEFROMSTRING_TIMEZONE_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMSTRING_TYPE_TESTS))
def test_dateFromString_types(collection, test_case: ExpressionTestCase):
    """Test $dateFromString type validation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
