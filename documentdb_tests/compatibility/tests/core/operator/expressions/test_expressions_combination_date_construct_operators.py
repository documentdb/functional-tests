"""Cross-operator combination tests for date construction and conversion operators.

Tests $dateFromString inside other date operators, a $dateToString round-trip,
and $toDate/$convert equivalence."""

from datetime import datetime, timezone

import pytest
from bson import Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Cross-Operator Composition]: date construction and conversion operators
# compose with one another and agree with equivalent conversions.
DATE_CONSTRUCT_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dateFromString_inside_dateAdd",
        expression={
            "$dateAdd": {
                "startDate": {"$dateFromString": {"dateString": "2024-06-15"}},
                "unit": "day",
                "amount": 5,
            }
        },
        expected=datetime(2024, 6, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept $dateFromString as its startDate",
    ),
    ExpressionTestCase(
        "dateFromString_inside_dateSubtract",
        expression={
            "$dateSubtract": {
                "startDate": {"$dateFromString": {"dateString": "2024-06-15"}},
                "unit": "month",
                "amount": 1,
            }
        },
        expected=datetime(2024, 5, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should accept $dateFromString as its startDate",
    ),
    ExpressionTestCase(
        "dateFromString_inside_dateTrunc",
        expression={
            "$dateTrunc": {
                "date": {"$dateFromString": {"dateString": "2024-06-15T10:30:00"}},
                "unit": "day",
            }
        },
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept $dateFromString as its date",
    ),
    ExpressionTestCase(
        "dateFromString_inside_dateDiff",
        expression={
            "$dateDiff": {
                "startDate": {"$dateFromString": {"dateString": "2024-01-01"}},
                "endDate": {"$dateFromString": {"dateString": "2024-06-15"}},
                "unit": "month",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should accept $dateFromString as both date inputs",
    ),
    ExpressionTestCase(
        "dateToString_of_dateFromString_roundtrip",
        expression={
            "$dateToString": {
                "date": {"$dateFromString": {"dateString": "2024-06-15T10:30:45.123Z"}},
                "format": "%Y-%m-%dT%H:%M:%S.%LZ",
            }
        },
        expected="2024-06-15T10:30:45.123Z",
        msg="$dateToString should round-trip a $dateFromString result",
    ),
    ExpressionTestCase(
        "toDate_convert_equivalence_string",
        expression={
            "$eq": [{"$toDate": "2024-06-15"}, {"$convert": {"input": "2024-06-15", "to": "date"}}]
        },
        expected=True,
        msg="$toDate should match $convert to date for a string input",
    ),
    ExpressionTestCase(
        "toDate_convert_equivalence_long",
        expression={
            "$eq": [
                {"$toDate": Int64(1718409600000)},
                {"$convert": {"input": Int64(1718409600000), "to": "date"}},
            ]
        },
        expected=True,
        msg="$toDate should match $convert to date for a long input",
    ),
    ExpressionTestCase(
        "toDate_convert_equivalence_double",
        expression={
            "$eq": [{"$toDate": 86400000.0}, {"$convert": {"input": 86400000.0, "to": "date"}}]
        },
        expected=True,
        msg="$toDate should match $convert to date for a double input",
    ),
    ExpressionTestCase(
        "toDate_convert_equivalence_oid",
        expression={
            "$eq": [
                {"$toDate": ObjectId("600000000000000000000000")},
                {"$convert": {"input": ObjectId("600000000000000000000000"), "to": "date"}},
            ]
        },
        expected=True,
        msg="$toDate should match $convert to date for an ObjectId input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATE_CONSTRUCT_COMBINATION_TESTS))
def test_date_construct_combination(collection, test_case: ExpressionTestCase):
    """Test date construction and conversion operators composed together."""
    result = execute_expression(collection, test_case.expression)
    assert_expression_result(result, expected=test_case.expected, msg=test_case.msg)
