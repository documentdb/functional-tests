"""$dateSubtract operand evaluation: literal operands and field-reference resolution."""

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

# Property [Literal Input]: $dateSubtract evaluates literal operands.
DATESUBTRACT_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_year_subtract",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "year",
                "amount": 1,
            }
        },
        expected=datetime(1999, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract 1 year from literal operands",
    ),
    ExpressionTestCase(
        "literal_day_subtract",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 11, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": 10,
            }
        },
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should subtract 10 days from literal operands",
    ),
    ExpressionTestCase(
        "literal_null_startDate",
        expression={"$dateSubtract": {"startDate": None, "unit": "day", "amount": 1}},
        expected=None,
        msg="$dateSubtract should return null for a literal null startDate",
    ),
]

# Property [Field Reference Operands]: the amount and unit operands resolve from field references.
DATESUBTRACT_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_amount",
        doc={"amt": 5},
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": "$amt",
            }
        },
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should resolve the amount from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_unit",
        doc={"unit_field": "day"},
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "$unit_field",
                "amount": 5,
            }
        },
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should resolve the unit from a field reference",
    ),
]

DATESUBTRACT_EXPRESSION_TESTS: list[ExpressionTestCase] = (
    DATESUBTRACT_LITERAL_TESTS + DATESUBTRACT_FIELD_REF_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATESUBTRACT_EXPRESSION_TESTS))
def test_dateSubtract_expressions(collection, test_case: ExpressionTestCase):
    """Test $dateSubtract evaluates literal and field-reference operands."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
