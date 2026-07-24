"""Tests for $exp null and missing field propagation."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
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

# Property [Null Propagation]: $exp of null or a missing field returns null.
EXP_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_value",
        doc={"value": None},
        expression={"$exp": ["$value"]},
        expected=None,
        msg="$exp should return null for null input",
    ),
    ExpressionTestCase(
        "missing_field",
        doc={},
        expression={"$exp": [MISSING]},
        expected=None,
        msg="$exp should return null for a missing field",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(EXP_NULL_TESTS))
def test_exp_null(collection, test_case: ExpressionTestCase):
    """Test $exp null and missing field propagation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
