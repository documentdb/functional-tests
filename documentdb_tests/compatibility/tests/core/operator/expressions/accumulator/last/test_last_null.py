from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.last.utils.last_common import (  # noqa: E501
    LastTest,
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
LAST_NULL_TESTS: list[LastTest] = [
    LastTest(
        "null_literal",
        value=None,
        expected=None,
        msg="$last should return null when argument is null",
    ),
    LastTest(
        "null_missing_field",
        value=MISSING,
        expected=None,
        msg="$last should return null when argument references a missing field",
    ),
    LastTest(
        "null_expression_returning_null",
        value={"$literal": None},
        expected=None,
        msg="$last should return null when argument is an expression returning null",
    ),
    LastTest(
        "null_field_reference",
        value="$val",
        document={"val": None},
        expected=None,
        msg="$last should return null when argument is a field reference to null",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LAST_NULL_TESTS))
def test_last_null(collection, test_case: LastTest):
    """Test $last cases."""
    if test_case.document is not None:
        result = execute_expression_with_insert(
            collection, {"$last": test_case.value}, test_case.document
        )
    else:
        result = execute_expression(collection, {"$last": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
