from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.toUpper_common import (
    ToUpperTest,
    _expr,
)

# Property [Null and Missing Behavior]: null, missing, or undefined arguments return empty string.
TOUPPER_NULL_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "null_literal", value=None, expected="", msg="$toUpper should return empty string for null"
    ),
    ToUpperTest(
        "missing_field",
        value=MISSING,
        expected="",
        msg="$toUpper should return empty string for missing field",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_NULL_TESTS))
def test_toupper_null(collection, test_case: ToUpperTest):
    """Test $toUpper null and missing behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
