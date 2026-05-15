"""Tests for cloneCollectionAsCapped field type validation."""

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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [toCollection Type Errors]: non-string BSON types and
# missing toCollection field produce TYPE_MISMATCH_ERROR.
TO_COLLECTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int32",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": 42,
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="int32 toCollection should fail",
    ),
    CommandTestCase(
        "int64",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": Int64(42),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int64 toCollection should fail",
    ),
    CommandTestCase(
        "double",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": 3.14,
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="double toCollection should fail",
    ),
    CommandTestCase(
        "decimal128",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": Decimal128("1"),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Decimal128 toCollection should fail",
    ),
    CommandTestCase(
        "bool",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": True,
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="bool toCollection should fail",
    ),
    CommandTestCase(
        "null",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": None,
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="null toCollection should fail",
    ),
    CommandTestCase(
        "array",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": [1, 2],
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="array toCollection should fail",
    ),
    CommandTestCase(
        "object",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": {"a": 1},
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="object toCollection should fail",
    ),
    CommandTestCase(
        "objectid",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": ObjectId("000000000000000000000001"),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId toCollection should fail",
    ),
    CommandTestCase(
        "datetime",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="datetime toCollection should fail",
    ),
    CommandTestCase(
        "timestamp",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": Timestamp(1, 1),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp toCollection should fail",
    ),
    CommandTestCase(
        "binary",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": Binary(b"\x01"),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary toCollection should fail",
    ),
    CommandTestCase(
        "regex",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": Regex("abc", "i"),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex toCollection should fail",
    ),
    CommandTestCase(
        "code",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": Code("function(){}"),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code toCollection should fail",
    ),
    CommandTestCase(
        "code_with_scope",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": Code("function(){}", {"x": 1}),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code with scope toCollection should fail",
    ),
    CommandTestCase(
        "minkey",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": MinKey(),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey toCollection should fail",
    ),
    CommandTestCase(
        "maxkey",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": MaxKey(),
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey toCollection should fail",
    ),
    CommandTestCase(
        "missing_field",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="missing toCollection field should fail",
    ),
    CommandTestCase(
        "wrong_case",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "tocollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="wrong-case field name should be treated as missing",
    ),
]

# Property [Source Type Errors]: all non-string BSON types for the
# cloneCollectionAsCapped field produce TYPE_MISMATCH_ERROR.
SOURCE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int32",
        command=lambda ctx: {
            "cloneCollectionAsCapped": 42,
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="int32 source should fail",
    ),
    CommandTestCase(
        "int64",
        command=lambda ctx: {
            "cloneCollectionAsCapped": Int64(42),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int64 source should fail",
    ),
    CommandTestCase(
        "double",
        command=lambda ctx: {
            "cloneCollectionAsCapped": 3.14,
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="double source should fail",
    ),
    CommandTestCase(
        "decimal128",
        command=lambda ctx: {
            "cloneCollectionAsCapped": Decimal128("1"),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Decimal128 source should fail",
    ),
    CommandTestCase(
        "bool",
        command=lambda ctx: {
            "cloneCollectionAsCapped": True,
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="bool source should fail",
    ),
    CommandTestCase(
        "null",
        command=lambda ctx: {
            "cloneCollectionAsCapped": None,
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="null source should fail",
    ),
    CommandTestCase(
        "array",
        command=lambda ctx: {
            "cloneCollectionAsCapped": [1, 2],
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="array source should fail",
    ),
    CommandTestCase(
        "object",
        command=lambda ctx: {
            "cloneCollectionAsCapped": {"a": 1},
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="object source should fail",
    ),
    CommandTestCase(
        "objectid",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ObjectId("000000000000000000000001"),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId source should fail",
    ),
    CommandTestCase(
        "datetime",
        command=lambda ctx: {
            "cloneCollectionAsCapped": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="datetime source should fail",
    ),
    CommandTestCase(
        "timestamp",
        command=lambda ctx: {
            "cloneCollectionAsCapped": Timestamp(1, 1),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp source should fail",
    ),
    CommandTestCase(
        "binary",
        command=lambda ctx: {
            "cloneCollectionAsCapped": Binary(b"\x01"),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary source should fail",
    ),
    CommandTestCase(
        "regex",
        command=lambda ctx: {
            "cloneCollectionAsCapped": Regex("abc", "i"),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex source should fail",
    ),
    CommandTestCase(
        "code",
        command=lambda ctx: {
            "cloneCollectionAsCapped": Code("function(){}"),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code source should fail",
    ),
    CommandTestCase(
        "code_with_scope",
        command=lambda ctx: {
            "cloneCollectionAsCapped": Code("function(){}", {"x": 1}),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code with scope source should fail",
    ),
    CommandTestCase(
        "minkey",
        command=lambda ctx: {
            "cloneCollectionAsCapped": MinKey(),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey source should fail",
    ),
    CommandTestCase(
        "maxkey",
        command=lambda ctx: {
            "cloneCollectionAsCapped": MaxKey(),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey source should fail",
    ),
]

FIELD_TYPES_TESTS: list[CommandTestCase] = TO_COLLECTION_TYPE_ERROR_TESTS + SOURCE_TYPE_ERROR_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FIELD_TYPES_TESTS))
def test_clone_collection_as_capped_field_types(database_client, collection, test):
    """Test cloneCollectionAsCapped field type validation."""
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
