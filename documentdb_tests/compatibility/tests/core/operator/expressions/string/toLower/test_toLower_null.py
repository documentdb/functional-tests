from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.toLower_common import (
    ToLowerTest,
    _expr,
)

# Property [Null and Missing Behavior]: null, missing, undefined, and expressions evaluating to
# null all produce an empty string.
TOLOWER_NULL_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "null_value", value=None, expected="", msg="$toLower should return empty string for null"
    ),
    ToLowerTest(
        "missing_value",
        value=MISSING,
        expected="",
        msg="$toLower should return empty string for missing field",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOLOWER_NULL_TESTS))
def test_tolower_null(collection, test_case: ToLowerTest):
    """Test $toLower null and missing behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
