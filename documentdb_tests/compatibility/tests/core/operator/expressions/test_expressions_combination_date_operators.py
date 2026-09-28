"""Cross-operator combinations of $dateAdd/$dateSubtract with $cond, $let, $abs, and nesting."""

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

# Property [Cross-Operator Composition]: date operators compose with $cond, $let, $abs,
# $dateFromString, and each other.
DATE_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dateAdd_inside_cond",
        doc={"date": datetime(2020, 12, 31, 12, 0, 0, tzinfo=timezone.utc), "active": True},
        expression={
            "$cond": {
                "if": "$active",
                "then": {"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
                "else": "$date",
            }
        },
        expected=datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should compose inside $cond",
    ),
    ExpressionTestCase(
        "dateAdd_with_let",
        expression={
            "$let": {
                "vars": {"d": datetime(2020, 12, 31, 12, 0, 0, tzinfo=timezone.utc)},
                "in": {"$dateAdd": {"startDate": "$$d", "unit": "day", "amount": 1}},
            }
        },
        expected=datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept a $let variable as startDate",
    ),
    ExpressionTestCase(
        "dateAdd_nested_literal",
        expression={
            "$dateAdd": {
                "startDate": {"$literal": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
                "unit": "day",
                "amount": 5,
            }
        },
        expected=datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept a nested $literal startDate",
    ),
    ExpressionTestCase(
        "dateAdd_nested_abs",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": {"$abs": -5},
            }
        },
        expected=datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept a nested $abs amount",
    ),
    ExpressionTestCase(
        "dateAdd_nested_dateAdd",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {
                "startDate": {"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1}},
                "unit": "day",
                "amount": 1,
            }
        },
        expected=datetime(2021, 1, 2, 12, 10, 5, tzinfo=timezone.utc),
        msg="nested $dateAdd should accumulate additions",
    ),
    ExpressionTestCase(
        "dateSubtract_from_expression",
        expression={
            "$dateSubtract": {
                "startDate": {"$dateFromString": {"dateString": "2021-06-15"}},
                "unit": "day",
                "amount": 1,
            }
        },
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should accept an expression operator as startDate",
    ),
    ExpressionTestCase(
        "dateSubtract_nested_literal",
        expression={
            "$dateSubtract": {
                "startDate": {"$literal": datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc)},
                "unit": "day",
                "amount": 5,
            }
        },
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should accept a nested $literal startDate",
    ),
    ExpressionTestCase(
        "dateSubtract_nested_abs",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": {"$abs": -5},
            }
        },
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should accept a nested $abs amount",
    ),
    ExpressionTestCase(
        "dateDiff_from_expression",
        expression={
            "$dateDiff": {
                "startDate": {"$dateFromString": {"dateString": "2021-01-01"}},
                "endDate": {"$dateFromString": {"dateString": "2021-01-02"}},
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should accept expression operators as date inputs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATE_COMBINATION_TESTS))
def test_date_operator_combination(collection, test_case: ExpressionTestCase):
    """Test date expression operators composed with other operators."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
