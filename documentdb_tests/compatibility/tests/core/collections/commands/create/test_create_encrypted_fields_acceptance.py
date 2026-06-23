"""Tests for the create command encrypted fields acceptance behavior."""

from uuid import uuid4

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [EncryptedFields Structure Acceptance]: valid encryptedFields
# documents are accepted, including null (treated as omitted), minimal
# required fields, and optional sub-fields.
CREATE_ENCRYPTED_FIELDS_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": None,
        },
        expected={"ok": 1.0},
        msg="null encryptedFields should be treated as omitted",
    ),
    CommandTestCase(
        id="minimal_fields_path_and_keyid",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
        },
        expected={"ok": Eq(1.0)},
        msg="Minimal encryptedFields with path and keyId should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="optional_bson_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "bsonType": "string",
                        "keyId": Binary(uuid4().bytes, 4),
                    }
                ]
            },
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with optional bsonType should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="optional_queries_object",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "bsonType": "string",
                        "keyId": Binary(uuid4().bytes, 4),
                        "queries": {"queryType": "equality"},
                    }
                ]
            },
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with queries as object should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="optional_queries_array",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    {
                        "path": "ssn",
                        "bsonType": "string",
                        "keyId": Binary(uuid4().bytes, 4),
                        "queries": [{"queryType": "equality"}],
                    }
                ]
            },
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with queries as array should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
]

# Property [EncryptedFields Custom Collections]: escCollection, ecocCollection,
# and eccCollection accept custom naming patterns.
CREATE_ENCRYPTED_FIELDS_CUSTOM_COLLECTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="esc_collection_custom",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}],
                "escCollection": f"enxcol_.{ctx.collection}_custom.esc",
            },
        },
        expected={"ok": Eq(1.0)},
        msg="Custom escCollection with valid naming pattern should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="ecoc_collection_custom",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}],
                "ecocCollection": f"enxcol_.{ctx.collection}_custom.ecoc",
            },
        },
        expected={"ok": Eq(1.0)},
        msg="Custom ecocCollection with valid naming pattern should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="ecc_collection_custom",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}],
                "eccCollection": "any_name_works",
            },
        },
        expected={"ok": Eq(1.0)},
        msg="eccCollection does not have naming pattern validation",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="null_elements_in_fields_array",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {
                "fields": [
                    None,
                    {"path": "ssn", "keyId": Binary(uuid4().bytes, 4)},
                    None,
                ]
            },
        },
        expected={"ok": Eq(1.0)},
        msg="Null elements in fields array should be silently accepted",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
]

# Property [EncryptedFields Compatibility]: encryptedFields is compatible with
# clusteredIndex, expireAfterSeconds, storageEngine, validator, collation, and
# changeStreamPreAndPostImages.
CREATE_ENCRYPTED_FIELDS_COMPATIBILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="compatible_with_clustered_index",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with clusteredIndex should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="compatible_with_expire_after_seconds",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "expireAfterSeconds": 3600,
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with expireAfterSeconds should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="compatible_with_storage_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "storageEngine": {"wiredTiger": {"configString": ""}},
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with storageEngine should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="compatible_with_validator",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "validator": {"x": {"$exists": True}},
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with validator should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="compatible_with_collation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "collation": {"locale": "en"},
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with collation should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
    CommandTestCase(
        id="compatible_with_change_stream_pre_post_images",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "encryptedFields": {"fields": [{"path": "ssn", "keyId": Binary(uuid4().bytes, 4)}]},
            "changeStreamPreAndPostImages": {"enabled": True},
        },
        expected={"ok": Eq(1.0)},
        msg="encryptedFields with changeStreamPreAndPostImages should succeed",
        marks=(pytest.mark.requires(queryable_encryption=True),),
    ),
]

CREATE_ENCRYPTED_FIELDS_SUCCESS_TESTS: list[CommandTestCase] = (
    CREATE_ENCRYPTED_FIELDS_STRUCTURE_TESTS
    + CREATE_ENCRYPTED_FIELDS_CUSTOM_COLLECTIONS_TESTS
    + CREATE_ENCRYPTED_FIELDS_COMPATIBILITY_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_ENCRYPTED_FIELDS_SUCCESS_TESTS))
def test_create_encrypted_fields_acceptance(database_client, collection, test):
    """Test create command encrypted fields acceptance behavior."""
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
