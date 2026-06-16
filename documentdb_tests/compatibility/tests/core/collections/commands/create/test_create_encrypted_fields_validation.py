"""Tests for the create command encrypted fields validation behavior."""

from datetime import datetime, timezone
from uuid import uuid4

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ENCRYPTED_FIELD_CAPPED_ERROR,
    ENCRYPTED_FIELD_DUPLICATE_PATH_ERROR,
    ENCRYPTED_FIELD_EMPTY_PATH_ERROR,
    ENCRYPTED_FIELD_ID_PATH_ERROR,
    ENCRYPTED_FIELD_UNSUPPORTED_TYPE_ERROR,
    ENCRYPTED_FIELD_VIEW_TIMESERIES_ERROR,
    INVALID_UUID_ERROR,
    MISSING_FIELD_ERROR,
    NULL_BYTE_PATH_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [EncryptedFields Type Strictness]: non-document types for
# encryptedFields produce TYPE_MISMATCH_ERROR.
CREATE_ENCRYPTED_FIELDS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"ef_err_non_document_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} encryptedFields should fail with type mismatch",
    )
    for label, val in [
        ("string", "not_a_doc"),
        ("int", 42),
        ("array", [{"fields": []}]),
        ("bool", True),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
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

# Property [EncryptedFields Structure Validation]: missing or non-array fields
# key produces errors.
CREATE_ENCRYPTED_FIELDS_STRUCTURE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="ef_err_missing_fields",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="encryptedFields without fields key should fail",
    ),
    CommandTestCase(
        id="ef_err_null_fields",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="encryptedFields with fields:null treated as missing should fail",
    ),
    CommandTestCase(
        id="ef_err_non_array_fields",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": "not_array"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="non-array fields should fail with type mismatch",
    ),
    CommandTestCase(
        id="ef_err_non_array_fields_object",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": {"path": "ssn"}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="object fields should fail with type mismatch",
    ),
]

# Property [EncryptedFields Path Validation]: empty, _id, _id subfield, and
# null-byte paths produce their respective errors.
CREATE_ENCRYPTED_FIELDS_PATH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="ef_err_empty_path",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "", "keyId": Binary(uuid4().bytes, 4)}]},
        },
        error_code=ENCRYPTED_FIELD_EMPTY_PATH_ERROR,
        msg="empty path should fail",
    ),
    CommandTestCase(
        id="ef_err_id_path",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "_id", "keyId": Binary(uuid4().bytes, 4)}]},
        },
        error_code=ENCRYPTED_FIELD_ID_PATH_ERROR,
        msg="_id path should fail",
    ),
    CommandTestCase(
        id="ef_err_id_subfield_path",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "_id.sub", "keyId": Binary(uuid4().bytes, 4)}]},
        },
        error_code=ENCRYPTED_FIELD_ID_PATH_ERROR,
        msg="_id.* subfield path should fail",
    ),
    CommandTestCase(
        id="ef_err_null_byte_in_path",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [{"path": "test\x00field", "keyId": Binary(uuid4().bytes, 4)}]
            },
        },
        error_code=NULL_BYTE_PATH_ERROR,
        msg="null byte in path should fail",
    ),
]

# Property [EncryptedFields KeyId Validation]: wrong size and wrong binary
# subtype for keyId produce their respective errors.
CREATE_ENCRYPTED_FIELDS_KEYID_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="ef_err_wrong_keyid_size",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(b"short", 4)}]},
        },
        error_code=INVALID_UUID_ERROR,
        msg="keyId with wrong size should fail",
    ),
    CommandTestCase(
        id="ef_err_wrong_binary_subtype",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 0)}]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="keyId with wrong Binary subtype should fail",
    ),
]

# Property [EncryptedFields BsonType Validation]: unsupported bsonType values
# (null, undefined, minKey, maxKey) and unknown type names produce errors.
CREATE_ENCRYPTED_FIELDS_BSONTYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="ef_err_unsupported_bsontype_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "null",
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_UNSUPPORTED_TYPE_ERROR,
        msg="bsonType 'null' is not supported",
    ),
    CommandTestCase(
        id="ef_err_unsupported_bsontype_undefined",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "undefined",
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_UNSUPPORTED_TYPE_ERROR,
        msg="bsonType 'undefined' is not supported",
    ),
    CommandTestCase(
        id="ef_err_unsupported_bsontype_minkey",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "minKey",
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_UNSUPPORTED_TYPE_ERROR,
        msg="bsonType 'minKey' is not supported",
    ),
    CommandTestCase(
        id="ef_err_unsupported_bsontype_maxkey",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "maxKey",
                    }
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_UNSUPPORTED_TYPE_ERROR,
        msg="bsonType 'maxKey' is not supported",
    ),
    CommandTestCase(
        id="ef_err_unknown_bsontype",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "keyId": Binary(uuid4().bytes, 4),
                        "bsonType": "foobar",
                    }
                ]
            },
        },
        error_code=BAD_VALUE_ERROR,
        msg="unknown bsonType name should fail",
    ),
]

# Property [EncryptedFields Duplicate Paths]: duplicate paths in the fields
# array produce ENCRYPTED_FIELD_DUPLICATE_PATH_ERROR.
CREATE_ENCRYPTED_FIELDS_DUPLICATE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="ef_err_duplicate_paths",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {"path": "ssn", "keyId": Binary(uuid4().bytes, 4)},
                    {"path": "ssn", "keyId": Binary(uuid4().bytes, 4)},
                ]
            },
        },
        error_code=ENCRYPTED_FIELD_DUPLICATE_PATH_ERROR,
        msg="duplicate paths should fail",
    ),
]

# Property [EncryptedFields Incompatibilities]: encryptedFields is incompatible
# with capped, timeseries, and viewOn.
CREATE_ENCRYPTED_FIELDS_INCOMPATIBILITY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="ef_err_incompatible_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "capped": True,
            "size": 4096,
        },
        error_code=ENCRYPTED_FIELD_CAPPED_ERROR,
        msg="encryptedFields incompatible with capped",
    ),
    CommandTestCase(
        id="ef_err_incompatible_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "timeseries": {"timeField": "ts"},
        },
        error_code=ENCRYPTED_FIELD_VIEW_TIMESERIES_ERROR,
        msg="encryptedFields incompatible with timeseries",
    ),
    CommandTestCase(
        id="ef_err_incompatible_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "viewOn": "other",
            "pipeline": [],
        },
        error_code=ENCRYPTED_FIELD_VIEW_TIMESERIES_ERROR,
        msg="encryptedFields incompatible with viewOn",
    ),
]

CREATE_ENCRYPTED_FIELDS_VALIDATION_TESTS: list[CommandTestCase] = (
    CREATE_ENCRYPTED_FIELDS_TYPE_ERROR_TESTS
    + CREATE_ENCRYPTED_FIELDS_STRUCTURE_ERROR_TESTS
    + CREATE_ENCRYPTED_FIELDS_PATH_ERROR_TESTS
    + CREATE_ENCRYPTED_FIELDS_KEYID_ERROR_TESTS
    + CREATE_ENCRYPTED_FIELDS_BSONTYPE_ERROR_TESTS
    + CREATE_ENCRYPTED_FIELDS_DUPLICATE_ERROR_TESTS
    + CREATE_ENCRYPTED_FIELDS_INCOMPATIBILITY_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_ENCRYPTED_FIELDS_VALIDATION_TESTS))
def test_create_encrypted_fields_validation(database_client, collection, test):
    """Test create command encrypted fields validation behavior."""
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
