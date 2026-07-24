"""$dateAdd / $dateSubtract equivalence under amount negation, plus add/subtract roundtrips."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Negation Equivalence]: $dateAdd(date, unit, N) equals $dateSubtract(date, unit, -N),
# verified server-side with $eq.
DATEADD_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"negation_{unit}_{amount}",
            expression={
                "$eq": [
                    {
                        "$dateAdd": {
                            "startDate": datetime(2021, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
                            "unit": unit,
                            "amount": amount,
                        }
                    },
                    {
                        "$dateSubtract": {
                            "startDate": datetime(2021, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
                            "unit": unit,
                            "amount": -amount,
                        }
                    },
                ]
            },
            expected=True,
            msg=f"$dateAdd should equal $dateSubtract with a negated {unit} amount",
        )
        for unit, amount in [
            ("year", 1),
            ("quarter", 2),
            ("month", 3),
            ("week", 4),
            ("day", 10),
            ("hour", 24),
            ("minute", 120),
            ("second", 3600),
            ("millisecond", 5000),
        ]
    ],
    ExpressionTestCase(
        "negation_with_timezone",
        expression={
            "$eq": [
                {
                    "$dateAdd": {
                        "startDate": datetime(2021, 3, 14, 10, 0, 0, tzinfo=timezone.utc),
                        "unit": "day",
                        "amount": 1,
                        "timezone": "America/New_York",
                    }
                },
                {
                    "$dateSubtract": {
                        "startDate": datetime(2021, 3, 14, 10, 0, 0, tzinfo=timezone.utc),
                        "unit": "day",
                        "amount": -1,
                        "timezone": "America/New_York",
                    }
                },
            ]
        },
        expected=True,
        msg="$dateAdd should equal $dateSubtract with a negated amount and a timezone",
    ),
    ExpressionTestCase(
        "negation_int64_amount",
        expression={
            "$eq": [
                {
                    "$dateAdd": {
                        "startDate": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                        "unit": "second",
                        "amount": Int64(86400),
                    }
                },
                {
                    "$dateSubtract": {
                        "startDate": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                        "unit": "second",
                        "amount": Int64(-86400),
                    }
                },
            ]
        },
        expected=True,
        msg="$dateAdd should equal $dateSubtract with negated Int64 amounts",
    ),
]

# Property [Roundtrip]: adding then subtracting the same amount returns the original date,
# reflecting end-of-month clamping.
DATEADD_ROUNDTRIP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "roundtrip_day_30",
        expression={
            "$dateSubtract": {
                "startDate": {
                    "$dateAdd": {
                        "startDate": datetime(2021, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
                        "unit": "day",
                        "amount": 30,
                    }
                },
                "unit": "day",
                "amount": 30,
            }
        },
        expected=datetime(2021, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
        msg="add then subtract of the same amount should return the original date",
    ),
    ExpressionTestCase(
        "roundtrip_month_clamping",
        expression={
            "$dateSubtract": {
                "startDate": {
                    "$dateAdd": {
                        "startDate": datetime(2021, 1, 31, 12, 0, 0, tzinfo=timezone.utc),
                        "unit": "month",
                        "amount": 1,
                    }
                },
                "unit": "month",
                "amount": 1,
            }
        },
        # Jan 31 + 1 month clamps to Feb 28, and Feb 28 - 1 month lands on Jan 28, not Jan 31.
        expected=datetime(2021, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
        msg="a month roundtrip should reflect end-of-month clamping",
    ),
]

DATEADD_DATESUBTRACT_TESTS = DATEADD_EQUIVALENCE_TESTS + DATEADD_ROUNDTRIP_TESTS


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_DATESUBTRACT_TESTS))
def test_dateAdd_dateSubtract(collection, test_case: ExpressionTestCase):
    """Test $dateAdd and $dateSubtract equivalence and roundtrips."""
    result = execute_expression(collection, test_case.expression)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
