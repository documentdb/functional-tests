from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)

# Property [Null and Missing in String Position]: when the string parameter is null, missing, or
# undefined, the result is an empty string "".
SUBSTRBYTES_NULL_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "null_string",
        string=None,
        byte_index=0,
        byte_count=5,
        expected="",
        msg="$substrBytes should return empty string for null string parameter",
    ),
    SubstrBytesTest(
        "missing_string",
        string=MISSING,
        byte_index=0,
        byte_count=5,
        expected="",
        msg="$substrBytes should return empty string for missing string parameter",
    ),
    SubstrBytesTest(
        "null_expression",
        string={"$literal": None},
        byte_index=0,
        byte_count=5,
        expected="",
        msg="$substrBytes should return empty string for null expression",
    ),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_NULL_TESTS))
def test_substrbytes_null(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
