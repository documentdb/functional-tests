"""$dateDiff basic behavior: valid differences, result sign, and long return type."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT64_ZERO,
)

# Property [Valid Operation]: with valid start date, end date, and unit, the difference is
# returned as a long, and the optional timezone and startOfWeek fields are accepted.
DATEDIFF_VALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_required",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(152),
        msg="$dateDiff should return the day difference for the required fields",
    ),
    ExpressionTestCase(
        "with_timezone",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": "UTC",
            }
        },
        expected=Int64(152),
        msg="$dateDiff should accept an optional timezone",
    ),
    ExpressionTestCase(
        "with_startOfWeek",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should accept an optional startOfWeek for the week unit",
    ),
    ExpressionTestCase(
        "all_five_fields",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 31, tzinfo=timezone.utc),
                "unit": "week",
                "timezone": "UTC",
                "startOfWeek": "monday",
            }
        },
        expected=Int64(4),
        msg="$dateDiff should accept all five fields together",
    ),
]

# Property [Sign Handling]: the difference is positive when endDate follows startDate,
# negative when it precedes, and zero when they are equal.
DATEDIFF_SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_diff",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(152),
        msg="$dateDiff should return a positive difference when endDate follows startDate",
    ),
    ExpressionTestCase(
        "negative_diff",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(-152),
        msg="$dateDiff should return a negative difference when endDate precedes startDate",
    ),
    ExpressionTestCase(
        "zero_diff",
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=INT64_ZERO,
        msg="$dateDiff should return zero when startDate equals endDate",
    ),
    ExpressionTestCase(
        "negative_year",
        expression={
            "$dateDiff": {
                "startDate": datetime(2022, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "year",
            }
        },
        expected=Int64(-1),
        msg="$dateDiff should return a negative year difference",
    ),
    ExpressionTestCase(
        "negative_month",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 6, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(-5),
        msg="$dateDiff should return a negative month difference",
    ),
]

# Property [Return Type]: $dateDiff returns a long regardless of the unit.
DATEDIFF_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_day",
        expression={
            "$type": {
                "$dateDiff": {
                    "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                    "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                    "unit": "day",
                }
            }
        },
        expected="long",
        msg="$dateDiff should return a long for a day difference",
    ),
    ExpressionTestCase(
        "return_type_millisecond",
        expression={
            "$type": {
                "$dateDiff": {
                    "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                    "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                    "unit": "millisecond",
                }
            }
        },
        expected="long",
        msg="$dateDiff should return a long for a millisecond difference",
    ),
]

DATEDIFF_BASIC_TESTS: list[ExpressionTestCase] = (
    DATEDIFF_VALID_TESTS + DATEDIFF_SIGN_TESTS + DATEDIFF_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_BASIC_TESTS))
def test_dateDiff_basic(collection, test_case: ExpressionTestCase):
    """Test $dateDiff produces the correct value, sign, and long return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
