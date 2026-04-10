from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.concat_common import (
    ConcatTest,
)

# Property [String Size Limit - Success]: a result just under the size limit succeeds, and null
# propagation takes precedence over the size limit when no single literal exceeds it.
CONCAT_SIZE_LIMIT_SUCCESS_TESTS: list[ConcatTest] = [
    # Two large strings concatenated, just under the limit.
    ConcatTest(
        "size_two_args_one_under",
        args=[
            "a" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2),
            "b" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2),
        ],
        expected="a" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2)
        + "b" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2),
        msg="$concat should handle two large strings concatenated together",
    ),
    ConcatTest(
        "size_one_under",
        args=["a" * (STRING_SIZE_LIMIT_BYTES - 1)],
        expected="a" * (STRING_SIZE_LIMIT_BYTES - 1),
        msg="$concat should succeed when result is one byte under the size limit",
    ),
    # 2-byte chars: one byte under the limit.
    ConcatTest(
        "size_one_under_2byte",
        args=["é" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a"],
        expected="é" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2) + "a",
        msg="$concat should succeed with 2-byte chars one byte under the limit",
    ),
    # 4-byte chars: one byte under the limit.
    ConcatTest(
        "size_one_under_4byte",
        args=["😀" * ((STRING_SIZE_LIMIT_BYTES - 1) // 4) + "abc"],
        expected="😀" * ((STRING_SIZE_LIMIT_BYTES - 1) // 4) + "abc",
        msg="$concat should succeed with 4-byte chars one byte under the limit",
    ),
    # Null propagation wins when individual args are under the limit.
    ConcatTest(
        "size_null_precedence",
        args=["a" * (STRING_SIZE_LIMIT_BYTES // 2), None, "b" * (STRING_SIZE_LIMIT_BYTES // 2)],
        expected=None,
        msg="$concat should return null when null appears among large strings under the limit",
    ),
]

# Property [String Size Limit - Error]: a result at or above the size limit produces an error.
STRING_SIZE_LIMIT_ERROR_TESTS: list[ConcatTest] = [
    ConcatTest(
        "size_at_limit",
        args=["a" * STRING_SIZE_LIMIT_BYTES],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$concat should reject result at the size limit",
    ),
    # Two halves summing to exactly the limit.
    ConcatTest(
        "size_two_halves",
        args=["a" * (STRING_SIZE_LIMIT_BYTES // 2), "b" * (STRING_SIZE_LIMIT_BYTES // 2)],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$concat should reject two strings summing to the size limit",
    ),
    # 2-byte chars totaling exactly the limit.
    ConcatTest(
        "size_at_limit_2byte",
        args=["é" * (STRING_SIZE_LIMIT_BYTES // 2)],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$concat should reject 2-byte chars totaling the size limit",
    ),
    # 4-byte chars totaling exactly the limit.
    ConcatTest(
        "size_at_limit_4byte",
        args=["😀" * (STRING_SIZE_LIMIT_BYTES // 4)],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$concat should reject 4-byte chars totaling the size limit",
    ),
    # Many small operands summing to exactly the limit.
    ConcatTest(
        "size_many_small",
        args=["a" * (STRING_SIZE_LIMIT_BYTES // 1024)] * 1024,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$concat should reject many small operands summing to the size limit",
    ),
    # Operand produced by a nested expression rather than a literal.
    ConcatTest(
        "size_nested",
        args=[
            {"$concat": ["a" * (STRING_SIZE_LIMIT_BYTES // 2)]},
            "b" * (STRING_SIZE_LIMIT_BYTES // 2),
        ],
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$concat should reject nested expression result exceeding the size limit",
    ),
]

CONCAT_SIZE_LIMIT_TESTS = CONCAT_SIZE_LIMIT_SUCCESS_TESTS + STRING_SIZE_LIMIT_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_SIZE_LIMIT_TESTS))
def test_concat_size_limit_cases(collection, test_case: ConcatTest):
    """Test $concat size limit cases."""
    result = execute_expression(collection, {"$concat": test_case.args})
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


def test_concat_size_limit_stored_field(collection):
    """Test $concat size limit is enforced when stored fields contribute to the result."""
    result = execute_project_with_insert(
        collection,
        {"s": "a" * (STRING_SIZE_LIMIT_BYTES // 2)},
        {"result": {"$concat": ["$s", "b" * (STRING_SIZE_LIMIT_BYTES // 2)]}},
    )
    assertFailureCode(
        result, STRING_SIZE_LIMIT_ERROR, msg="$concat should enforce size limit with stored fields"
    )
