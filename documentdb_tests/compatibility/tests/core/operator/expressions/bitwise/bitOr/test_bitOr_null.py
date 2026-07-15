# handle null by returning null
from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.bitwise.bitOr.utils.bitOr_common import (  # noqa: E501
    BitOrTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

BITOR_NULL_TESTS: list[BitOrTest] = [
    BitOrTest(
        "null_in_array",
        args=[1, 2, 3, None],
        expected=None,
        msg="$bitOr with null in the operand array should return null",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(BITOR_NULL_TESTS))
def test_bitOr_null(collection, test_case: BitOrTest):
    """Test $bitOr null handling."""
    result = execute_expression(collection, {"$bitOr": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
