"""$toObjectId null and missing input tests."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null and Missing Behavior]: if the input is null or missing, the result is null.
TOOBJECTID_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_input",
        msg="null input returns null",
        expression={"$toObjectId": None},
        expected=None,
    ),
    ExpressionTestCase(
        "missing_field",
        msg="Missing field reference returns null",
        expression={"$toObjectId": MISSING},
        expected=None,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TOOBJECTID_NULL_TESTS))
def test_toObjectId_null(collection, test: ExpressionTestCase):
    """$toObjectId returns null for null or missing input."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
