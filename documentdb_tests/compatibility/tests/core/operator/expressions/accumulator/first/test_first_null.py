from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.first.utils.first_common import (  # noqa: E501
    FirstTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null and Missing Behavior]: if the argument is null, missing, or an
# expression returning null, the result is null.
FIRST_NULL_TESTS: list[FirstTest] = [
    FirstTest(
        "null_literal",
        value=None,
        expected=None,
        msg="$first should return null when argument is null",
    ),
    FirstTest(
        "null_missing_field",
        value=MISSING,
        expected=None,
        msg="$first should return null when argument references a missing field",
    ),
    FirstTest(
        "null_expression_returning_null",
        value={"$literal": None},
        expected=None,
        msg="$first should return null when argument is an expression returning null",
    ),
    FirstTest(
        "null_field_reference",
        value="$val",
        document={"val": None},
        expected=None,
        msg="$first should return null when argument is a field reference to null",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(FIRST_NULL_TESTS))
def test_first_null(collection, test_case: FirstTest):
    """Test $first cases."""
    if test_case.document is not None:
        result = execute_expression_with_insert(
            collection, {"$first": test_case.value}, test_case.document
        )
    else:
        result = execute_expression(collection, {"$first": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
