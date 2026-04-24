from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.set.utils.set_common import (
    STAGE_NAMES,
    replace_stage_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [BSON Type Pass-Through]: all BSON types are accepted as field
# values and pass through unchanged, including empty arrays, empty objects,
# nested arrays, and arrays containing null.
SET_BSON_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "bson_string",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": "hello"}}],
        expected=[{"_id": 1, "v": "hello"}],
        msg="$set should pass through a string value unchanged",
    ),
    StageTestCase(
        "bson_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": 42}}],
        expected=[{"_id": 1, "v": 42}],
        msg="$set should pass through an int32 value unchanged",
    ),
    StageTestCase(
        "bson_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Int64(9_000_000_000)}}],
        expected=[{"_id": 1, "v": Int64(9_000_000_000)}],
        msg="$set should pass through an Int64 value unchanged",
    ),
    StageTestCase(
        "bson_float",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": 3.14}}],
        expected=[{"_id": 1, "v": 3.14}],
        msg="$set should pass through a float value unchanged",
    ),
    StageTestCase(
        "bson_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": datetime(2023, 1, 15)}}],
        expected=[{"_id": 1, "v": datetime(2023, 1, 15)}],
        msg="$set should pass through a datetime value unchanged",
    ),
    StageTestCase(
        "bson_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": ObjectId("507f1f77bcf86cd799439011")}}],
        expected=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$set should pass through an ObjectId value unchanged",
    ),
    StageTestCase(
        "bson_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Decimal128("123.456")}}],
        expected=[{"_id": 1, "v": Decimal128("123.456")}],
        msg="$set should pass through a Decimal128 value unchanged",
    ),
    StageTestCase(
        "bson_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": b"\x01\x02\x03"}}],
        expected=[{"_id": 1, "v": b"\x01\x02\x03"}],
        msg="$set should pass through a binary value unchanged",
    ),
    StageTestCase(
        "bson_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Regex("abc", "i")}}],
        expected=[{"_id": 1, "v": Regex("abc", "i")}],
        msg="$set should pass through a Regex value unchanged",
    ),
    StageTestCase(
        "bson_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Timestamp(1234567890, 1)}}],
        expected=[{"_id": 1, "v": Timestamp(1234567890, 1)}],
        msg="$set should pass through a Timestamp value unchanged",
    ),
    StageTestCase(
        "bson_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": MaxKey()}}],
        expected=[{"_id": 1, "v": MaxKey()}],
        msg="$set should pass through a MaxKey value unchanged",
    ),
    StageTestCase(
        "bson_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": MinKey()}}],
        expected=[{"_id": 1, "v": MinKey()}],
        msg="$set should pass through a MinKey value unchanged",
    ),
    StageTestCase(
        "bson_code",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Code("function() {}")}}],
        expected=[{"_id": 1, "v": Code("function() {}")}],
        msg="$set should pass through a JavaScript code value unchanged",
    ),
    StageTestCase(
        "bson_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Code("function() {}", {"x": 1})}}],
        expected=[{"_id": 1, "v": Code("function() {}", {"x": 1})}],
        msg="$set should pass through a JavaScript code with scope value unchanged",
    ),
    StageTestCase(
        "bson_array",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": {"$literal": [1, "two", 3.0]}}}],
        expected=[{"_id": 1, "v": [1, "two", 3.0]}],
        msg="$set should pass through an array value unchanged",
    ),
    StageTestCase(
        "bson_empty_array",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": {"$literal": []}}}],
        expected=[{"_id": 1, "v": []}],
        msg="$set should pass through an empty array unchanged",
    ),
    StageTestCase(
        "bson_nested_array",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": {"$literal": [[1, 2], [3, 4]]}}}],
        expected=[{"_id": 1, "v": [[1, 2], [3, 4]]}],
        msg="$set should pass through a nested array unchanged",
    ),
    StageTestCase(
        "bson_array_with_null",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": {"$literal": [1, None, 3]}}}],
        expected=[{"_id": 1, "v": [1, None, 3]}],
        msg="$set should pass through an array containing null unchanged",
    ),
    StageTestCase(
        "bson_empty_object",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": {"$literal": {}}}}],
        expected=[{"_id": 1, "v": {}}],
        msg="$set should pass through an empty object unchanged",
    ),
    StageTestCase(
        "bson_bool_true",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": True}}],
        expected=[{"_id": 1, "v": True}],
        msg="$set should pass through a boolean true value unchanged",
    ),
    StageTestCase(
        "bson_bool_false",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": False}}],
        expected=[{"_id": 1, "v": False}],
        msg="$set should pass through a boolean false value unchanged",
    ),
    StageTestCase(
        "bson_none",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": None}}],
        expected=[{"_id": 1, "v": None}],
        msg="$set should pass through a null value unchanged",
    ),
    StageTestCase(
        "bson_float_nan",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": FLOAT_NAN}}],
        expected=[{"_id": 1, "v": pytest.approx(FLOAT_NAN, nan_ok=True)}],
        msg="$set should pass through NaN unchanged",
    ),
    StageTestCase(
        "bson_float_inf",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": FLOAT_INFINITY}}],
        expected=[{"_id": 1, "v": FLOAT_INFINITY}],
        msg="$set should pass through Infinity unchanged",
    ),
    StageTestCase(
        "bson_float_neg_zero",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": DOUBLE_NEGATIVE_ZERO}}],
        expected=[{"_id": 1, "v": DOUBLE_NEGATIVE_ZERO}],
        msg="$set should pass through -0.0 unchanged",
    ),
    StageTestCase(
        "bson_uuid",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc"))}}],
        expected=[{"_id": 1, "v": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc"))}],
        msg="$set should pass through a UUID value unchanged",
    ),
    StageTestCase(
        "bson_binary_subtype_5",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Binary(b"\x01\x02\x03", 5)}}],
        expected=[{"_id": 1, "v": Binary(b"\x01\x02\x03", 5)}],
        msg="$set should pass through a Binary with non-default subtype unchanged",
    ),
    StageTestCase(
        "bson_timestamp_zero",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"v": Timestamp(0, 0)}}],
        expected=[{"_id": 1, "v": Timestamp(0, 0)}],
        msg="$set should pass through Timestamp(0, 0) unchanged",
    ),
]


@pytest.mark.parametrize("stage_name", STAGE_NAMES)
@pytest.mark.parametrize("test_case", pytest_params(SET_BSON_TYPE_TESTS))
def test_set_bson_types(collection, stage_name: str, test_case: StageTestCase):
    """Test $set / $addFields BSON type pass-through cases."""
    populate_collection(collection, test_case)
    pipeline = replace_stage_name(test_case.pipeline, stage_name)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=f"{stage_name!r}: {test_case.msg!r}",
    )
