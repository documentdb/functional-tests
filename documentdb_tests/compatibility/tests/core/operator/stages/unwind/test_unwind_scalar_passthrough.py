"""Tests for $unwind stage — non-array scalar passthrough."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

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

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Array Scalar Passthrough]: when the value at the path is a
# non-array, non-null, non-missing scalar, $unwind outputs a single document
# with the value as-is, regardless of the preserveNullAndEmptyArrays setting.
UNWIND_SCALAR_PASSTHROUGH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "scalar_bool",
        docs=[{"_id": 1, "a": True}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": True}],
        msg="$unwind should pass through bool scalar as-is",
    ),
    StageTestCase(
        "scalar_int32",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through int32 scalar as-is",
    ),
    StageTestCase(
        "scalar_int64",
        docs=[{"_id": 1, "a": Int64(999)}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Int64(999)}],
        msg="$unwind should pass through Int64 scalar as-is",
    ),
    StageTestCase(
        "scalar_double",
        docs=[{"_id": 1, "a": 3.14}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 3.14}],
        msg="$unwind should pass through double scalar as-is",
    ),
    StageTestCase(
        "scalar_decimal128",
        docs=[{"_id": 1, "a": Decimal128("9.99")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Decimal128("9.99")}],
        msg="$unwind should pass through Decimal128 scalar as-is",
    ),
    StageTestCase(
        "scalar_string",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$unwind should pass through string scalar as-is",
    ),
    StageTestCase(
        "scalar_object",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": {"x": 1}}],
        msg="$unwind should pass through embedded document scalar as-is",
    ),
    StageTestCase(
        "scalar_objectid",
        docs=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        msg="$unwind should pass through ObjectId scalar as-is",
    ),
    StageTestCase(
        "scalar_datetime",
        docs=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$unwind should pass through datetime scalar as-is",
    ),
    StageTestCase(
        "scalar_timestamp",
        docs=[{"_id": 1, "a": Timestamp(1, 1)}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Timestamp(1, 1)}],
        msg="$unwind should pass through Timestamp scalar as-is",
    ),
    StageTestCase(
        "scalar_binary",
        docs=[{"_id": 1, "a": Binary(b"\x01\x02")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": b"\x01\x02"}],
        msg="$unwind should pass through Binary scalar as-is",
    ),
    StageTestCase(
        "scalar_binary_uuid",
        docs=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            }
        ],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {
                "_id": 1,
                "a": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc")),
            }
        ],
        msg="$unwind should pass through Binary UUID scalar as-is",
    ),
    StageTestCase(
        "scalar_regex",
        docs=[{"_id": 1, "a": Regex("^a", "i")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Regex("^a", "i")}],
        msg="$unwind should pass through Regex scalar as-is",
    ),
    StageTestCase(
        "scalar_code",
        docs=[{"_id": 1, "a": Code("x")}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Code("x")}],
        msg="$unwind should pass through Code scalar as-is",
    ),
    StageTestCase(
        "scalar_code_with_scope",
        docs=[{"_id": 1, "a": Code("x", {"z": 1})}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": Code("x", {"z": 1})}],
        msg="$unwind should pass through Code with scope scalar as-is",
    ),
    StageTestCase(
        "scalar_minkey",
        docs=[{"_id": 1, "a": MinKey()}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": MinKey()}],
        msg="$unwind should pass through MinKey scalar as-is",
    ),
    StageTestCase(
        "scalar_maxkey",
        docs=[{"_id": 1, "a": MaxKey()}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="$unwind should pass through MaxKey scalar as-is",
    ),
    StageTestCase(
        "scalar_preserve_true_does_not_affect",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through scalar as-is when preserveNullAndEmptyArrays is true",
    ),
    StageTestCase(
        "scalar_preserve_false_does_not_affect",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": False}}],
        expected=[{"_id": 1, "a": 42}],
        msg="$unwind should pass through scalar as-is when preserveNullAndEmptyArrays is false",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_SCALAR_PASSTHROUGH_TESTS))
def test_unwind_scalar_passthrough(collection, test_case: StageTestCase):
    """Test $unwind non-array scalar passthrough."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
