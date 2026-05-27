"""Tests for dataSize command keyPattern parameter."""

from dataclasses import dataclass, field
from typing import Any, Dict

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

KEYPATTERN_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="keyPattern_type",
        msg="keyPattern should reject non-document types",
        keyword="keyPattern",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

KEYPATTERN_REJECTION_CASES = generate_bson_rejection_test_cases(KEYPATTERN_TYPE_PARAMS)
KEYPATTERN_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(KEYPATTERN_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", KEYPATTERN_REJECTION_CASES)
def test_dataSize_keyPattern_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dataSize rejects non-document BSON types for keyPattern."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": sample_value})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", KEYPATTERN_ACCEPTANCE_CASES)
def test_dataSize_keyPattern_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test dataSize accepts document and null BSON types for keyPattern."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)


@dataclass(frozen=True)
class KeyPatternTest(BaseTestCase):
    """Test case for dataSize keyPattern parameter behavior."""

    doc_count: int = 10
    create_index: bool = False
    key_pattern: Dict[str, Any] = field(default_factory=lambda: {"_id": 1})


KEY_PATTERN_TESTS: list[KeyPatternTest] = [
    KeyPatternTest(
        "keyPattern_id",
        expected={"ok": 1.0},
        key_pattern={"_id": 1},
        msg="keyPattern _id should succeed",
    ),
    KeyPatternTest(
        "without_min_max",
        expected={"ok": 1.0},
        create_index=True,
        key_pattern={"x": 1},
        msg="keyPattern without min/max should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KEY_PATTERN_TESTS))
def test_dataSize_key_pattern(collection, test):
    """Test dataSize with keyPattern parameter."""
    collection.insert_many([{"_id": i, "x": i} for i in range(test.doc_count)])
    if test.create_index:
        collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": test.key_pattern})
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_dataSize_keyPattern_no_matching_index(collection):
    """Test dataSize with keyPattern not matching any index still succeeds."""
    collection.insert_one({"_id": 1, "x": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": {"z": 1}})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Non-matching keyPattern should still succeed")


def test_dataSize_keyPattern_compound_index(collection):
    """Test dataSize with compound keyPattern matching compound index succeeds."""
    collection.insert_many([{"_id": i, "a": i, "b": i * 2} for i in range(10)])
    collection.create_index([("a", 1), ("b", 1)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": {"a": 1, "b": 1}})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Compound keyPattern should succeed")
