from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [String Size Limit - Success]: strings one byte under the limit are
# accepted in all parameter positions, and a shrinking replacement succeeds
# when the input itself is under the limit.
REPLACEONE_SIZE_LIMIT_SUCCESS_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "size_success_input_max",
        input=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
        find="xyz",
        replacement="abc",
        expected=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
        msg="$replaceOne size limit: success input max",
    ),
    # Large input with a shrinking replacement stays under the limit.
    ReplaceOneTest(
        "size_success_shrinking_replacement",
        input=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
        find="a",
        replacement="",
        expected=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 2)),
        msg="$replaceOne size limit: success shrinking replacement",
    ),
    ReplaceOneTest(
        "size_success_find_max",
        input="hello",
        find=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
        replacement="X",
        expected="hello",
        msg="$replaceOne size limit: success find max",
    ),
    # Replace at start of a near-limit string.
    ReplaceOneTest(
        "size_find_at_start",
        input=lazy(lambda: "X" + "a" * (STRING_SIZE_LIMIT_BYTES - 2)),
        find="X",
        replacement="Y",
        expected=lazy(lambda: "Y" + "a" * (STRING_SIZE_LIMIT_BYTES - 2)),
        msg="$replaceOne size limit: find at start",
    ),
    # Replace at end of a near-limit string.
    ReplaceOneTest(
        "size_find_at_end",
        input=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 2) + "X"),
        find="X",
        replacement="Y",
        expected=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 2) + "Y"),
        msg="$replaceOne size limit: find at end",
    ),
    # Replace in middle of a near-limit string.
    ReplaceOneTest(
        "size_find_in_middle",
        input=lazy(
            lambda: "a" * ((STRING_SIZE_LIMIT_BYTES - 2) // 2)
            + "X"
            + "a" * ((STRING_SIZE_LIMIT_BYTES - 2) // 2)
        ),
        find="X",
        replacement="Y",
        expected=lazy(
            lambda: "a" * ((STRING_SIZE_LIMIT_BYTES - 2) // 2)
            + "Y"
            + "a" * ((STRING_SIZE_LIMIT_BYTES - 2) // 2)
        ),
        msg="$replaceOne size limit: find in middle",
    ),
    # Large find string replaces entire input. Both at half-limit because two
    # near-limit strings in one command would exceed the BSON document size.
    ReplaceOneTest(
        "size_large_find",
        input=lazy(lambda: "a" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2)),
        find=lazy(lambda: "a" * ((STRING_SIZE_LIMIT_BYTES - 1) // 2)),
        replacement="X",
        expected="X",
        msg="$replaceOne size limit: large find",
    ),
    # Large replacement string.
    ReplaceOneTest(
        "size_large_replacement",
        input="X",
        find="X",
        replacement=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
        expected=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
        msg="$replaceOne size limit: large replacement",
    ),
]


# Property [String Size Limit - Errors]: strings at the size limit produce an
# error, enforced per literal and per expression result, not only on the final
# output.
REPLACEONE_SIZE_LIMIT_ERROR_TESTS: list[ReplaceOneTest] = [
    # Exactly at the limit.
    ReplaceOneTest(
        "size_error_input_at_limit",
        input=lazy(lambda: "a" * STRING_SIZE_LIMIT_BYTES),
        find="a",
        replacement="b",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceOne size limit: error input at limit",
    ),
    # 2-byte chars at the limit.
    ReplaceOneTest(
        "size_error_byte_based_2byte",
        input=lazy(lambda: "\u00e9" * (STRING_SIZE_LIMIT_BYTES // 2)),
        find="\u00e9",
        replacement="e",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceOne size limit: error byte based 2byte",
    ),
    # 4-byte chars at the limit.
    ReplaceOneTest(
        "size_error_byte_based_4byte",
        input=lazy(lambda: "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)),
        find="\U0001f600",
        replacement="x",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceOne size limit: error byte based 4byte",
    ),
    # Input literal rejected even when replacement would shrink the result.
    ReplaceOneTest(
        "size_error_input_shrinking_rejected",
        input=lazy(lambda: "a" * STRING_SIZE_LIMIT_BYTES),
        find="a" * 100,
        replacement="",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceOne size limit: error input shrinking rejected",
    ),
    # Result amplification: input under limit, replacement grows result to limit.
    ReplaceOneTest(
        "size_error_result_amplification",
        input=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
        find="a",
        replacement="aa",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceOne size limit: error result amplification",
    ),
    # Find parameter at the limit.
    ReplaceOneTest(
        "size_error_find_at_limit",
        input="hello",
        find=lazy(lambda: "a" * STRING_SIZE_LIMIT_BYTES),
        replacement="b",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$replaceOne size limit: error find at limit",
    ),
]

REPLACEONE_SIZE_LIMIT_ALL_TESTS = (
    REPLACEONE_SIZE_LIMIT_SUCCESS_TESTS + REPLACEONE_SIZE_LIMIT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_SIZE_LIMIT_ALL_TESTS))
def test_replaceone_size_limit_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne size limit cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
