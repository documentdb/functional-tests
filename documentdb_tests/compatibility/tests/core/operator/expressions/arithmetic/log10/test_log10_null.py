"""Tests for $log10 null and missing field propagation."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: $log10 of null or a missing field returns null.
LOG10_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_value",
        doc={"value": None},
        expression={"$log10": ["$value"]},
        expected=None,
        msg="$log10 should return null for null input",
    ),
    ExpressionTestCase(
        "missing_field",
        doc={},
        expression={"$log10": [MISSING]},
        expected=None,
        msg="$log10 should return null for a missing field",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LOG10_NULL_TESTS))
def test_log10_null(collection, test_case: ExpressionTestCase):
    """Test $log10 null and missing field propagation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
