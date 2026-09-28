"""$dateAdd null and missing propagation: a null or missing operand returns null."""

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

# Property [Null Handling]: a null literal for startDate, amount, or unit returns null.
DATEADD_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_startDate",
        doc={"date": None},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
        expected=None,
        msg="$dateAdd should return null for a null startDate",
    ),
    ExpressionTestCase(
        "null_amount",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": None,
            }
        },
        expected=None,
        msg="$dateAdd should return null for a null amount",
    ),
    ExpressionTestCase(
        "null_unit",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": None,
                "amount": 1,
            }
        },
        expected=None,
        msg="$dateAdd should return null for a null unit",
    ),
    ExpressionTestCase(
        "null_startDate_zero_amount",
        doc={"date": None},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 0}},
        expected=None,
        msg="$dateAdd should return null for a null startDate even with a zero amount",
    ),
    ExpressionTestCase(
        "all_null",
        expression={"$dateAdd": {"startDate": None, "unit": None, "amount": None}},
        expected=None,
        msg="$dateAdd should return null when all inputs are null",
    ),
]

# Property [Missing Field Reference]: a missing startDate, amount, unit, or timezone field
# reference returns null.
DATEADD_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_startDate",
        expression={"$dateAdd": {"startDate": MISSING, "unit": "day", "amount": 1}},
        expected=None,
        msg="$dateAdd should return null for a missing startDate field reference",
    ),
    ExpressionTestCase(
        "missing_amount",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": MISSING,
            }
        },
        expected=None,
        msg="$dateAdd should return null for a missing amount field reference",
    ),
    ExpressionTestCase(
        "missing_unit",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": MISSING,
                "amount": 1,
            }
        },
        expected=None,
        msg="$dateAdd should return null for a missing unit field reference",
    ),
    ExpressionTestCase(
        "missing_startDate_zero_amount",
        expression={"$dateAdd": {"startDate": MISSING, "unit": "day", "amount": 0}},
        expected=None,
        msg="$dateAdd should return null for a missing startDate field reference and zero amount",
    ),
    ExpressionTestCase(
        "missing_timezone",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": 1,
                "timezone": MISSING,
            }
        },
        expected=None,
        msg="$dateAdd should return null for a missing timezone field reference",
    ),
    ExpressionTestCase(
        "missing_startDate_with_tz",
        expression={
            "$dateAdd": {"startDate": MISSING, "unit": "day", "amount": 1, "timezone": "UTC"}
        },
        expected=None,
        msg="$dateAdd should return null for a missing startDate even with a timezone",
    ),
]

DATEADD_NULL_MISSING_TESTS: list[ExpressionTestCase] = DATEADD_NULL_TESTS + DATEADD_MISSING_TESTS


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_NULL_MISSING_TESTS))
def test_dateAdd_null(collection, test_case: ExpressionTestCase):
    """Test $dateAdd returns null for null literals and missing field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
