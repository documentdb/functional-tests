from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    INDEXOF_INDEX_TYPE_ERROR,
    INDEXOFBYTES_STRING_TYPE_ERROR,
    INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF, MISSING

from .utils.indexOfBytes_common import (
    IndexOfBytesTest,
)

# Property [Type Strictness]: arguments of incorrect type produce an error.
INDEXOFBYTES_TYPE_ERROR_TESTS: list[IndexOfBytesTest] = [
    # First arg: non-string, non-null types
    IndexOfBytesTest(
        "type_first_array",
        args=[["a"], "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject array as string argument",
    ),
    IndexOfBytesTest(
        "type_first_binary",
        args=[Binary(b"data"), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject binary as string argument",
    ),
    IndexOfBytesTest(
        "type_first_bool",
        args=[True, "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject bool as string argument",
    ),
    IndexOfBytesTest(
        "type_first_date",
        args=[datetime(2024, 1, 1, tzinfo=timezone.utc), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject date as string argument",
    ),
    IndexOfBytesTest(
        "type_first_decimal128",
        args=[DECIMAL128_ONE_AND_HALF, "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject decimal128 as string argument",
    ),
    IndexOfBytesTest(
        "type_first_float",
        args=[3.14, "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject float as string argument",
    ),
    IndexOfBytesTest(
        "type_first_int",
        args=[42, "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject int as string argument",
    ),
    IndexOfBytesTest(
        "type_first_long",
        args=[Int64(42), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject long as string argument",
    ),
    IndexOfBytesTest(
        "type_first_maxkey",
        args=[MaxKey(), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject maxkey as string argument",
    ),
    IndexOfBytesTest(
        "type_first_minkey",
        args=[MinKey(), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject minkey as string argument",
    ),
    IndexOfBytesTest(
        "type_first_object",
        args=[{"a": 1}, "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject object as string argument",
    ),
    IndexOfBytesTest(
        "type_first_objectid",
        args=[ObjectId("507f1f77bcf86cd799439011"), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject objectid as string argument",
    ),
    IndexOfBytesTest(
        "type_first_regex",
        args=[Regex("pattern"), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject regex as string argument",
    ),
    IndexOfBytesTest(
        "type_first_timestamp",
        args=[Timestamp(1, 1), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject timestamp as string argument",
    ),
    IndexOfBytesTest(
        "type_first_code",
        args=[Code("function() {}"), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject javascript code as string argument",
    ),
    IndexOfBytesTest(
        "type_first_code_scope",
        args=[Code("function() {}", {"x": 1}), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject code with scope as string argument",
    ),
    IndexOfBytesTest(
        "type_first_binary_uuid",
        args=[Binary(b"data", 4), "sub"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject binary UUID as string argument",
    ),
    # Second arg: non-string types
    IndexOfBytesTest(
        "type_second_array",
        args=["hello", ["a"]],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject array as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_binary",
        args=["hello", Binary(b"data")],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject binary as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_bool",
        args=["hello", True],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject bool as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_date",
        args=["hello", datetime(2024, 1, 1, tzinfo=timezone.utc)],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject date as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_decimal128",
        args=["hello", DECIMAL128_ONE_AND_HALF],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject decimal128 as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_float",
        args=["hello", 3.14],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject float as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_int",
        args=["hello", 42],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject int as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_long",
        args=["hello", Int64(42)],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject long as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_maxkey",
        args=["hello", MaxKey()],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject maxkey as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_minkey",
        args=["hello", MinKey()],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject minkey as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_object",
        args=["hello", {"a": 1}],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject object as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_objectid",
        args=["hello", ObjectId("507f1f77bcf86cd799439011")],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject objectid as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_regex",
        args=["hello", Regex("pattern")],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject regex as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_timestamp",
        args=["hello", Timestamp(1, 1)],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject timestamp as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_code",
        args=["hello", Code("function() {}")],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject javascript code as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_code_scope",
        args=["hello", Code("function() {}", {"x": 1})],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject code with scope as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_binary_uuid",
        args=["hello", Binary(b"data", 4)],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject binary UUID as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_null",
        args=["hello", None],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject null as substring argument",
    ),
    IndexOfBytesTest(
        "type_second_missing",
        args=["hello", MISSING],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject missing field as substring argument",
    ),
    # Third arg (start): non-numeric types
    IndexOfBytesTest(
        "type_third_array",
        args=["hello", "h", ["a"]],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject array as start argument",
    ),
    IndexOfBytesTest(
        "type_third_binary",
        args=["hello", "h", Binary(b"data")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject binary as start argument",
    ),
    IndexOfBytesTest(
        "type_third_bool",
        args=["hello", "h", True],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject bool as start argument",
    ),
    IndexOfBytesTest(
        "type_third_date",
        args=["hello", "h", datetime(2024, 1, 1, tzinfo=timezone.utc)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject date as start argument",
    ),
    IndexOfBytesTest(
        "type_third_maxkey",
        args=["hello", "h", MaxKey()],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject maxkey as start argument",
    ),
    IndexOfBytesTest(
        "type_third_minkey",
        args=["hello", "h", MinKey()],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject minkey as start argument",
    ),
    IndexOfBytesTest(
        "type_third_object",
        args=["hello", "h", {"a": 1}],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject object as start argument",
    ),
    IndexOfBytesTest(
        "type_third_objectid",
        args=["hello", "h", ObjectId("507f1f77bcf86cd799439011")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject objectid as start argument",
    ),
    IndexOfBytesTest(
        "type_third_regex",
        args=["hello", "h", Regex("pattern")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject regex as start argument",
    ),
    IndexOfBytesTest(
        "type_third_timestamp",
        args=["hello", "h", Timestamp(1, 1)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject timestamp as start argument",
    ),
    IndexOfBytesTest(
        "type_third_code",
        args=["hello", "h", Code("function() {}")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject javascript code as start argument",
    ),
    IndexOfBytesTest(
        "type_third_code_scope",
        args=["hello", "h", Code("function() {}", {"x": 1})],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject code with scope as start argument",
    ),
    IndexOfBytesTest(
        "type_third_binary_uuid",
        args=["hello", "h", Binary(b"data", 4)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject binary UUID as start argument",
    ),
    IndexOfBytesTest(
        "type_third_string",
        args=["hello", "h", "x"],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject string as start argument",
    ),
    IndexOfBytesTest(
        "type_third_null",
        args=["hello", "h", None],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject null as start argument",
    ),
    IndexOfBytesTest(
        "type_third_missing",
        args=["hello", "h", MISSING],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject missing field as start argument",
    ),
    # Fourth arg (end): non-numeric types
    IndexOfBytesTest(
        "type_fourth_array",
        args=["hello", "h", 0, ["a"]],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject array as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_binary",
        args=["hello", "h", 0, Binary(b"data")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject binary as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_bool",
        args=["hello", "h", 0, True],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject bool as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_date",
        args=["hello", "h", 0, datetime(2024, 1, 1, tzinfo=timezone.utc)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject date as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_maxkey",
        args=["hello", "h", 0, MaxKey()],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject maxkey as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_minkey",
        args=["hello", "h", 0, MinKey()],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject minkey as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_object",
        args=["hello", "h", 0, {"a": 1}],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject object as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_objectid",
        args=["hello", "h", 0, ObjectId("507f1f77bcf86cd799439011")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject objectid as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_regex",
        args=["hello", "h", 0, Regex("pattern")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject regex as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_timestamp",
        args=["hello", "h", 0, Timestamp(1, 1)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject timestamp as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_code",
        args=["hello", "h", 0, Code("function() {}")],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject javascript code as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_code_scope",
        args=["hello", "h", 0, Code("function() {}", {"x": 1})],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject code with scope as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_binary_uuid",
        args=["hello", "h", 0, Binary(b"data", 4)],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject binary UUID as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_string",
        args=["hello", "h", 0, "x"],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject string as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_null",
        args=["hello", "h", 0, None],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject null as end argument",
    ),
    IndexOfBytesTest(
        "type_fourth_missing",
        args=["hello", "h", 0, MISSING],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject missing field as end argument",
    ),
    # Non-integral floats and decimals are rejected as index arguments even though
    # whole-number values of these types are accepted (see INDEXOFBYTES_INDEX_TYPE_TESTS).
    IndexOfBytesTest(
        "type_third_non_integral_float",
        args=["hello", "h", 3.14],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject non-integral float as start",
    ),
    IndexOfBytesTest(
        "type_third_non_integral_decimal128",
        args=["hello", "h", DECIMAL128_ONE_AND_HALF],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject non-integral Decimal128 as start",
    ),
    IndexOfBytesTest(
        "type_fourth_non_integral_float",
        args=["hello", "h", 0, 3.14],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject non-integral float as end",
    ),
    IndexOfBytesTest(
        "type_fourth_non_integral_decimal128",
        args=["hello", "h", 0, DECIMAL128_ONE_AND_HALF],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject non-integral Decimal128 as end",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFBYTES_TYPE_ERROR_TESTS))
def test_indexofbytes_cases(collection, test_case: IndexOfBytesTest):
    """Test $indexOfBytes cases."""
    result = execute_expression(collection, {"$indexOfBytes": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
