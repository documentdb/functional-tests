"""Date arithmetic tests for the $subtract operator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Date minus numeric]: $subtract subtracts a numeric duration in milliseconds from a date.
SUBTRACT_DATE_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_int32",
        doc={"a": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc), "b": 86400000},
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="Should subtract int32 milliseconds from a date",
    ),
    ExpressionTestCase(
        "date_int64",
        doc={"a": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc), "b": Int64(86400000)},
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="Should subtract int64 milliseconds from a date",
    ),
    ExpressionTestCase(
        "date_decimal",
        doc={"a": datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc), "b": Decimal128("1.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 998000, tzinfo=timezone.utc),
        msg="Should subtract decimal128 milliseconds from a date",
    ),
    ExpressionTestCase(
        "date_double_round_up",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, 3000, tzinfo=timezone.utc), 2.5]},
        expected=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        msg="Should round up when subtracting fractional double milliseconds",
    ),
    ExpressionTestCase(
        "date_double_truncates",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, 5000, tzinfo=timezone.utc), 4.4]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
        msg="Should truncate when subtracting fractional double milliseconds",
    ),
    ExpressionTestCase(
        "date_negative",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), -86400000]},
        expected=datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="Should subtract negative milliseconds from a date",
    ),
    ExpressionTestCase(
        "date_zero",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), 0]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="Should subtract zero milliseconds from a date",
    ),
    ExpressionTestCase(
        "date_negative_zero",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), -0.0]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="Should subtract negative zero from a date",
    ),
]

# Property [Date minus date]: $subtract returns the duration in milliseconds between two dates.
SUBTRACT_DATE_DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "two_dates",
        doc={
            "a": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(86400000),
        msg="Should subtract an earlier date from a later date",
    ),
    ExpressionTestCase(
        "two_dates_negative",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(-86400000),
        msg="Should subtract a later date from an earlier date",
    ),
]

# Property [Date errors]: $subtract rejects invalid date arithmetic.
SUBTRACT_DATE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "number_minus_date",
        doc={},
        expression={"$subtract": [1, datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject subtracting a date from a number",
    ),
    ExpressionTestCase(
        "date_minus_string",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), "string"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject subtracting a string from a date",
    ),
    ExpressionTestCase(
        "date_minus_bool",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), True]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject subtracting a boolean from a date",
    ),
    ExpressionTestCase(
        "date_minus_array",
        doc={},
        expression={"$subtract": [datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), [1, 2]]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject subtracting an array from a date",
    ),
]

SUBTRACT_DATE_TESTS = (
    SUBTRACT_DATE_NUMERIC_TESTS + SUBTRACT_DATE_DATE_TESTS + SUBTRACT_DATE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_DATE_TESTS))
def test_subtract_dates(collection, test_case: ExpressionTestCase):
    """Test $subtract date arithmetic cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
