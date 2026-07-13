"""$dateAdd operand evaluation: literal operands and field-reference resolution."""

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

# Property [Literal Input]: $dateAdd evaluates literal operands.
DATEADD_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_year_add",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "year",
                "amount": 1,
            }
        },
        expected=datetime(2001, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 1 year from literal operands",
    ),
    ExpressionTestCase(
        "literal_day_add",
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": 10,
            }
        },
        expected=datetime(2000, 1, 11, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 10 days from literal operands",
    ),
    ExpressionTestCase(
        "literal_null_startDate",
        expression={"$dateAdd": {"startDate": None, "unit": "day", "amount": 1}},
        expected=None,
        msg="$dateAdd should return null for a literal null startDate",
    ),
]

# Property [Field Reference Operands]: the amount and unit operands resolve from field references.
DATEADD_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_amount",
        doc={"amt": 5},
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": "$amt",
            }
        },
        expected=datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should resolve the amount from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_unit",
        doc={"unit_field": "day"},
        expression={
            "$dateAdd": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "$unit_field",
                "amount": 5,
            }
        },
        expected=datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should resolve the unit from a field reference",
    ),
]

DATEADD_EXPRESSION_TESTS: list[ExpressionTestCase] = DATEADD_LITERAL_TESTS + DATEADD_FIELD_REF_TESTS


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_EXPRESSION_TESTS))
def test_dateAdd_expressions(collection, test_case: ExpressionTestCase):
    """Test $dateAdd evaluates literal and field-reference operands."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
