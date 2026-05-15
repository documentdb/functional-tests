"""Tests for validateDBMetadata type strictness on apiParameters, db, and collection."""

from __future__ import annotations

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
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness - apiParameters]: apiParameters must be a
# document; all non-document BSON types produce a type mismatch error.
VALIDATE_DB_METADATA_API_PARAMETERS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_err_api_params_{tid}",
        command={"validateDBMetadata": 1, "apiParameters": val},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"validateDBMetadata should reject {tid} apiParameters",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("string", "not a doc"),
        ("array", [1, 2]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Type Strictness - db]: the db field must be a string; all
# non-string, non-null BSON types produce a type mismatch error.
VALIDATE_DB_METADATA_DB_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_err_db_{tid}",
        command={
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"validateDBMetadata should reject {tid} db",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["test"]),
        ("object", {"name": "test"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Type Strictness - collection]: the collection field must be a
# string; all non-string, non-null BSON types produce a type mismatch error.
VALIDATE_DB_METADATA_COLLECTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_err_collection_{tid}",
        command={
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"validateDBMetadata should reject {tid} collection",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["test"]),
        ("object", {"name": "test"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Type Strictness - apiParameters.version]: the version field
# inside apiParameters must be a string; all non-string BSON types produce
# a type mismatch error.
VALIDATE_DB_METADATA_VERSION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_err_version_{tid}",
        command={
            "validateDBMetadata": 1,
            "apiParameters": {"version": val, "strict": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"validateDBMetadata should reject {tid} apiParameters.version",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["1"]),
        ("object", {"v": "1"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Type Strictness - apiParameters.strict]: the strict field
# inside apiParameters must be a boolean; all non-boolean BSON types
# (including null) produce a type mismatch error.
VALIDATE_DB_METADATA_STRICT_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_err_strict_{tid}",
        command={
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": val},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"validateDBMetadata should reject {tid} apiParameters.strict",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("string", "true"),
        ("null", None),
        ("array", [True]),
        ("object", {"v": True}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Type Strictness - apiParameters.deprecationErrors]: the
# deprecationErrors field inside apiParameters must be a boolean; all
# non-boolean BSON types (including null) produce a type mismatch error.
VALIDATE_DB_METADATA_DEPRECATION_ERRORS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_err_deprecation_errors_{tid}",
        command={
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True, "deprecationErrors": val},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"validateDBMetadata should reject {tid} apiParameters.deprecationErrors",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("string", "true"),
        ("null", None),
        ("array", [True]),
        ("object", {"v": True}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

VALIDATE_DB_METADATA_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = (
    VALIDATE_DB_METADATA_API_PARAMETERS_TYPE_ERROR_TESTS
    + VALIDATE_DB_METADATA_DB_TYPE_ERROR_TESTS
    + VALIDATE_DB_METADATA_COLLECTION_TYPE_ERROR_TESTS
    + VALIDATE_DB_METADATA_VERSION_TYPE_ERROR_TESTS
    + VALIDATE_DB_METADATA_STRICT_TYPE_ERROR_TESTS
    + VALIDATE_DB_METADATA_DEPRECATION_ERRORS_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_TYPE_STRICTNESS_TESTS))
def test_validateDBMetadata_type_strictness(database_client, collection, test):
    """Test validateDBMetadata type strictness on apiParameters, db, and collection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
