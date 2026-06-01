"""Tests for dataSize command optional parameters.

Covers BSON type rejection and acceptance for min/max via bson_type_validator,
and behavioral tests for keyPattern, estimate, and min/max.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin


KEY_PATTERN_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "keyPattern_id",
        command={"keyPattern": {"_id": 1}},
        expected={"ok": 1.0},
        msg="keyPattern _id should succeed",
    ),
    DiagnosticTestCase(
        "without_min_max",
        command={"keyPattern": {"x": 1}},
        expected={"ok": 1.0},
        msg="keyPattern without min/max should succeed",
    ),
    DiagnosticTestCase(
        "no_matching_index",
        command={"keyPattern": {"z": 1}},
        expected={"ok": 1.0},
        msg="Non-matching keyPattern should still succeed",
    ),
]

MIN_MAX_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "with_min_max",
        command={"keyPattern": {"x": 1}, "min": {"x": 10}, "max": {"x": 50}},
        expected={"ok": 1.0},
        msg="min/max range query should succeed",
    ),
    DiagnosticTestCase(
        "min_max_no_match",
        command={"keyPattern": {"x": 1}, "min": {"x": 1000}, "max": {"x": 2000}},
        expected={"numObjects": Int64(0)},
        msg="No match should return 0",
    ),
    DiagnosticTestCase(
        "min_equal_max",
        command={"keyPattern": {"x": 1}, "min": {"x": 5}, "max": {"x": 5}},
        expected={"numObjects": Int64(0)},
        msg="min==max should return 0",
    ),
    DiagnosticTestCase(
        "min_greater_than_max",
        command={"keyPattern": {"x": 1}, "min": {"x": 50}, "max": {"x": 10}},
        expected={"numObjects": Int64(0)},
        msg="min > max should return 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KEY_PATTERN_TESTS + MIN_MAX_TESTS))
def test_dataSize_key_pattern_and_min_max(collection, test):
    """Test dataSize with keyPattern and min/max parameters."""
    collection.insert_many([{"_id": i, "x": i} for i in range(100)])
    collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    cmd = {"dataSize": ns, **(test.command or {})}
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_dataSize_keyPattern_compound_index(collection):
    """Test dataSize with compound keyPattern matching compound index succeeds."""
    collection.insert_many([{"_id": i, "a": i, "b": i * 2} for i in range(10)])
    collection.create_index([("a", 1), ("b", 1)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": {"a": 1, "b": 1}})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Compound keyPattern should succeed")


def test_dataSize_estimate_true(collection):
    """Test dataSize with estimate: true returns estimate: true in response."""
    collection.insert_many([{"_id": i, "data": "x" * 100} for i in range(10)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": True})
    assertSuccessPartial(
        result, {"ok": 1.0, "estimate": True}, msg="estimate true should echo in response"
    )


def test_dataSize_estimate_false(collection):
    """Test dataSize with estimate: false returns estimate: false in response."""
    collection.insert_many([{"_id": i} for i in range(10)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": False})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "estimate": False, "numObjects": Int64(10)},
        msg="estimate false should echo in response",
    )


def test_dataSize_estimate_returns_numObjects(collection):
    """Test dataSize with estimate: true includes numObjects in response."""
    collection.insert_many([{"_id": i} for i in range(20)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": True})
    assertResult(
        result,
        expected={"numObjects": Exists()},
        raw_res=True,
        msg="estimate should include numObjects",
    )


def test_dataSize_min_max_both_null(collection):
    """Test dataSize with both min and max set to null succeeds (treated as absent)."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])
    collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(
        collection,
        {"dataSize": ns, "keyPattern": {"x": 1}, "min": None, "max": None},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Both min and max null should succeed")


MIN_MAX_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="min_type",
        msg="min should reject non-document types",
        keyword="min",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="max_type",
        msg="max should reject non-document types",
        keyword="max",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

MIN_MAX_REJECTION_CASES = generate_bson_rejection_test_cases(MIN_MAX_TYPE_PARAMS)
MIN_MAX_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(MIN_MAX_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", MIN_MAX_REJECTION_CASES)
def test_dataSize_min_max_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dataSize rejects non-document BSON types for min and max."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    cmd = {"dataSize": ns, "keyPattern": {"_id": 1}, spec.keyword: sample_value}
    result = execute_command(collection, cmd)
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", MIN_MAX_ACCEPTANCE_CASES)
def test_dataSize_min_max_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test dataSize accepts document and null BSON types for min and max.

    OBJECT acceptance sets both bounds together with keyPattern-matching fields
    (semantic constraint). NULL is treated as absent so no sibling is needed.
    """
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    if sample_value is None:
        cmd = {"dataSize": ns, "keyPattern": {"_id": 1}, spec.keyword: sample_value}
    else:
        cmd = {
            "dataSize": ns,
            "keyPattern": {"_id": 1},
            "min": {"_id": 0},
            "max": {"_id": 100},
        }
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)
