from __future__ import annotations

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR, STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

# Property [String Size Limit Success]: BinData-to-string conversion succeeds
# when the output is below the string size limit.
CONVERT_STRING_SIZE_LIMIT_SUCCESS_TESTS: list[ConvertTest] = [
    ConvertTest(
        "size_limit_hex_under",
        input=Binary(b"A" * (STRING_SIZE_LIMIT_BYTES // 2 - 1)),
        to="string",
        format="hex",
        expected="41" * (STRING_SIZE_LIMIT_BYTES // 2 - 1),
        msg=(
            "$convert should succeed for BinData-to-string when output is"
            " just under the size limit"
        ),
    ),
]

# Property [String Size Limit Errors]: BinData-to-string conversion produces a
# conversion failure error when the output reaches the string size limit.
CONVERT_STRING_SIZE_LIMIT_ERROR_TESTS: list[ConvertTest] = [
    # hex format: 8_388_608 bytes -> 16_777_216 chars (exactly the limit).
    ConvertTest(
        "size_limit_err_hex_at_limit",
        input=Binary(b"A" * (STRING_SIZE_LIMIT_BYTES // 2)),
        to="string",
        format="hex",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject BinData-to-string when hex output reaches the size limit",
    ),
    # base64 format: 12_582_912 bytes -> 16_777_216 chars (exactly the limit).
    ConvertTest(
        "size_limit_err_base64_at_limit",
        input=Binary(b"A" * (STRING_SIZE_LIMIT_BYTES * 3 // 4)),
        to="string",
        format="base64",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject BinData-to-string when base64 output reaches the size limit",
    ),
    # utf8 format: 16_777_216 bytes -> 16_777_216 chars produces a different
    # error code than other formats.
    ConvertTest(
        "size_limit_err_utf8_at_limit",
        input=Binary(b"A" * STRING_SIZE_LIMIT_BYTES),
        to="string",
        format="utf8",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$convert should reject BinData-to-string when utf8 output reaches the size limit",
    ),
    ConvertTest(
        "size_limit_err_oversized_input",
        input="A" * STRING_SIZE_LIMIT_BYTES,
        to="int",
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$convert should reject oversized string in input parameter",
    ),
    ConvertTest(
        "size_limit_err_oversized_to",
        input=42,
        to="A" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$convert should reject oversized string in to parameter",
    ),
    ConvertTest(
        "size_limit_err_oversized_to_type",
        input=42,
        to={"type": "A" * STRING_SIZE_LIMIT_BYTES},
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$convert should reject oversized string in to.type parameter",
    ),
    ConvertTest(
        "size_limit_err_oversized_to_subtype",
        input=42,
        to={"type": "binData", "subtype": "A" * STRING_SIZE_LIMIT_BYTES},
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$convert should reject oversized string in to.subtype parameter",
    ),
    ConvertTest(
        "size_limit_err_oversized_format",
        input=42,
        to="string",
        format="A" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$convert should reject oversized string in format parameter",
    ),
    ConvertTest(
        "size_limit_err_oversized_byte_order",
        input=42,
        to="binData",
        byte_order="A" * STRING_SIZE_LIMIT_BYTES,
        error_code=STRING_SIZE_LIMIT_ERROR,
        msg="$convert should reject oversized string in byteOrder parameter",
    ),
]

CONVERT_SIZE_LIMIT_TESTS = (
    CONVERT_STRING_SIZE_LIMIT_SUCCESS_TESTS + CONVERT_STRING_SIZE_LIMIT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_SIZE_LIMIT_TESTS))
def test_convert_size_limit(collection, test_case: ConvertTest):
    """Test $convert string size limit behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
