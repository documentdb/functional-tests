"""$dateTrunc null and missing propagation: a null or missing operand returns null."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    MISSING,
)

# Property [Null Handling]: a null date, unit, binSize, timezone, or week startOfWeek returns null.
DATETRUNC_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_date",
        doc={"date": None},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=None,
        msg="$dateTrunc should return null for a null date",
    ),
    ExpressionTestCase(
        "null_unit",
        expression={
            "$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc), "unit": None}
        },
        expected=None,
        msg="$dateTrunc should return null for a null unit",
    ),
    ExpressionTestCase(
        "null_binSize",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": None,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a null binSize",
    ),
    ExpressionTestCase(
        "null_timezone",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": None,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a null timezone",
    ),
    ExpressionTestCase(
        "null_startOfWeek_week",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": None,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a null startOfWeek with the week unit",
    ),
]

# Property [Missing Field Reference]: a missing field reference for date or any optional parameter
# returns null.
DATETRUNC_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_date_ref",
        expression={"$dateTrunc": {"date": MISSING, "unit": "day"}},
        expected=None,
        msg="$dateTrunc should return null for a missing date field reference",
    ),
    ExpressionTestCase(
        "missing_binSize_ref",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "hour",
                "binSize": MISSING,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a missing binSize field reference",
    ),
    ExpressionTestCase(
        "missing_timezone_ref",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": MISSING,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a missing timezone field reference",
    ),
    ExpressionTestCase(
        "missing_startOfWeek_ref",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": MISSING,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a missing startOfWeek field reference",
    ),
]

DATETRUNC_NULL_MISSING_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_NULL_TESTS + DATETRUNC_MISSING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_NULL_MISSING_TESTS))
def test_dateTrunc_null(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc returns null for null literals and missing field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
