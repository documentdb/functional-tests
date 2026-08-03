"""Tests for $dateToString type validation of the date, format, and timezone fields."""

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
    DATETOSTRING_INVALID_FORMAT_TYPE_ERROR,
    INVALID_TIMEZONE_TYPE_ERROR,
    TYPE_MISMATCH_DATE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [date Type Rejection]: any non-date, non-null date value is rejected as a type mismatch.
DATETOSTRING_DATE_TYPE_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"date_type_{tid}",
            doc={"date": val},
            expression={"$dateToString": {"date": "$date", "format": "%Y"}},
            error_code=TYPE_MISMATCH_DATE_ERROR,
            msg=f"$dateToString should reject a {tid} date",
        )
        for tid, val in [
            ("int32", 123),
            ("int64", Int64(123)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("string", "2024-01-01"),
            ("bool_true", True),
            ("bool_false", False),
            ("object", {"a": 1}),
            ("array", [1, 2]),
            ("binary", Binary(b"\x01")),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    ExpressionTestCase(
        "date_nan",
        doc={"date": FLOAT_NAN},
        expression={"$dateToString": {"date": "$date", "format": "%Y"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$dateToString should reject a NaN date",
    ),
    ExpressionTestCase(
        "date_infinity",
        doc={"date": FLOAT_INFINITY},
        expression={"$dateToString": {"date": "$date", "format": "%Y"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$dateToString should reject an infinity date",
    ),
    ExpressionTestCase(
        "date_decimal128_nan",
        doc={"date": DECIMAL128_NAN},
        expression={"$dateToString": {"date": "$date", "format": "%Y"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$dateToString should reject a Decimal128 NaN date",
    ),
    ExpressionTestCase(
        "date_decimal128_infinity",
        doc={"date": DECIMAL128_INFINITY},
        expression={"$dateToString": {"date": "$date", "format": "%Y"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$dateToString should reject a Decimal128 infinity date",
    ),
    ExpressionTestCase(
        "date_decimal128_neg_infinity",
        doc={"date": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$dateToString": {"date": "$date", "format": "%Y"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$dateToString should reject a Decimal128 negative-infinity date",
    ),
]

# Property [format Type Rejection]: any non-string, non-null format is rejected as an invalid type.
DATETOSTRING_FORMAT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"format_type_{tid}",
        doc={"format": val},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "format": "$format",
            }
        },
        error_code=DATETOSTRING_INVALID_FORMAT_TYPE_ERROR,
        msg=f"$dateToString should reject a {tid} format",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("object", {"%Y": 1}),
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
DATETOSTRING_TIMEZONE_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"timezone_type_{tid}",
        doc={"timezone": val},
        expression={
            "$dateToString": {
                "date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
                "format": "%Y",
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateToString should reject a {tid} timezone",
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

DATETOSTRING_TYPE_TESTS: list[ExpressionTestCase] = (
    DATETOSTRING_DATE_TYPE_TESTS + DATETOSTRING_FORMAT_TYPE_TESTS + DATETOSTRING_TIMEZONE_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_TYPE_TESTS))
def test_dateToString_types(collection, test_case: ExpressionTestCase):
    """Test $dateToString type validation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
