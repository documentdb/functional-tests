"""Tests for dataSize command argument validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


@dataclass(frozen=True)
class DataSizeArgTest(BaseTestCase):
    value: Any = None


INVALID_TYPE_TESTS: list[DataSizeArgTest] = [
    DataSizeArgTest("int", value=1, error_code=TYPE_MISMATCH_ERROR, msg="int should fail"),
    DataSizeArgTest("double", value=1.5, error_code=TYPE_MISMATCH_ERROR, msg="double should fail"),
    DataSizeArgTest("long", value=Int64(1), error_code=TYPE_MISMATCH_ERROR, msg="long should fail"),
    DataSizeArgTest(
        "decimal128",
        value=Decimal128("1"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="decimal128 should fail",
    ),
    DataSizeArgTest(
        "bool_true", value=True, error_code=TYPE_MISMATCH_ERROR, msg="bool should fail"
    ),
    DataSizeArgTest(
        "bool_false", value=False, error_code=TYPE_MISMATCH_ERROR, msg="bool false should fail"
    ),
    DataSizeArgTest(
        "date",
        value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=TYPE_MISMATCH_ERROR,
        msg="date should fail",
    ),
    DataSizeArgTest("null", value=None, error_code=MISSING_FIELD_ERROR, msg="null should fail"),
    DataSizeArgTest("object", value={}, error_code=TYPE_MISMATCH_ERROR, msg="object should fail"),
    DataSizeArgTest("array", value=[], error_code=TYPE_MISMATCH_ERROR, msg="array should fail"),
    DataSizeArgTest(
        "binData", value=Binary(b""), error_code=TYPE_MISMATCH_ERROR, msg="binData should fail"
    ),
    DataSizeArgTest(
        "objectId", value=ObjectId(), error_code=TYPE_MISMATCH_ERROR, msg="objectId should fail"
    ),
    DataSizeArgTest(
        "regex", value=Regex("test"), error_code=TYPE_MISMATCH_ERROR, msg="regex should fail"
    ),
    DataSizeArgTest(
        "timestamp",
        value=Timestamp(0, 0),
        error_code=TYPE_MISMATCH_ERROR,
        msg="timestamp should fail",
    ),
    DataSizeArgTest(
        "minKey", value=MinKey(), error_code=TYPE_MISMATCH_ERROR, msg="minKey should fail"
    ),
    DataSizeArgTest(
        "maxKey", value=MaxKey(), error_code=TYPE_MISMATCH_ERROR, msg="maxKey should fail"
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_TYPE_TESTS))
def test_dataSize_invalid_type(collection, test):
    """Test dataSize with non-string types for namespace."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dataSize": test.value})
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_dataSize_valid_namespace(collection):
    """Test dataSize with valid namespace db.collection succeeds."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Valid namespace should succeed")


def test_dataSize_empty_string(collection):
    """Test dataSize with empty string returns error."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dataSize": ""})
    assertFailureCode(result, INVALID_NAMESPACE_ERROR, msg="Empty string should fail")


def test_dataSize_no_dot(collection):
    """Test dataSize with namespace without dot returns error."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dataSize": "nodot"})
    assertFailureCode(result, INVALID_NAMESPACE_ERROR, msg="No dot in namespace should fail")


def test_dataSize_unrecognized_field(collection):
    """Test dataSize with unrecognized extra field returns error."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "foo": 1})
    assertFailureCode(
        result, UNRECOGNIZED_COMMAND_FIELD_ERROR, msg="Unrecognized field should error"
    )
