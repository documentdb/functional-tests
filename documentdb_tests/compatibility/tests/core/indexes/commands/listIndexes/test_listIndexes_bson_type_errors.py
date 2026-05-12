"""
Tests for listIndexes command — BSON type validation.

Covers invalid BSON type rejection for: collection name, cursor.batchSize,
cursor object, includeIndexBuildInfo, and includeBuildUUIDs.
"""

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, ObjectId, Regex, Timestamp
from bson.max_key import MaxKey
from bson.min_key import MinKey

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INVALID_COLLECTION_NAME_TYPES: list[IndexTestCase] = [
    IndexTestCase(
        "int",
        invalid_input=123,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Integer collection name should fail",
    ),
    IndexTestCase(
        "long",
        invalid_input=Int64(123),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Long collection name should fail",
    ),
    IndexTestCase(
        "double",
        invalid_input=1.5,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Double collection name should fail",
    ),
    IndexTestCase(
        "decimal128",
        invalid_input=Decimal128("1.5"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Decimal128 collection name should fail",
    ),
    IndexTestCase(
        "bool",
        invalid_input=True,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Boolean collection name should fail",
    ),
    IndexTestCase(
        "date",
        invalid_input=datetime(2024, 1, 1),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Date collection name should fail",
    ),
    IndexTestCase(
        "null",
        invalid_input=None,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Null collection name should fail",
    ),
    IndexTestCase(
        "object",
        invalid_input={"a": 1},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Object collection name should fail",
    ),
    IndexTestCase(
        "array",
        invalid_input=[1, 2],
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Array collection name should fail",
    ),
    IndexTestCase(
        "binData",
        invalid_input=Binary(b"\x00\x01"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="BinData collection name should fail",
    ),
    IndexTestCase(
        "objectId",
        invalid_input=ObjectId(),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="ObjectId collection name should fail",
    ),
    IndexTestCase(
        "regex",
        invalid_input=Regex(".*"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Regex collection name should fail",
    ),
    IndexTestCase(
        "javascript",
        invalid_input=Code("function(){}"),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="JavaScript collection name should fail",
    ),
    IndexTestCase(
        "timestamp",
        invalid_input=Timestamp(0, 1),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Timestamp collection name should fail",
    ),
    IndexTestCase(
        "minKey",
        invalid_input=MinKey(),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MinKey collection name should fail",
    ),
    IndexTestCase(
        "maxKey",
        invalid_input=MaxKey(),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MaxKey collection name should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_COLLECTION_NAME_TYPES))
def test_listIndexes_invalid_collection_name_type(collection, test):
    """Test listIndexes rejects non-string collection name types."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"listIndexes": test.invalid_input})
    assertResult(result, error_code=test.error_code, msg=test.msg)


INVALID_BATCH_SIZE_TYPES: list[IndexTestCase] = [
    IndexTestCase(
        "string",
        invalid_input="abc",
        error_code=TYPE_MISMATCH_ERROR,
        msg="String batchSize should fail",
    ),
    IndexTestCase(
        "bool",
        invalid_input=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Boolean batchSize should fail",
    ),
    IndexTestCase(
        "date",
        invalid_input=datetime(2024, 1, 1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Date batchSize should fail",
    ),
    IndexTestCase(
        "object",
        invalid_input={"a": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Object batchSize should fail",
    ),
    IndexTestCase(
        "array",
        invalid_input=[1, 2],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array batchSize should fail",
    ),
    IndexTestCase(
        "binData",
        invalid_input=Binary(b"\x00"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="BinData batchSize should fail",
    ),
    IndexTestCase(
        "objectId",
        invalid_input=ObjectId(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId batchSize should fail",
    ),
    IndexTestCase(
        "regex",
        invalid_input=Regex(".*"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex batchSize should fail",
    ),
    IndexTestCase(
        "javascript",
        invalid_input=Code("function(){}"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="JavaScript batchSize should fail",
    ),
    IndexTestCase(
        "timestamp",
        invalid_input=Timestamp(0, 1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp batchSize should fail",
    ),
    IndexTestCase(
        "minKey",
        invalid_input=MinKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey batchSize should fail",
    ),
    IndexTestCase(
        "maxKey",
        invalid_input=MaxKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey batchSize should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_BATCH_SIZE_TYPES))
def test_listIndexes_invalid_batchSize_type(collection, test):
    """Test listIndexes rejects invalid cursor.batchSize types."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection, {"listIndexes": collection.name, "cursor": {"batchSize": test.invalid_input}}
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)


INVALID_CURSOR_TYPES: list[IndexTestCase] = [
    IndexTestCase(
        "string",
        invalid_input="abc",
        error_code=TYPE_MISMATCH_ERROR,
        msg="String cursor should fail",
    ),
    IndexTestCase(
        "int", invalid_input=123, error_code=TYPE_MISMATCH_ERROR, msg="Integer cursor should fail"
    ),
    IndexTestCase(
        "long",
        invalid_input=Int64(123),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Long cursor should fail",
    ),
    IndexTestCase(
        "double",
        invalid_input=1.5,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Double cursor should fail",
    ),
    IndexTestCase(
        "decimal128",
        invalid_input=Decimal128("1.5"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Decimal128 cursor should fail",
    ),
    IndexTestCase(
        "bool",
        invalid_input=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Boolean cursor should fail",
    ),
    IndexTestCase(
        "date",
        invalid_input=datetime(2024, 1, 1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Date cursor should fail",
    ),
    IndexTestCase(
        "array",
        invalid_input=[1, 2],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array cursor should fail",
    ),
    IndexTestCase(
        "binData",
        invalid_input=Binary(b"\x00"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="BinData cursor should fail",
    ),
    IndexTestCase(
        "objectId",
        invalid_input=ObjectId(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId cursor should fail",
    ),
    IndexTestCase(
        "regex",
        invalid_input=Regex(".*"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex cursor should fail",
    ),
    IndexTestCase(
        "javascript",
        invalid_input=Code("function(){}"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="JavaScript cursor should fail",
    ),
    IndexTestCase(
        "timestamp",
        invalid_input=Timestamp(0, 1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp cursor should fail",
    ),
    IndexTestCase(
        "minKey",
        invalid_input=MinKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey cursor should fail",
    ),
    IndexTestCase(
        "maxKey",
        invalid_input=MaxKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey cursor should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_CURSOR_TYPES))
def test_listIndexes_invalid_cursor_type(collection, test):
    """Test listIndexes rejects non-object cursor types."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection, {"listIndexes": collection.name, "cursor": test.invalid_input}
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)


INVALID_BOOL_OPTION_TYPES: list[IndexTestCase] = [
    IndexTestCase(
        "buildInfo_string",
        command_options={"includeIndexBuildInfo": "abc"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="String includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_date",
        command_options={"includeIndexBuildInfo": datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Date includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_object",
        command_options={"includeIndexBuildInfo": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Object includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_array",
        command_options={"includeIndexBuildInfo": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_binData",
        command_options={"includeIndexBuildInfo": Binary(b"\x00")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="BinData includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_objectId",
        command_options={"includeIndexBuildInfo": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_regex",
        command_options={"includeIndexBuildInfo": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_javascript",
        command_options={"includeIndexBuildInfo": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="JavaScript includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_timestamp",
        command_options={"includeIndexBuildInfo": Timestamp(0, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_minKey",
        command_options={"includeIndexBuildInfo": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildInfo_maxKey",
        command_options={"includeIndexBuildInfo": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey includeIndexBuildInfo should fail",
    ),
    IndexTestCase(
        "buildUUIDs_string",
        command_options={"includeBuildUUIDs": "abc"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="String includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_date",
        command_options={"includeBuildUUIDs": datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Date includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_object",
        command_options={"includeBuildUUIDs": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Object includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_array",
        command_options={"includeBuildUUIDs": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_binData",
        command_options={"includeBuildUUIDs": Binary(b"\x00")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="BinData includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_objectId",
        command_options={"includeBuildUUIDs": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_regex",
        command_options={"includeBuildUUIDs": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_javascript",
        command_options={"includeBuildUUIDs": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="JavaScript includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_timestamp",
        command_options={"includeBuildUUIDs": Timestamp(0, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_minKey",
        command_options={"includeBuildUUIDs": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey includeBuildUUIDs should fail",
    ),
    IndexTestCase(
        "buildUUIDs_maxKey",
        command_options={"includeBuildUUIDs": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey includeBuildUUIDs should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_BOOL_OPTION_TYPES))
def test_listIndexes_invalid_bool_option_type(collection, test):
    """Test listIndexes rejects non-boolean includeIndexBuildInfo and includeBuildUUIDs types."""
    collection.insert_one({"_id": 1})
    cmd = {"listIndexes": collection.name}
    cmd.update(test.command_options)
    result = execute_command(collection, cmd)
    assertResult(result, error_code=test.error_code, msg=test.msg)
