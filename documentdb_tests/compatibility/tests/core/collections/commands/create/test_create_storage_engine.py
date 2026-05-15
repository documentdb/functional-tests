"""Tests for the create command input/output contract."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [StorageEngine and IndexOptionDefaults Acceptance]: both fields
# accept document or null; null and empty {} are treated as omitted.
CREATE_STORAGE_ENGINE_INDEX_OPTION_DEFAULTS_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="storage_engine_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": None,
        },
        expected={"ok": 1.0},
        msg="storageEngine:null should be treated as omitted",
    ),
    CommandTestCase(
        id="storage_engine_empty_doc",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {},
        },
        expected={"ok": 1.0},
        msg="storageEngine:{} should be treated as omitted",
    ),
    CommandTestCase(
        id="storage_engine_wired_tiger",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {"wiredTiger": {"configString": ""}},
        },
        expected={"ok": 1.0},
        msg="storageEngine with registered engine name should succeed",
    ),
    CommandTestCase(
        id="index_option_defaults_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": None,
        },
        expected={"ok": 1.0},
        msg="indexOptionDefaults:null should be treated as omitted",
    ),
    CommandTestCase(
        id="index_option_defaults_empty_doc",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {},
        },
        expected={"ok": 1.0},
        msg="indexOptionDefaults:{} should be treated as omitted",
    ),
    CommandTestCase(
        id="index_option_defaults_storage_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {"storageEngine": {"wiredTiger": {"configString": ""}}},
        },
        expected={"ok": 1.0},
        msg="indexOptionDefaults with storageEngine sub-field should succeed",
    ),
    CommandTestCase(
        id="capped_with_index_option_defaults",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "indexOptionDefaults": {"storageEngine": {"wiredTiger": {"configString": ""}}},
        },
        expected={"ok": 1.0},
        msg="Capped collection + indexOptionDefaults should succeed",
    ),
]

# Property [StorageEngine Type Strictness]: non-document types for
# storageEngine or indexOptionDefaults produce TYPE_MISMATCH_ERROR.
CREATE_STORAGE_ENGINE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"{field_id}_{label}",
        command=lambda ctx, field=field_key, val=val: {
            "create": f"{ctx.collection}_custom",
            field: val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} {field_key} should fail with type mismatch",
    )
    for field_id, field_key in [
        ("storage_engine", "storageEngine"),
        ("index_option_defaults", "indexOptionDefaults"),
    ]
    for label, val in [
        ("int", 123),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("string", "invalid"),
        ("array", [1, 2]),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [StorageEngine Unknown Engine]: an unregistered engine name
# in storageEngine or indexOptionDefaults.storageEngine produces
# INVALID_OPTIONS_ERROR.
CREATE_STORAGE_ENGINE_UNKNOWN_ENGINE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="storage_engine_unknown_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {"unknownEngine": {}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Unknown engine name in storageEngine should fail",
    ),
    CommandTestCase(
        id="index_option_defaults_unknown_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {"storageEngine": {"unknownEngine": {}}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Unknown engine name in indexOptionDefaults.storageEngine should fail",
    ),
]

# Property [StorageEngine Value Validation]: invalid engine values,
# unrecognized keys, and malformed configString content produce errors.
CREATE_STORAGE_ENGINE_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="storage_engine_non_doc_engine_value",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {"wiredTiger": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Non-document engine value should fail",
    ),
    CommandTestCase(
        id="storage_engine_unknown_key_in_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {"wiredTiger": {"badKey": "val"}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Unknown key in wiredTiger doc should fail",
    ),
    CommandTestCase(
        id="storage_engine_invalid_config_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {"wiredTiger": {"configString": "invalid=bad"}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid configString content should fail",
    ),
    CommandTestCase(
        id="storage_engine_null_bytes_in_config_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "storageEngine": {"wiredTiger": {"configString": "test\x00null"}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Null bytes in configString should fail",
    ),
    CommandTestCase(
        id="index_option_defaults_non_doc_engine_value",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {"storageEngine": {"wiredTiger": "invalid"}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Non-document engine value in indexOptionDefaults should fail",
    ),
    CommandTestCase(
        id="index_option_defaults_unknown_key_in_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {"storageEngine": {"wiredTiger": {"badKey": "val"}}},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Unknown key in indexOptionDefaults wiredTiger doc should fail",
    ),
    CommandTestCase(
        id="index_option_defaults_invalid_config_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {
                "storageEngine": {"wiredTiger": {"configString": "invalid=bad"}}
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid configString in indexOptionDefaults should fail",
    ),
    CommandTestCase(
        id="index_option_defaults_null_bytes_in_config_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {
                "storageEngine": {"wiredTiger": {"configString": "test\x00null"}}
            },
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Null bytes in indexOptionDefaults configString should fail",
    ),
]

# Property [IndexOptionDefaults Unknown Fields]: unknown sub-fields in
# indexOptionDefaults produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CREATE_INDEX_OPTION_DEFAULTS_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="index_option_defaults_unknown_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "indexOptionDefaults": {"unknownField": "val"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown sub-field in indexOptionDefaults should fail",
    ),
]

CREATE_STORAGE_ENGINE_INDEX_OPTION_DEFAULTS_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_STORAGE_ENGINE_TYPE_ERROR_TESTS
    + CREATE_STORAGE_ENGINE_UNKNOWN_ENGINE_TESTS
    + CREATE_STORAGE_ENGINE_VALUE_ERROR_TESTS
    + CREATE_INDEX_OPTION_DEFAULTS_UNKNOWN_FIELD_TESTS
)

CREATE_STORAGE_ENGINE_TESTS: list[CommandTestCase] = (
    CREATE_STORAGE_ENGINE_INDEX_OPTION_DEFAULTS_SUCCESS_TESTS
    + CREATE_STORAGE_ENGINE_INDEX_OPTION_DEFAULTS_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_STORAGE_ENGINE_TESTS))
def test_create_storage_engine(database_client, collection, test):
    """Test create command storage engine behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
