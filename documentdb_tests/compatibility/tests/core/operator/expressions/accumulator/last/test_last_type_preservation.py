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

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.last.utils.last_common import (  # noqa: E501
    LastTest,
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

# Property [Element Type Preservation]: $last preserves the BSON type of the
# last element exactly, including numeric boundary values.
LAST_TYPE_TESTS: list[LastTest] = [
    # Each array has a leading element of a different BSON type so that
    # returning the first element instead of the last would cause a type mismatch.
    LastTest(
        "type_int32",
        value="$arr",
        document={"arr": ["first", 42]},
        expected="int",
        msg="$last should preserve int32 type",
    ),
    LastTest(
        "type_int64",
        value="$arr",
        document={"arr": ["first", Int64(42)]},
        expected="long",
        msg="$last should preserve int64 type",
    ),
    LastTest(
        "type_double",
        value="$arr",
        document={"arr": ["first", 3.14]},
        expected="double",
        msg="$last should preserve double type",
    ),
    LastTest(
        "type_decimal128",
        value="$arr",
        document={"arr": ["first", Decimal128("123.456")]},
        expected="decimal",
        msg="$last should preserve Decimal128 type",
    ),
    LastTest(
        "type_string",
        value="$arr",
        document={"arr": [0, "hello"]},
        expected="string",
        msg="$last should preserve string type",
    ),
    LastTest(
        "type_boolean",
        value="$arr",
        document={"arr": ["first", True]},
        expected="bool",
        msg="$last should preserve boolean type",
    ),
    LastTest(
        "type_null",
        value="$arr",
        document={"arr": ["first", None]},
        expected="null",
        msg="$last should preserve null type",
    ),
    LastTest(
        "type_object",
        value="$arr",
        document={"arr": ["first", {"a": 1}]},
        expected="object",
        msg="$last should preserve object type",
    ),
    LastTest(
        "type_array",
        value="$arr",
        document={"arr": ["first", [1, 2]]},
        expected="array",
        msg="$last should preserve array type",
    ),
    LastTest(
        "type_objectid",
        value="$arr",
        document={"arr": ["first", ObjectId("507f1f77bcf86cd799439011")]},
        expected="objectId",
        msg="$last should preserve ObjectId type",
    ),
    LastTest(
        "type_datetime",
        value="$arr",
        document={"arr": ["first", datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        expected="date",
        msg="$last should preserve datetime type",
    ),
    LastTest(
        "type_timestamp",
        value="$arr",
        document={"arr": ["first", Timestamp(1234567890, 1)]},
        expected="timestamp",
        msg="$last should preserve Timestamp type",
    ),
    LastTest(
        "type_binary",
        value="$arr",
        document={"arr": ["first", Binary(b"\x01\x02\x03")]},
        expected="binData",
        msg="$last should preserve Binary type",
    ),
    LastTest(
        "type_regex",
        value="$arr",
        document={"arr": ["first", Regex("^abc", "i")]},
        expected="regex",
        msg="$last should preserve Regex type",
    ),
    LastTest(
        "type_code",
        value="$arr",
        document={"arr": ["first", Code("function() {}")]},
        expected="javascript",
        msg="$last should preserve Code type",
    ),
    LastTest(
        "type_code_with_scope",
        value="$arr",
        document={"arr": ["first", Code("function() {}", {"x": 1})]},
        expected="javascriptWithScope",
        msg="$last should preserve CodeWithScope type",
    ),
    LastTest(
        "type_minkey",
        value="$arr",
        document={"arr": ["first", MinKey()]},
        expected="minKey",
        msg="$last should preserve MinKey type",
    ),
    LastTest(
        "type_maxkey",
        value="$arr",
        document={"arr": ["first", MaxKey()]},
        expected="maxKey",
        msg="$last should preserve MaxKey type",
    ),
    LastTest(
        "type_double_min",
        value="$arr",
        document={"arr": ["first", DOUBLE_MIN_SUBNORMAL]},
        expected="double",
        msg="$last should preserve double smallest positive value",
    ),
    LastTest(
        "type_double_nan",
        value="$arr",
        document={"arr": ["first", FLOAT_NAN]},
        expected="double",
        msg="$last should preserve double NaN",
    ),
    LastTest(
        "type_double_pos_inf",
        value="$arr",
        document={"arr": ["first", FLOAT_INFINITY]},
        expected="double",
        msg="$last should preserve double positive infinity",
    ),
    LastTest(
        "type_double_neg_zero",
        value="$arr",
        document={"arr": ["first", DOUBLE_NEGATIVE_ZERO]},
        expected="double",
        msg="$last should preserve double negative zero",
    ),
    LastTest(
        "type_decimal128_nan",
        value="$arr",
        document={"arr": ["first", DECIMAL128_NAN]},
        expected="decimal",
        msg="$last should preserve Decimal128 NaN",
    ),
    LastTest(
        "type_decimal128_inf",
        value="$arr",
        document={"arr": ["first", DECIMAL128_INFINITY]},
        expected="decimal",
        msg="$last should preserve Decimal128 Infinity",
    ),
    LastTest(
        "type_decimal128_neg_zero",
        value="$arr",
        document={"arr": ["first", DECIMAL128_NEGATIVE_ZERO]},
        expected="decimal",
        msg="$last should preserve Decimal128 negative zero",
    ),
    # Timestamp(0, 0) inside an array is not replaced by the server.
    LastTest(
        "type_timestamp_zero",
        value="$arr",
        document={"arr": ["first", Timestamp(0, 0)]},
        expected="timestamp",
        msg="$last should preserve Timestamp(0, 0) without server replacement",
    ),
    LastTest(
        "type_missing",
        value="$arr",
        document={"arr": []},
        expected="missing",
        msg="$last of empty array should have BSON type missing",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LAST_TYPE_TESTS))
def test_last_element_type_preservation(collection, test_case: LastTest):
    """Test $last preserves the BSON type of the last element."""
    result = execute_project_with_insert(
        collection,
        test_case.document,
        {"typeResult": {"$type": {"$last": test_case.value}}},
    )
    assertSuccess(
        result,
        [{"typeResult": test_case.expected}],
        msg=test_case.msg,
    )
