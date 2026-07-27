"""Tests for $dateToParts type validation of the date and iso8601 fields."""

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
    DATETOPARTS_ISO8601_TYPE_ERROR,
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

# Property [Date Type Rejection]: a date that is not a date, ObjectId, or Timestamp is rejected.
DATETOPARTS_DATE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"date_type_{tid}",
        doc={"date": val},
        expression={"$dateToParts": {"date": "$date"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg=f"$dateToParts should reject {tid} as a date",
    )
    for tid, val in [
        ("int", 123),
        ("double", 1.0),
        ("string", "2017-01-01"),
        ("bool", True),
        ("bool_false", False),
        ("object", {"a": 1}),
        ("array", [1, 2]),
        ("int64", Int64(123)),
        ("decimal128", Decimal128("1")),
        ("regex", Regex(".*")),
        ("binary", Binary(b"\x01")),
        ("javascript", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Non-Finite Date Rejection]: non-finite numeric values are rejected as dates.
DATETOPARTS_DATE_NON_FINITE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"date_{tid}",
        doc={"date": val},
        expression={"$dateToParts": {"date": "$date"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg=f"$dateToParts should reject {tid} as a date",
    )
    for tid, val in [
        ("nan", FLOAT_NAN),
        ("inf", FLOAT_INFINITY),
        ("decimal128_nan", DECIMAL128_NAN),
        ("decimal128_inf", DECIMAL128_INFINITY),
        ("decimal128_neg_inf", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [iso8601 Type Rejection]: an iso8601 that is not a boolean or null is rejected.
DATETOPARTS_ISO8601_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"iso8601_type_{tid}",
        doc={"iso8601": val},
        expression={
            "$dateToParts": {
                "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "iso8601": "$iso8601",
            }
        },
        error_code=DATETOPARTS_ISO8601_TYPE_ERROR,
        msg=f"$dateToParts should reject {tid} as an iso8601 value",
    )
    for tid, val in [
        ("int", 1),
        ("double", 1.0),
        ("int64", Int64(1)),
        ("decimal128", Decimal128("1")),
        ("string", "true"),
        ("object", {"a": 1}),
        ("array", [True]),
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

DATETOPARTS_TYPE_TESTS: list[ExpressionTestCase] = (
    DATETOPARTS_DATE_TYPE_ERROR_TESTS
    + DATETOPARTS_DATE_NON_FINITE_TESTS
    + DATETOPARTS_ISO8601_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_TYPE_TESTS))
def test_dateToParts_types(collection, test_case: ExpressionTestCase):
    """Test $dateToParts type validation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
