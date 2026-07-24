"""
BSON type validation tests for $sqrt expression.

Systematically verifies that the single numeric input accepts the four numeric
types plus null, and rejects every other BSON type. Samples are non-negative so
acceptance does not trip the negative-input error.
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
from documentdb_tests.framework.error_codes import NON_NUMERIC_TYPE_MISMATCH_ERROR

SQRT_BSON_PARAMS = [
    BsonTypeTestCase(
        id="input",
        msg="$sqrt should reject non-numeric input",
        keyword="input",
        valid_types=[
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(SQRT_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SQRT_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_sqrt_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $sqrt rejects invalid BSON types."""
    result = execute_expression_with_insert(
        collection, {"$sqrt": "$value"}, {"value": sample_value}
    )
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg}: {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_sqrt_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $sqrt accepts valid numeric BSON types (and null)."""
    result = execute_expression_with_insert(
        collection, {"$sqrt": "$value"}, {"value": sample_value}
    )
    assertNotError(result, msg=f"$sqrt should accept {bson_type.value}")
