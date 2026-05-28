"""Tests for dataSize command estimate parameter.

Covers explicit true/false behavioral tests, BSON type acceptance/rejection
via bson_type_validator framework, and response field presence.
"""

import pytest
from bson import Int64

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
from documentdb_tests.framework.property_checks import Exists
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin


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


ESTIMATE_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="estimate_type",
        msg="estimate should reject non-numeric/non-boolean/non-null types",
        keyword="estimate",
        valid_types=[
            BsonType.BOOL,
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

ESTIMATE_REJECTION_CASES = generate_bson_rejection_test_cases(ESTIMATE_TYPE_PARAMS)
ESTIMATE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(ESTIMATE_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ESTIMATE_REJECTION_CASES)
def test_dataSize_estimate_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dataSize rejects non-numeric/non-boolean/non-null BSON types for estimate."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": sample_value})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ESTIMATE_ACCEPTANCE_CASES)
def test_dataSize_estimate_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test dataSize accepts numeric, boolean, and null BSON types for estimate."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)
