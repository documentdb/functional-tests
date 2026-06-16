"""Tests for validate command argument type handling.

Validates that the validate parameter (collection name) must be a string and
rejects all other BSON types with the correct error code.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Type Rejection]: validate rejects all non-string BSON types for the collection name.
INVALID_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "double",
        command={"validate": 1.0},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject double for collection name",
    ),
    DiagnosticTestCase(
        "int32",
        command={"validate": 1},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject int32 for collection name",
    ),
    DiagnosticTestCase(
        "int64",
        command={"validate": Int64(1)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject int64 for collection name",
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"validate": Decimal128("1")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Decimal128 for collection name",
    ),
    DiagnosticTestCase(
        "bool_true",
        command={"validate": True},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject bool true for collection name",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"validate": False},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject bool false for collection name",
    ),
    DiagnosticTestCase(
        "null",
        command={"validate": None},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject null for collection name",
    ),
    DiagnosticTestCase(
        "object",
        command={"validate": {"a": 1}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject object for collection name",
    ),
    DiagnosticTestCase(
        "empty_object",
        command={"validate": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject empty object for collection name",
    ),
    DiagnosticTestCase(
        "array",
        command={"validate": [1, 2]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject array for collection name",
    ),
    DiagnosticTestCase(
        "empty_array",
        command={"validate": []},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject empty array for collection name",
    ),
    DiagnosticTestCase(
        "binary",
        command={"validate": Binary(b"data")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Binary for collection name",
    ),
    DiagnosticTestCase(
        "objectid",
        command={"validate": ObjectId()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject ObjectId for collection name",
    ),
    DiagnosticTestCase(
        "datetime",
        command={"validate": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject datetime for collection name",
    ),
    DiagnosticTestCase(
        "regex",
        command={"validate": Regex(".*")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Regex for collection name",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"validate": Timestamp(0, 0)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Timestamp for collection name",
    ),
    DiagnosticTestCase(
        "code",
        command={"validate": Code("function(){}")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject JavaScript Code for collection name",
    ),
    DiagnosticTestCase(
        "minkey",
        command={"validate": MinKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject MinKey for collection name",
    ),
    DiagnosticTestCase(
        "maxkey",
        command={"validate": MaxKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject MaxKey for collection name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_TYPE_TESTS))
def test_validate_rejects_non_string_types(collection, test):
    """Test that validate rejects non-string BSON types for the collection name."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [String Acceptance]: validate accepts a valid string collection name.
VALID_STRING_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "valid_collection_name",
        checks={"ok": Eq(1.0)},
        msg="validate should accept a valid collection name string",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_STRING_TESTS))
def test_validate_accepts_string(collection, test):
    """Test that validate accepts a valid string collection name."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
