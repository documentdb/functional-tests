from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.first.utils.first_common import (  # noqa: E501
    FirstTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [Element Type Preservation]: $first preserves the BSON type and
# value of the first element exactly, including numeric boundary values.
FIRST_TYPE_TESTS: list[FirstTest] = [
    # Each array has a trailing element of a different BSON type so that
    # returning the last element instead of the first would cause a type mismatch.
    FirstTest(
        "type_int32",
        value="$arr",
        document={"arr": [42, "last"]},
        expected="int",
        msg="$first should preserve int32 type",
    ),
    FirstTest(
        "type_int64",
        value="$arr",
        document={"arr": [Int64(42), "last"]},
        expected="long",
        msg="$first should preserve int64 type",
    ),
    FirstTest(
        "type_double",
        value="$arr",
        document={"arr": [3.14, "last"]},
        expected="double",
        msg="$first should preserve double type",
    ),
    FirstTest(
        "type_decimal128",
        value="$arr",
        document={"arr": [Decimal128("123.456"), "last"]},
        expected="decimal",
        msg="$first should preserve Decimal128 type",
    ),
    FirstTest(
        "type_string",
        value="$arr",
        document={"arr": ["hello", 0]},
        expected="string",
        msg="$first should preserve string type",
    ),
    FirstTest(
        "type_boolean",
        value="$arr",
        document={"arr": [True, "last"]},
        expected="bool",
        msg="$first should preserve boolean type",
    ),
    FirstTest(
        "type_null",
        value="$arr",
        document={"arr": [None, "last"]},
        expected="null",
        msg="$first should preserve null type",
    ),
    FirstTest(
        "type_object",
        value="$arr",
        document={"arr": [{"a": 1}, "last"]},
        expected="object",
        msg="$first should preserve object type",
    ),
    FirstTest(
        "type_array",
        value="$arr",
        document={"arr": [[1, 2], "last"]},
        expected="array",
        msg="$first should preserve array type",
    ),
    FirstTest(
        "type_objectid",
        value="$arr",
        document={"arr": [ObjectId("507f1f77bcf86cd799439011"), "last"]},
        expected="objectId",
        msg="$first should preserve ObjectId type",
    ),
    FirstTest(
        "type_datetime",
        value="$arr",
        document={"arr": [datetime(2024, 1, 1, tzinfo=timezone.utc), "last"]},
        expected="date",
        msg="$first should preserve datetime type",
    ),
    FirstTest(
        "type_timestamp",
        value="$arr",
        document={"arr": [Timestamp(1234567890, 1), "last"]},
        expected="timestamp",
        msg="$first should preserve Timestamp type",
    ),
    FirstTest(
        "type_binary",
        value="$arr",
        document={"arr": [Binary(b"\x01\x02\x03"), "last"]},
        expected="binData",
        msg="$first should preserve Binary type",
    ),
    FirstTest(
        "type_regex",
        value="$arr",
        document={"arr": [Regex("^abc", "i"), "last"]},
        expected="regex",
        msg="$first should preserve Regex type",
    ),
    FirstTest(
        "type_code",
        value="$arr",
        document={"arr": [Code("function() {}"), "last"]},
        expected="javascript",
        msg="$first should preserve Code type",
    ),
    FirstTest(
        "type_code_with_scope",
        value="$arr",
        document={"arr": [Code("function() {}", {"x": 1}), "last"]},
        expected="javascriptWithScope",
        msg="$first should preserve CodeWithScope type",
    ),
    FirstTest(
        "type_minkey",
        value="$arr",
        document={"arr": [MinKey(), "last"]},
        expected="minKey",
        msg="$first should preserve MinKey type",
    ),
    FirstTest(
        "type_maxkey",
        value="$arr",
        document={"arr": [MaxKey(), "last"]},
        expected="maxKey",
        msg="$first should preserve MaxKey type",
    ),
    FirstTest(
        "type_double_min",
        value="$arr",
        document={"arr": [DOUBLE_MIN_SUBNORMAL, "last"]},
        expected="double",
        msg="$first should preserve double smallest positive value",
    ),
    FirstTest(
        "type_double_nan",
        value="$arr",
        document={"arr": [FLOAT_NAN, "last"]},
        expected="double",
        msg="$first should preserve double NaN",
    ),
    FirstTest(
        "type_double_pos_inf",
        value="$arr",
        document={"arr": [FLOAT_INFINITY, "last"]},
        expected="double",
        msg="$first should preserve double positive infinity",
    ),
    FirstTest(
        "type_double_neg_zero",
        value="$arr",
        document={"arr": [DOUBLE_NEGATIVE_ZERO, "last"]},
        expected="double",
        msg="$first should preserve double negative zero",
    ),
    FirstTest(
        "type_decimal128_nan",
        value="$arr",
        document={"arr": [DECIMAL128_NAN, "last"]},
        expected="decimal",
        msg="$first should preserve Decimal128 NaN",
    ),
    FirstTest(
        "type_decimal128_inf",
        value="$arr",
        document={"arr": [DECIMAL128_INFINITY, "last"]},
        expected="decimal",
        msg="$first should preserve Decimal128 Infinity",
    ),
    FirstTest(
        "type_decimal128_neg_zero",
        value="$arr",
        document={"arr": [DECIMAL128_NEGATIVE_ZERO, "last"]},
        expected="decimal",
        msg="$first should preserve Decimal128 negative zero",
    ),
    # Timestamp(0, 0) inside an array is not replaced by the server.
    FirstTest(
        "type_timestamp_zero",
        value="$arr",
        document={"arr": [Timestamp(0, 0), "last"]},
        expected="timestamp",
        msg="$first should preserve Timestamp(0, 0) without server replacement",
    ),
    FirstTest(
        "type_missing",
        value="$arr",
        document={"arr": []},
        expected="missing",
        msg="$first of empty array should have BSON type missing",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(FIRST_TYPE_TESTS))
def test_first_element_type_preservation(collection, test_case: FirstTest):
    """Test $first preserves the BSON type of the first element."""
    result = execute_project_with_insert(
        collection,
        test_case.document,
        {"typeResult": {"$type": {"$first": test_case.value}}},
    )
    assertSuccess(
        result,
        [{"typeResult": test_case.expected}],
        msg=test_case.msg,
    )
