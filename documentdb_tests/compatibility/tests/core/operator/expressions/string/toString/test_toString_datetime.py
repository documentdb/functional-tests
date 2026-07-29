"""$toString datetime conversion tests: ISO 8601 formatting, timezone, and precision."""

from datetime import datetime, timedelta, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Datetime Conversion]: datetime values are formatted as ISO 8601
# (YYYY-MM-DDTHH:MM:SS.mmmZ) in UTC with exactly 3 millisecond digits; sub-millisecond
# precision is truncated, not rounded.
TOSTRING_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "datetime_with_ms",
        msg="Datetime with milliseconds formats correctly",
        expression={"$toString": datetime(2024, 6, 15, 12, 30, 45, 123000, tzinfo=timezone.utc)},
        expected="2024-06-15T12:30:45.123Z",
    ),
    ExpressionTestCase(
        "datetime_no_ms",
        msg="Datetime with zero microseconds emits .000Z",
        expression={"$toString": datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc)},
        expected="2024-06-15T12:30:45.000Z",
    ),
    ExpressionTestCase(
        "datetime_epoch",
        msg="Unix epoch formats correctly",
        expression={"$toString": datetime(1970, 1, 1, tzinfo=timezone.utc)},
        expected="1970-01-01T00:00:00.000Z",
    ),
    ExpressionTestCase(
        "datetime_pre_epoch",
        msg="Pre-epoch datetime formats correctly",
        expression={"$toString": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expected="1969-12-31T23:59:59.000Z",
    ),
    ExpressionTestCase(
        "datetime_far_future",
        msg="Far-future datetime formats correctly",
        expression={"$toString": datetime(9999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expected="9999-12-31T23:59:59.999Z",
    ),
    ExpressionTestCase(
        "datetime_year_0001",
        msg="Year 0001 formats with zero-padded year",
        expression={"$toString": datetime(1, 1, 1, tzinfo=timezone.utc)},
        expected="0001-01-01T00:00:00.000Z",
    ),
    ExpressionTestCase(
        "datetime_leap_day",
        msg="Leap day (Feb 29) formats correctly",
        expression={"$toString": datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)},
        expected="2024-02-29T12:00:00.000Z",
    ),
    ExpressionTestCase(
        "datetime_non_utc",
        msg="Non-UTC timezone is converted to UTC before formatting",
        expression={
            "$toString": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=5)))
        },
        expected="2024-06-15T07:00:00.000Z",
    ),
    ExpressionTestCase(
        "datetime_naive",
        msg="Naive datetime (no timezone) is treated as UTC",
        expression={"$toString": datetime(2024, 1, 1)},
        expected="2024-01-01T00:00:00.000Z",
    ),
    ExpressionTestCase(
        "datetime_sub_ms_truncated",
        msg="Sub-millisecond precision is truncated, not rounded",
        expression={"$toString": datetime(2024, 1, 1, 0, 0, 0, 123999, tzinfo=timezone.utc)},
        expected="2024-01-01T00:00:00.123Z",
    ),
    ExpressionTestCase(
        "datetime_sub_ms_half",
        msg="Sub-millisecond truncation at 0.5ms boundary does not round up",
        expression={"$toString": datetime(2024, 1, 1, 0, 0, 0, 500500, tzinfo=timezone.utc)},
        expected="2024-01-01T00:00:00.500Z",
    ),
    ExpressionTestCase(
        "datetime_end_of_day",
        msg="End-of-day datetime formats correctly",
        expression={"$toString": datetime(2024, 1, 1, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expected="2024-01-01T23:59:59.999Z",
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOSTRING_DATETIME_TESTS, "$toString", "string")),
)
def test_toString_datetime(collection, test: ExpressionTestCase):
    """$toString formats datetime values as ISO 8601 strings in UTC."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
