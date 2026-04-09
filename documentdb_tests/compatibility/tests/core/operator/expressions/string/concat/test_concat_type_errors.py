from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import CONCAT_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

from .utils.concat_common import (
    ConcatTest,
)

# Property [Type Strictness]: any non-string, non-null argument produces CONCAT_TYPE_ERROR.
CONCAT_TYPE_ERROR_TESTS: list[ConcatTest] = [
    # Invalid value as the only argument.
    ConcatTest(
        "type_array_solo",
        args=[["a"]],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject array argument",
    ),
    ConcatTest(
        "type_binary_solo",
        args=[Binary(b"data")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject binary argument",
    ),
    ConcatTest(
        "type_bool_solo",
        args=[True],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject boolean argument",
    ),
    ConcatTest(
        "type_date_solo",
        args=[datetime(2024, 1, 1, tzinfo=timezone.utc)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject datetime argument",
    ),
    ConcatTest(
        "type_decimal128_solo",
        args=[DECIMAL128_ONE_AND_HALF],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Decimal128 argument",
    ),
    ConcatTest(
        "type_float_solo",
        args=[3.14],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject float argument",
    ),
    ConcatTest(
        "type_int_solo",
        args=[42],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject int argument",
    ),
    ConcatTest(
        "type_long_solo",
        args=[Int64(42)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Int64 argument",
    ),
    ConcatTest(
        "type_maxkey_solo",
        args=[MaxKey()],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject MaxKey argument",
    ),
    ConcatTest(
        "type_minkey_solo",
        args=[MinKey()],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject MinKey argument",
    ),
    ConcatTest(
        "type_object_solo",
        args=[{"a": 1}],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject object argument",
    ),
    ConcatTest(
        "type_objectid_solo",
        args=[ObjectId("507f1f77bcf86cd799439011")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject ObjectId argument",
    ),
    ConcatTest(
        "type_regex_solo",
        args=[Regex("pattern")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject regex argument",
    ),
    ConcatTest(
        "type_timestamp_solo",
        args=[Timestamp(1, 1)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Timestamp argument",
    ),
    ConcatTest(
        "type_code_solo",
        args=[Code("function() {}")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Code argument",
    ),
    ConcatTest(
        "type_code_scope_solo",
        args=[Code("function() {}", {"x": 1})],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Code with scope argument",
    ),
    ConcatTest(
        "type_binary_uuid_solo",
        args=[Binary(b"data", 4)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject binary UUID argument",
    ),
    # Invalid value after a valid string.
    ConcatTest(
        "type_array_after_string",
        args=["hello", ["a"]],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject array after valid string",
    ),
    ConcatTest(
        "type_binary_after_string",
        args=["hello", Binary(b"data")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject binary after valid string",
    ),
    ConcatTest(
        "type_bool_after_string",
        args=["hello", True],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject boolean after valid string",
    ),
    ConcatTest(
        "type_date_after_string",
        args=["hello", datetime(2024, 1, 1, tzinfo=timezone.utc)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject datetime after valid string",
    ),
    ConcatTest(
        "type_decimal128_after_string",
        args=["hello", DECIMAL128_ONE_AND_HALF],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Decimal128 after valid string",
    ),
    ConcatTest(
        "type_float_after_string",
        args=["hello", 3.14],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject float after valid string",
    ),
    ConcatTest(
        "type_int_after_string",
        args=["hello", 42],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject int after valid string",
    ),
    ConcatTest(
        "type_long_after_string",
        args=["hello", Int64(42)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Int64 after valid string",
    ),
    ConcatTest(
        "type_maxkey_after_string",
        args=["hello", MaxKey()],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject MaxKey after valid string",
    ),
    ConcatTest(
        "type_minkey_after_string",
        args=["hello", MinKey()],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject MinKey after valid string",
    ),
    ConcatTest(
        "type_object_after_string",
        args=["hello", {"a": 1}],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject object after valid string",
    ),
    ConcatTest(
        "type_objectid_after_string",
        args=["hello", ObjectId("507f1f77bcf86cd799439011")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject ObjectId after valid string",
    ),
    ConcatTest(
        "type_regex_after_string",
        args=["hello", Regex("pattern")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject regex after valid string",
    ),
    ConcatTest(
        "type_timestamp_after_string",
        args=["hello", Timestamp(1, 1)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Timestamp after valid string",
    ),
    ConcatTest(
        "type_code_after_string",
        args=["hello", Code("function() {}")],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Code after valid string",
    ),
    ConcatTest(
        "type_code_scope_after_string",
        args=["hello", Code("function() {}", {"x": 1})],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Code with scope after valid string",
    ),
    ConcatTest(
        "type_binary_uuid_after_string",
        args=["hello", Binary(b"data", 4)],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject binary UUID after valid string",
    ),
    # Invalid value before a valid string.
    ConcatTest(
        "type_array_before_string",
        args=[["a"], "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject array before valid string",
    ),
    ConcatTest(
        "type_binary_before_string",
        args=[Binary(b"data"), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject binary before valid string",
    ),
    ConcatTest(
        "type_bool_before_string",
        args=[True, "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject boolean before valid string",
    ),
    ConcatTest(
        "type_date_before_string",
        args=[datetime(2024, 1, 1, tzinfo=timezone.utc), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject datetime before valid string",
    ),
    ConcatTest(
        "type_decimal128_before_string",
        args=[DECIMAL128_ONE_AND_HALF, "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Decimal128 before valid string",
    ),
    ConcatTest(
        "type_float_before_string",
        args=[3.14, "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject float before valid string",
    ),
    ConcatTest(
        "type_int_before_string",
        args=[42, "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject int before valid string",
    ),
    ConcatTest(
        "type_long_before_string",
        args=[Int64(42), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Int64 before valid string",
    ),
    ConcatTest(
        "type_maxkey_before_string",
        args=[MaxKey(), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject MaxKey before valid string",
    ),
    ConcatTest(
        "type_minkey_before_string",
        args=[MinKey(), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject MinKey before valid string",
    ),
    ConcatTest(
        "type_object_before_string",
        args=[{"a": 1}, "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject object before valid string",
    ),
    ConcatTest(
        "type_objectid_before_string",
        args=[ObjectId("507f1f77bcf86cd799439011"), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject ObjectId before valid string",
    ),
    ConcatTest(
        "type_regex_before_string",
        args=[Regex("pattern"), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject regex before valid string",
    ),
    ConcatTest(
        "type_timestamp_before_string",
        args=[Timestamp(1, 1), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Timestamp before valid string",
    ),
    ConcatTest(
        "type_code_before_string",
        args=[Code("function() {}"), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Code before valid string",
    ),
    ConcatTest(
        "type_code_scope_before_string",
        args=[Code("function() {}", {"x": 1}), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject Code with scope before valid string",
    ),
    ConcatTest(
        "type_binary_uuid_before_string",
        args=[Binary(b"data", 4), "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject binary UUID before valid string",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_TYPE_ERROR_TESTS))
def test_concat_type_error_cases(collection, test_case: ConcatTest):
    """Test $concat type error cases."""
    result = execute_expression(collection, {"$concat": test_case.args})
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
