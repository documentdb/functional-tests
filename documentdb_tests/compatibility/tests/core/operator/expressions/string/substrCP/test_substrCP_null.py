from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Null String]: when the string expression is null or missing, the result is "".
SUBSTRCP_NULL_STRING_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "null_string",
        string=None,
        index=0,
        count=1,
        expected="",
        msg="$substrCP should return empty string when string is null",
    ),
    SubstrCPTest(
        "missing_string",
        string=MISSING,
        index=0,
        count=1,
        expected="",
        msg="$substrCP should return empty string when string is missing",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_NULL_STRING_TESTS))
def test_substrcp_null(collection, test_case: SubstrCPTest):
    """Test $substrCP null string cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
