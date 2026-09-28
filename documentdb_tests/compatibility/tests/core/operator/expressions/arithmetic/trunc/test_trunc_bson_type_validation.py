"""
BSON type validation tests for $trunc expression.

Verifies the number (first) and place (second) inputs each accept the four
numeric types plus null, and reject every other BSON type. Value-level place
validation (out-of-range, non-integral, NaN/infinity) lives in
test_trunc_errors.py.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import INVALID_TYPE_ERROR, NON_NUMERIC_TYPE_ERROR

TRUNC_BSON_PARAMS = [
    BsonTypeTestCase(
        id="number",
        msg="$trunc number should reject non-numeric types",
        keyword="number",
        # The four numeric types plus null (null propagates to a null result).
        valid_types=[
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=NON_NUMERIC_TYPE_ERROR,
    ),
    BsonTypeTestCase(
        id="place",
        msg="$trunc place should reject non-numeric types",
        keyword="place",
        # The four numeric types plus null (null place propagates to a null result).
        valid_types=[
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=INVALID_TYPE_ERROR,
        valid_inputs={
            BsonType.DOUBLE: 2.0,
            BsonType.INT: 2,
            BsonType.LONG: Int64(2),
            BsonType.DECIMAL: Decimal128("2"),
        },
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(TRUNC_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TRUNC_BSON_PARAMS)


def _trunc_expression(spec):
    """Build the $trunc expression for the argument under test."""
    if spec.keyword == "place":
        return {"$trunc": ["$value", "$place"]}
    return {"$trunc": "$value"}


def _trunc_document(spec, sample_value):
    """Build the inserted document for the argument under test."""
    if spec.keyword == "place":
        return {"value": 3.14159, "place": sample_value}
    return {"value": sample_value}


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_trunc_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $trunc rejects invalid BSON types for the number and place inputs."""
    result = execute_expression_with_insert(
        collection, _trunc_expression(spec), _trunc_document(spec, sample_value)
    )
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg}: {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_trunc_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $trunc accepts valid numeric BSON types (and null) for number and place."""
    result = execute_expression_with_insert(
        collection, _trunc_expression(spec), _trunc_document(spec, sample_value)
    )
    assertNotError(result, msg=f"$trunc {spec.keyword} should accept {bson_type.value}")
