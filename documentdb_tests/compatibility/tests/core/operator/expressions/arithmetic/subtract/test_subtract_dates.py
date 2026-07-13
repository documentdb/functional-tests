from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_TWO_AND_HALF,
    INT32_ZERO,
)

# Property [Date - numeric]: $subtract returns a date when the minuend is a date and subtrahend
# is numeric (milliseconds).
DATE_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_int32",
        doc={
            "a": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            "b": 86400000,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$subtract should subtract int32 milliseconds from a date",
    ),
    ExpressionTestCase(
        "date_int64",
        doc={
            "a": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            "b": Int64(86400000),
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$subtract should subtract int64 milliseconds from a date",
    ),
    # Date minus negative number (moves date forward)
    ExpressionTestCase(
        "date_negative",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "b": -86400000,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        msg="$subtract should move a date forward when subtracting a negative millisecond offset",
    ),
    ExpressionTestCase(
        "date_zero",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "b": INT32_ZERO,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$subtract should return the same date when subtracting zero milliseconds",
    ),
    ExpressionTestCase(
        "date_negative_zero",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "b": DOUBLE_NEGATIVE_ZERO,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$subtract should return the same date when subtracting negative-zero milliseconds",
    ),
]

# Property [Date - date]: $subtract returns the difference in milliseconds when both operands
# are dates.
DATE_DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "two_dates",
        doc={
            "a": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(86400000),
        msg="$subtract of two dates should return the difference in milliseconds",
    ),
    ExpressionTestCase(
        "two_dates_negative",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(-86400000),
        msg="$subtract of two dates should return negative ms when the minuend date is earlier",
    ),
]

# Property [Date rounding]: fractional ms operands are rounded.
DATE_ROUNDING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_decimal",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            "b": DECIMAL128_ONE_AND_HALF,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 998000, tzinfo=timezone.utc),
        msg="$subtract should round Decimal128 1.5 ms to 2 ms before subtracting",
    ),
    ExpressionTestCase(
        "date_double_round_up",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, 3000, tzinfo=timezone.utc),
            "b": DOUBLE_TWO_AND_HALF,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$subtract should round double 2.5 ms up to 3 ms before subtracting",
    ),
    ExpressionTestCase(
        "date_double_round_down_negative",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "b": -2.5,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 3000, tzinfo=timezone.utc),
        msg="$subtract should round double -2.5 ms down to -3 ms before subtracting",
    ),
    ExpressionTestCase(
        "date_double_truncates",
        doc={
            "a": datetime(2026, 1, 1, 0, 0, 0, 5000, tzinfo=timezone.utc),
            "b": 4.4,
        },
        expression={"$subtract": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
        msg="$subtract should round double 4.4 ms to 4 ms before subtracting from a date",
    ),
]

SUBTRACT_DATE_TESTS: list[ExpressionTestCase] = (
    DATE_NUMERIC_TESTS + DATE_DATE_TESTS + DATE_ROUNDING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_DATE_TESTS))
def test_subtract_dates(collection, test_case: ExpressionTestCase):
    """Test $subtract date arithmetic: date minus numeric and date minus date."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
