"""
BSON type validation tests for $sigmoid expression.

Systematically verifies that the single numeric input accepts the four numeric
types plus null, and rejects every other BSON type (generic code 14).
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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR

SIGMOID_BSON_PARAMS = [
    BsonTypeTestCase(
        id="input",
        msg="$sigmoid should reject non-numeric input",
        keyword="input",
        valid_types=[
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(SIGMOID_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SIGMOID_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_sigmoid_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $sigmoid rejects invalid BSON types."""
    result = execute_expression_with_insert(
        collection, {"$sigmoid": "$value"}, {"value": sample_value}
    )
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg}: {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_sigmoid_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $sigmoid accepts valid numeric BSON types (and null)."""
    result = execute_expression_with_insert(
        collection, {"$sigmoid": "$value"}, {"value": sample_value}
    )
    assertNotError(result, msg=f"$sigmoid should accept {bson_type.value}")
