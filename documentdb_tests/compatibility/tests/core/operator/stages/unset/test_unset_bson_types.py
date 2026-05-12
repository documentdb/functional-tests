"""Tests for $unset stage BSON type handling."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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

# Property [BSON Type Independence]: field removal succeeds regardless of the
# BSON type of the field's value.
UNSET_BSON_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "bson_double",
        docs=[{"_id": 1, "v": 3.14}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with double value",
    ),
    StageTestCase(
        "bson_string",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with string value",
    ),
    StageTestCase(
        "bson_document",
        docs=[{"_id": 1, "v": {"a": 1}}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with embedded document value",
    ),
    StageTestCase(
        "bson_array",
        docs=[{"_id": 1, "v": [1, 2, 3]}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with array value",
    ),
    StageTestCase(
        "bson_null",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with null value",
    ),
    StageTestCase(
        "bson_int32",
        docs=[{"_id": 1, "v": 42}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with int32 value",
    ),
    StageTestCase(
        "bson_objectid",
        docs=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with ObjectId value",
    ),
    StageTestCase(
        "bson_datetime",
        docs=[{"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with datetime value",
    ),
    StageTestCase(
        "bson_binary",
        docs=[{"_id": 1, "v": Binary(b"\x01\x02\x03")}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with Binary value",
    ),
    StageTestCase(
        "bson_regex",
        docs=[{"_id": 1, "v": Regex("^abc", "i")}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with Regex value",
    ),
    StageTestCase(
        "bson_bool",
        docs=[{"_id": 1, "v": True}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with bool value",
    ),
    StageTestCase(
        "bson_int64",
        docs=[{"_id": 1, "v": Int64(9_999_999_999)}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with Int64 value",
    ),
    StageTestCase(
        "bson_decimal128",
        docs=[{"_id": 1, "v": Decimal128("123.456")}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with Decimal128 value",
    ),
    StageTestCase(
        "bson_minkey",
        docs=[{"_id": 1, "v": MinKey()}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with MinKey value",
    ),
    StageTestCase(
        "bson_maxkey",
        docs=[{"_id": 1, "v": MaxKey()}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with MaxKey value",
    ),
    StageTestCase(
        "bson_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1_700_000_000, 1)}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with Timestamp value",
    ),
    StageTestCase(
        "bson_code",
        docs=[{"_id": 1, "v": Code("function(){}")}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with Code value",
    ),
    StageTestCase(
        "bson_code_with_scope",
        docs=[{"_id": 1, "v": Code("function(){}", {"x": 1})}],
        pipeline=[{"$unset": "v"}],
        expected=[{"_id": 1}],
        msg="$unset should remove a field with CodeWithScope value",
    ),
]

# Property [BSON Type Preservation]: unspecified fields retain their original
# value and type after $unset removes a different field.
UNSET_BSON_TYPE_PRESERVATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "preserve_double",
        docs=[{"_id": 1, "v": 3.14, "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": 3.14}],
        msg="$unset should preserve a double field unchanged",
    ),
    StageTestCase(
        "preserve_string",
        docs=[{"_id": 1, "v": "hello", "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": "hello"}],
        msg="$unset should preserve a string field unchanged",
    ),
    StageTestCase(
        "preserve_document",
        docs=[{"_id": 1, "v": {"a": 1}, "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": {"a": 1}}],
        msg="$unset should preserve an embedded document field unchanged",
    ),
    StageTestCase(
        "preserve_array",
        docs=[{"_id": 1, "v": [1, 2, 3], "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": [1, 2, 3]}],
        msg="$unset should preserve an array field unchanged",
    ),
    StageTestCase(
        "preserve_null",
        docs=[{"_id": 1, "v": None, "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": None}],
        msg="$unset should preserve a null field unchanged",
    ),
    StageTestCase(
        "preserve_bool",
        docs=[{"_id": 1, "v": True, "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": True}],
        msg="$unset should preserve a bool field unchanged",
    ),
    StageTestCase(
        "preserve_int32",
        docs=[{"_id": 1, "v": 42, "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": 42}],
        msg="$unset should preserve an int32 field unchanged",
    ),
    StageTestCase(
        "preserve_int64",
        docs=[{"_id": 1, "v": Int64(9_999_999_999), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": Int64(9_999_999_999)}],
        msg="$unset should preserve an Int64 field unchanged",
    ),
    StageTestCase(
        "preserve_decimal128",
        docs=[{"_id": 1, "v": Decimal128("123.456"), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": Decimal128("123.456")}],
        msg="$unset should preserve a Decimal128 field unchanged",
    ),
    StageTestCase(
        "preserve_objectid",
        docs=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011"), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$unset should preserve an ObjectId field unchanged",
    ),
    StageTestCase(
        "preserve_datetime",
        docs=[{"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$unset should preserve a datetime field unchanged",
    ),
    StageTestCase(
        "preserve_binary",
        docs=[{"_id": 1, "v": Binary(b"\x01\x02\x03"), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": b"\x01\x02\x03"}],
        msg="$unset should preserve a Binary field unchanged",
    ),
    StageTestCase(
        "preserve_regex",
        docs=[{"_id": 1, "v": Regex("^abc", "i"), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": Regex("^abc", "i")}],
        msg="$unset should preserve a Regex field unchanged",
    ),
    StageTestCase(
        "preserve_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1_700_000_000, 1), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": Timestamp(1_700_000_000, 1)}],
        msg="$unset should preserve a Timestamp field unchanged",
    ),
    StageTestCase(
        "preserve_minkey",
        docs=[{"_id": 1, "v": MinKey(), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": MinKey()}],
        msg="$unset should preserve a MinKey field unchanged",
    ),
    StageTestCase(
        "preserve_maxkey",
        docs=[{"_id": 1, "v": MaxKey(), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": MaxKey()}],
        msg="$unset should preserve a MaxKey field unchanged",
    ),
    StageTestCase(
        "preserve_code",
        docs=[{"_id": 1, "v": Code("function(){}"), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": Code("function(){}")}],
        msg="$unset should preserve a Code field unchanged",
    ),
    StageTestCase(
        "preserve_code_with_scope",
        docs=[{"_id": 1, "v": Code("function(){}", {"x": 1}), "rm": 0}],
        pipeline=[{"$unset": "rm"}],
        expected=[{"_id": 1, "v": Code("function(){}", {"x": 1})}],
        msg="$unset should preserve a CodeWithScope field unchanged",
    ),
]

UNSET_BSON_TYPE_TESTS_ALL = UNSET_BSON_TYPE_TESTS + UNSET_BSON_TYPE_PRESERVATION_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_BSON_TYPE_TESTS_ALL))
def test_unset_bson_types(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset stage BSON type handling."""
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
        ignore_doc_order=True,
    )
