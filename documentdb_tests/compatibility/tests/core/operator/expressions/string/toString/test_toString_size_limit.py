"""$toString size limit tests: string and binary inputs at and near the 16 MB limit."""

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR, STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

# Property [String Size Limit Success]: input strings just under the size limit are accepted.
TOSTRING_STRING_SIZE_SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_one_under",
        msg="String one byte under the 16 MB limit passes through",
        expression=lazy(lambda: {"$toString": "a" * (STRING_SIZE_LIMIT_BYTES - 1)}),
        expected=lazy(lambda: "a" * (STRING_SIZE_LIMIT_BYTES - 1)),
    ),
]

# Property [String Size Limit]: input strings at or above the size limit produce an error.
TOSTRING_STRING_SIZE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_at_limit",
        msg="String at the 16 MB byte limit is rejected",
        expression=lazy(lambda: {"$toString": "a" * STRING_SIZE_LIMIT_BYTES}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
]

# Binary base64 encoding: every 3 input bytes produce 4 output characters.
_BINARY_UNDER_LIMIT_BYTES = ((STRING_SIZE_LIMIT_BYTES - 1) // 4) * 3
_BINARY_AT_LIMIT_BYTES = (STRING_SIZE_LIMIT_BYTES // 4) * 3

# Property [Binary Size Limit Success]: binary values whose base64 output fits within the
# string size limit are accepted.
TOSTRING_BINARY_SIZE_SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_under_limit",
        msg="Binary whose base64 output is just under the 16 MB limit is accepted",
        expression=lazy(lambda: {"$toString": Binary(b"\x00" * _BINARY_UNDER_LIMIT_BYTES)}),
        expected=lazy(lambda: "A" * (_BINARY_UNDER_LIMIT_BYTES // 3 * 4)),
    ),
]

# Property [Binary Size Limit]: binary values whose base64 output reaches the string size
# limit produce a conversion failure.
TOSTRING_BINARY_SIZE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_at_limit",
        msg="Binary whose base64 output reaches the 16 MB limit is rejected",
        expression=lazy(lambda: {"$toString": Binary(b"\x00" * _BINARY_AT_LIMIT_BYTES)}),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOSTRING_SIZE_LIMIT_TESTS = (
    TOSTRING_STRING_SIZE_SUCCESS_TESTS
    + TOSTRING_STRING_SIZE_ERROR_TESTS
    + TOSTRING_BINARY_SIZE_SUCCESS_TESTS
    + TOSTRING_BINARY_SIZE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TOSTRING_SIZE_LIMIT_TESTS))
def test_toString_size_limit(collection, test: ExpressionTestCase):
    """$toString enforces the 16 MB string size limit for both string and binary inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
