"""Tests for bulkWrite core insert operations, data type coverage, and document edge cases."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_constants import BSON_TYPE_SAMPLES, BsonType

BULKWRITE_INSERT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "insert_double",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.DOUBLE]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a double field value",
    ),
    CommandTestCase(
        "insert_string",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.STRING]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a string field value",
    ),
    CommandTestCase(
        "insert_object",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.OBJECT]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a object field value",
    ),
    CommandTestCase(
        "insert_array",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.ARRAY]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a array field value",
    ),
    CommandTestCase(
        "insert_bindata",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.BIN_DATA]}}
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a bindata field value",
    ),
    CommandTestCase(
        "insert_objectid",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.OBJECT_ID]}}
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a objectid field value",
    ),
    CommandTestCase(
        "insert_boolean",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.BOOL]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a boolean field value",
    ),
    CommandTestCase(
        "insert_date",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.DATE]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a date field value",
    ),
    CommandTestCase(
        "insert_null",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.NULL]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a null field value",
    ),
    CommandTestCase(
        "insert_regex",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.REGEX]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a regex field value",
    ),
    CommandTestCase(
        "insert_int",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.INT]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a int field value",
    ),
    CommandTestCase(
        "insert_long",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.LONG]}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a long field value",
    ),
    CommandTestCase(
        "insert_timestamp",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.TIMESTAMP]}}
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a timestamp field value",
    ),
    CommandTestCase(
        "insert_decimal128",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.DECIMAL]}}
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a decimal128 field value",
    ),
    CommandTestCase(
        "insert_minkey",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.MIN_KEY]}}
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a minkey field value",
    ),
    CommandTestCase(
        "insert_maxkey",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.MAX_KEY]}}
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a maxkey field value",
    ),
    CommandTestCase(
        "insert_javascript",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "v": BSON_TYPE_SAMPLES[BsonType.JAVASCRIPT]}}
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a javascript field value",
    ),
]

BULKWRITE_INSERT_CORE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_insert",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1, "a": 1}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should perform a single insert",
    ),
    CommandTestCase(
        "multiple_inserts",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "a": 1}},
                {"insert": 0, "document": {"_id": 2, "a": 2}},
                {"insert": 0, "document": {"_id": 3, "a": 3}},
            ],
        },
        expected={"ok": 1.0, "nInserted": 3},
        msg="bulkWrite should perform multiple inserts in one command",
    ),
    CommandTestCase(
        "insert_with_specified_id",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 100, "x": "hello"}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with a specified _id",
    ),
    CommandTestCase(
        "insert_auto_generated_id",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"x": "no_id"}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with an auto-generated _id",
    ),
    CommandTestCase(
        "insert_into_nonexistent_collection",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1, "x": 1}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite insert should implicitly create a non-existent collection",
    ),
    CommandTestCase(
        "insert_empty_document",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert an empty document with an auto-generated _id",
    ),
    CommandTestCase(
        "insert_deeply_nested",
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "insert": 0,
                    "document": {
                        "_id": 1,
                        "level0": {
                            "level1": {
                                "level2": {
                                    "level3": {
                                        "level4": {
                                            "level5": {
                                                "level6": {
                                                    "level7": {
                                                        "level8": {
                                                            "level9": {
                                                                "level10": {
                                                                    "level11": {"value": "deep"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                    },
                }
            ],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a deeply nested document",
    ),
    CommandTestCase(
        "insert_long_field_names",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "a" * 200: "value"}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with very long field names",
    ),
    CommandTestCase(
        "insert_dollar_prefixed_fields",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "$dollar": "value"}}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with dollar-prefixed field names",
    ),
    CommandTestCase(
        "insert_dot_notation_fields",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1, "a.b": "value"}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert a document with dot-notation field names",
    ),
    CommandTestCase(
        "insert_into_capped_collection",
        target_collection=CappedCollection(size=1048576),
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1, "x": 1}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should insert into a capped collection",
    ),
]

BULKWRITE_INSERT_TESTS = BULKWRITE_INSERT_TYPE_TESTS + BULKWRITE_INSERT_CORE_TESTS


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_INSERT_TESTS))
def test_bulkWrite_core_insert(database_client, collection, test):
    """Test bulkWrite core insert operations, data type coverage, and document edge cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
