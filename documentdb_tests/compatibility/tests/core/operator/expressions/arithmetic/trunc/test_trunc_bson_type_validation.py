"""
BSON type validation tests for $trunc expression.

Systematically verifies that the number (first) input accepts the four numeric
types plus null, and rejects every other BSON type. The `place`-position
validation lives in test_trunc_errors.py.
"""

import pytest

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
from documentdb_tests.framework.error_codes import NON_NUMERIC_TYPE_ERROR

TRUNC_BSON_PARAMS = [
    BsonTypeTestCase(
        id="number",
        msg="$trunc number should reject non-numeric types",
        keyword="number",
        valid_types=[
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=NON_NUMERIC_TYPE_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(TRUNC_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TRUNC_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_trunc_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $trunc rejects invalid BSON types for the number input."""
    result = execute_expression_with_insert(
        collection, {"$trunc": "$value"}, {"value": sample_value}
    )
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg}: {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_trunc_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $trunc accepts valid numeric BSON types (and null)."""
    result = execute_expression_with_insert(
        collection, {"$trunc": "$value"}, {"value": sample_value}
    )
    assertNotError(result, msg=f"$trunc number should accept {bson_type.value}")
