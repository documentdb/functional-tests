"""Tests for dataSize command min/max parameters.

Covers BSON type rejection via bson_type_validator framework and behavioral
tests for min/max range queries. Acceptance tests are not generated via the
framework because min/max have semantic constraints (bound field names must
match keyPattern, and both must be set together) that the generic samples
cannot satisfy.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

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


@pytest.mark.parametrize("bson_type,sample_value,spec", MIN_MAX_REJECTION_CASES)
def test_dataSize_min_max_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dataSize rejects non-document BSON types for min and max."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    cmd = {"dataSize": ns, "keyPattern": {"_id": 1}, spec.keyword: sample_value}
    result = execute_command(collection, cmd)
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@dataclass(frozen=True)
class MinMaxTest(BaseTestCase):
    """Test case for dataSize min/max range behavior."""

    doc_count: int = 10
    key_pattern: Dict[str, Any] = field(default_factory=lambda: {"x": 1})
    min_bound: Optional[Dict[str, Any]] = None
    max_bound: Optional[Dict[str, Any]] = None


MIN_MAX_TESTS: list[MinMaxTest] = [
    MinMaxTest(
        "with_min_max",
        expected={"ok": 1.0},
        doc_count=100,
        key_pattern={"x": 1},
        min_bound={"x": 10},
        max_bound={"x": 50},
        msg="min/max range query should succeed",
    ),
    MinMaxTest(
        "min_max_no_match",
        expected={"numObjects": Int64(0)},
        key_pattern={"x": 1},
        min_bound={"x": 1000},
        max_bound={"x": 2000},
        msg="No match should return 0",
    ),
    MinMaxTest(
        "min_equal_max",
        expected={"numObjects": Int64(0)},
        key_pattern={"x": 1},
        min_bound={"x": 5},
        max_bound={"x": 5},
        msg="min==max should return 0",
    ),
    MinMaxTest(
        "min_greater_than_max",
        expected={"numObjects": Int64(0)},
        key_pattern={"x": 1},
        min_bound={"x": 50},
        max_bound={"x": 10},
        msg="min > max should return 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MIN_MAX_TESTS))
def test_dataSize_min_max(collection, test):
    """Test dataSize with min/max range parameters."""
    collection.insert_many([{"_id": i, "x": i} for i in range(test.doc_count)])
    collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    cmd = {"dataSize": ns, "keyPattern": test.key_pattern}
    if test.min_bound is not None:
        cmd["min"] = test.min_bound
    if test.max_bound is not None:
        cmd["max"] = test.max_bound
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, test.expected, msg=test.msg)


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
