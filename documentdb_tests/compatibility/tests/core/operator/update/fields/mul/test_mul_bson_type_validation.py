"""
BSON type validation tests for $mul update field operator.

Verifies that $mul rejects non-numeric BSON types for both the multiplier
value and the target field value, and accepts all numeric types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

BSON_PARAMS = [
    BsonTypeTestCase(
        id="multiplier",
        msg="$mul should reject non-numeric multiplier types",
        keyword="multiplier",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 2.0,
            BsonType.INT: 2,
            BsonType.LONG: Int64(2),
            BsonType.DECIMAL: Decimal128("2"),
        },
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="target_field",
        msg="$mul should reject non-numeric target field types",
        keyword="target_field",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        valid_inputs={
            BsonType.DOUBLE: 10.0,
            BsonType.INT: 10,
            BsonType.LONG: Int64(10),
            BsonType.DECIMAL: Decimal128("10"),
        },
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

REJECTION_TESTS = generate_bson_rejection_test_cases(BSON_PARAMS)
ACCEPTANCE_TESTS = generate_bson_acceptance_test_cases(BSON_PARAMS)


def _build_setup_doc(spec, sample_value):
    """Build the document to insert before the update."""
    if spec.keyword == "multiplier":
        return {"_id": 1, "val": 10}
    return {"_id": 1, "val": sample_value}


def _build_update(spec, sample_value):
    """Build the $mul update command."""
    if spec.keyword == "multiplier":
        return {"$mul": {"val": sample_value}}
    return {"$mul": {"val": 2}}


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_TESTS)
def test_mul_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $mul rejects invalid BSON types."""
    setup_doc = _build_setup_doc(spec, sample_value)
    update = _build_update(spec, sample_value)
    collection.insert_one(setup_doc)
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": update}]},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_TESTS)
def test_mul_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $mul accepts numeric BSON types."""
    setup_doc = _build_setup_doc(spec, sample_value)
    update = _build_update(spec, sample_value)
    collection.insert_one(setup_doc)
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": update}]},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1},
        msg=f"$mul should accept {bson_type.value} for {spec.keyword}",
    )
