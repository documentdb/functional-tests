"""Tests that $project preserves all BSON types through each projection mode."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Type Inclusion]: each BSON type is preserved unchanged
# when the field is explicitly included.
PROJECT_BSON_INCLUSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "inclusion_null",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": None}],
        msg="$project inclusion should preserve null",
    ),
    StageTestCase(
        "inclusion_string",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": "hello"}],
        msg="$project inclusion should preserve string",
    ),
    StageTestCase(
        "inclusion_int32",
        docs=[{"_id": 1, "v": 42}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": 42}],
        msg="$project inclusion should preserve int32",
    ),
    StageTestCase(
        "inclusion_int64",
        docs=[{"_id": 1, "v": Int64(123_456_789_012_345)}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": Int64(123_456_789_012_345)}],
        msg="$project inclusion should preserve int64",
    ),
    StageTestCase(
        "inclusion_double",
        docs=[{"_id": 1, "v": 3.14}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": 3.14}],
        msg="$project inclusion should preserve double",
    ),
    StageTestCase(
        "inclusion_decimal128",
        docs=[{"_id": 1, "v": Decimal128("1.23")}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": Decimal128("1.23")}],
        msg="$project inclusion should preserve Decimal128",
    ),
    StageTestCase(
        "inclusion_bool",
        docs=[{"_id": 1, "v": True}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": True}],
        msg="$project inclusion should preserve bool",
    ),
    StageTestCase(
        "inclusion_array",
        docs=[{"_id": 1, "v": [1, 2, 3]}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": [1, 2, 3]}],
        msg="$project inclusion should preserve array",
    ),
    StageTestCase(
        "inclusion_object",
        docs=[{"_id": 1, "v": {"nested": "doc"}}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": {"nested": "doc"}}],
        msg="$project inclusion should preserve object",
    ),
    StageTestCase(
        "inclusion_objectid",
        docs=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$project inclusion should preserve ObjectId",
    ),
    StageTestCase(
        "inclusion_datetime",
        docs=[{"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": datetime(2024, 1, 1)}],
        msg="$project inclusion should preserve datetime",
    ),
    StageTestCase(
        "inclusion_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1_234_567_890, 1)}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": Timestamp(1_234_567_890, 1)}],
        msg="$project inclusion should preserve Timestamp",
    ),
    StageTestCase(
        "inclusion_binary",
        docs=[{"_id": 1, "v": Binary(b"hello")}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": b"hello"}],
        msg="$project inclusion should preserve Binary",
    ),
    StageTestCase(
        "inclusion_regex",
        docs=[{"_id": 1, "v": Regex("abc", "i")}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": Regex("abc", "i")}],
        msg="$project inclusion should preserve Regex",
    ),
    StageTestCase(
        "inclusion_code",
        docs=[{"_id": 1, "v": Code("function() {}")}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": Code("function() {}")}],
        msg="$project inclusion should preserve Code",
    ),
    StageTestCase(
        "inclusion_code_with_scope",
        docs=[{"_id": 1, "v": Code("function() { return x; }", {"x": 1})}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": Code("function() { return x; }", {"x": 1})}],
        msg="$project inclusion should preserve CodeWithScope",
    ),
    StageTestCase(
        "inclusion_minkey",
        docs=[{"_id": 1, "v": MinKey()}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": MinKey()}],
        msg="$project inclusion should preserve MinKey",
    ),
    StageTestCase(
        "inclusion_maxkey",
        docs=[{"_id": 1, "v": MaxKey()}],
        pipeline=[{"$project": {"v": 1}}],
        expected=[{"_id": 1, "v": MaxKey()}],
        msg="$project inclusion should preserve MaxKey",
    ),
]

# Property [BSON Type Exclusion]: each BSON type is preserved unchanged
# when a different field is excluded.
PROJECT_BSON_EXCLUSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "exclusion_null",
        docs=[{"_id": 1, "v": None, "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": None}],
        msg="$project exclusion should preserve null",
    ),
    StageTestCase(
        "exclusion_string",
        docs=[{"_id": 1, "v": "hello", "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": "hello"}],
        msg="$project exclusion should preserve string",
    ),
    StageTestCase(
        "exclusion_int32",
        docs=[{"_id": 1, "v": 42, "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": 42}],
        msg="$project exclusion should preserve int32",
    ),
    StageTestCase(
        "exclusion_int64",
        docs=[{"_id": 1, "v": Int64(123_456_789_012_345), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": Int64(123_456_789_012_345)}],
        msg="$project exclusion should preserve int64",
    ),
    StageTestCase(
        "exclusion_double",
        docs=[{"_id": 1, "v": 3.14, "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": 3.14}],
        msg="$project exclusion should preserve double",
    ),
    StageTestCase(
        "exclusion_decimal128",
        docs=[{"_id": 1, "v": Decimal128("1.23"), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": Decimal128("1.23")}],
        msg="$project exclusion should preserve Decimal128",
    ),
    StageTestCase(
        "exclusion_bool",
        docs=[{"_id": 1, "v": True, "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": True}],
        msg="$project exclusion should preserve bool",
    ),
    StageTestCase(
        "exclusion_array",
        docs=[{"_id": 1, "v": [1, 2, 3], "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": [1, 2, 3]}],
        msg="$project exclusion should preserve array",
    ),
    StageTestCase(
        "exclusion_object",
        docs=[{"_id": 1, "v": {"nested": "doc"}, "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": {"nested": "doc"}}],
        msg="$project exclusion should preserve object",
    ),
    StageTestCase(
        "exclusion_objectid",
        docs=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011"), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$project exclusion should preserve ObjectId",
    ),
    StageTestCase(
        "exclusion_datetime",
        docs=[{"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": datetime(2024, 1, 1)}],
        msg="$project exclusion should preserve datetime",
    ),
    StageTestCase(
        "exclusion_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1_234_567_890, 1), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": Timestamp(1_234_567_890, 1)}],
        msg="$project exclusion should preserve Timestamp",
    ),
    StageTestCase(
        "exclusion_binary",
        docs=[{"_id": 1, "v": Binary(b"hello"), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": b"hello"}],
        msg="$project exclusion should preserve Binary",
    ),
    StageTestCase(
        "exclusion_regex",
        docs=[{"_id": 1, "v": Regex("abc", "i"), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": Regex("abc", "i")}],
        msg="$project exclusion should preserve Regex",
    ),
    StageTestCase(
        "exclusion_code",
        docs=[{"_id": 1, "v": Code("function() {}"), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": Code("function() {}")}],
        msg="$project exclusion should preserve Code",
    ),
    StageTestCase(
        "exclusion_code_with_scope",
        docs=[{"_id": 1, "v": Code("function() { return x; }", {"x": 1}), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": Code("function() { return x; }", {"x": 1})}],
        msg="$project exclusion should preserve CodeWithScope",
    ),
    StageTestCase(
        "exclusion_minkey",
        docs=[{"_id": 1, "v": MinKey(), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": MinKey()}],
        msg="$project exclusion should preserve MinKey",
    ),
    StageTestCase(
        "exclusion_maxkey",
        docs=[{"_id": 1, "v": MaxKey(), "x": 0}],
        pipeline=[{"$project": {"x": 0}}],
        expected=[{"_id": 1, "v": MaxKey()}],
        msg="$project exclusion should preserve MaxKey",
    ),
]

# Property [BSON Type Field Path Reference]: each BSON type is preserved
# unchanged when copied via a field path expression.
PROJECT_BSON_FIELD_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_path_null",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": None}],
        msg="$project field path should preserve null",
    ),
    StageTestCase(
        "field_path_string",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": "hello"}],
        msg="$project field path should preserve string",
    ),
    StageTestCase(
        "field_path_int32",
        docs=[{"_id": 1, "v": 42}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": 42}],
        msg="$project field path should preserve int32",
    ),
    StageTestCase(
        "field_path_int64",
        docs=[{"_id": 1, "v": Int64(123_456_789_012_345)}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": Int64(123_456_789_012_345)}],
        msg="$project field path should preserve int64",
    ),
    StageTestCase(
        "field_path_double",
        docs=[{"_id": 1, "v": 3.14}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": 3.14}],
        msg="$project field path should preserve double",
    ),
    StageTestCase(
        "field_path_decimal128",
        docs=[{"_id": 1, "v": Decimal128("1.23")}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": Decimal128("1.23")}],
        msg="$project field path should preserve Decimal128",
    ),
    StageTestCase(
        "field_path_bool",
        docs=[{"_id": 1, "v": True}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": True}],
        msg="$project field path should preserve bool",
    ),
    StageTestCase(
        "field_path_array",
        docs=[{"_id": 1, "v": [1, 2, 3]}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": [1, 2, 3]}],
        msg="$project field path should preserve array",
    ),
    StageTestCase(
        "field_path_object",
        docs=[{"_id": 1, "v": {"nested": "doc"}}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": {"nested": "doc"}}],
        msg="$project field path should preserve object",
    ),
    StageTestCase(
        "field_path_objectid",
        docs=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$project field path should preserve ObjectId",
    ),
    StageTestCase(
        "field_path_datetime",
        docs=[{"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": datetime(2024, 1, 1)}],
        msg="$project field path should preserve datetime",
    ),
    StageTestCase(
        "field_path_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1_234_567_890, 1)}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": Timestamp(1_234_567_890, 1)}],
        msg="$project field path should preserve Timestamp",
    ),
    StageTestCase(
        "field_path_binary",
        docs=[{"_id": 1, "v": Binary(b"hello")}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": b"hello"}],
        msg="$project field path should preserve Binary",
    ),
    StageTestCase(
        "field_path_regex",
        docs=[{"_id": 1, "v": Regex("abc", "i")}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": Regex("abc", "i")}],
        msg="$project field path should preserve Regex",
    ),
    StageTestCase(
        "field_path_code",
        docs=[{"_id": 1, "v": Code("function() {}")}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": Code("function() {}")}],
        msg="$project field path should preserve Code",
    ),
    StageTestCase(
        "field_path_code_with_scope",
        docs=[{"_id": 1, "v": Code("function() { return x; }", {"x": 1})}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": Code("function() { return x; }", {"x": 1})}],
        msg="$project field path should preserve CodeWithScope",
    ),
    StageTestCase(
        "field_path_minkey",
        docs=[{"_id": 1, "v": MinKey()}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": MinKey()}],
        msg="$project field path should preserve MinKey",
    ),
    StageTestCase(
        "field_path_maxkey",
        docs=[{"_id": 1, "v": MaxKey()}],
        pipeline=[{"$project": {"r": "$v"}}],
        expected=[{"_id": 1, "r": MaxKey()}],
        msg="$project field path should preserve MaxKey",
    ),
]

PROJECT_BSON_TYPE_TESTS = (
    PROJECT_BSON_INCLUSION_TESTS + PROJECT_BSON_EXCLUSION_TESTS + PROJECT_BSON_FIELD_PATH_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(PROJECT_BSON_TYPE_TESTS))
def test_project_bson_type_cases(collection: Any, test_case: StageTestCase):
    """Test that $project preserves BSON types."""
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
