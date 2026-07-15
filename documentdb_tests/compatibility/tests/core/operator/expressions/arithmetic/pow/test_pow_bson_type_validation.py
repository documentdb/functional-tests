"""
BSON type validation tests for $pow expression.

Verifies that $pow rejects invalid BSON types for its base and exponent input
positions and accepts valid numeric types. Systematically covers every BSON type
per position via the shared bson_type_validator harness. The base and exponent
positions report distinct error codes.

Arithmetic correctness for the accepted types lives in
test_pow_core_arithmetic.py and test_pow_boundaries_precision.py;
this file only asserts type acceptance (no error) vs. type rejection (error code).
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
from documentdb_tests.framework.error_codes import (
    POW_NON_NUMERIC_BASE_ERROR,
    POW_NON_NUMERIC_EXP_ERROR,
)

# $pow accepts the four numeric types in either position. null propagates to a
# null result, so it is treated as accepted. Every other BSON type is rejected;
# the base and exponent positions report distinct error codes.
NUMERIC_AND_NULL = [
    BsonType.DOUBLE,
    BsonType.INT,
    BsonType.LONG,
    BsonType.DECIMAL,
    BsonType.NULL,
]

POW_BSON_PARAMS = [
    BsonTypeTestCase(
        id="base",
        msg="$pow base should reject non-numeric types",
        keyword="base",
        valid_types=NUMERIC_AND_NULL,
        default_error_code=POW_NON_NUMERIC_BASE_ERROR,
    ),
    BsonTypeTestCase(
        id="exponent",
        msg="$pow exponent should reject non-numeric types",
        keyword="exponent",
        valid_types=NUMERIC_AND_NULL,
        default_error_code=POW_NON_NUMERIC_EXP_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(POW_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(POW_BSON_PARAMS)


def _build_pow_expr(spec, sample_value):
    """Build a $pow expression with sample_value in the position under test."""
    doc = {"value": sample_value}
    if spec.keyword == "base":
        return {"$pow": ["$value", 2]}, doc
    return {"$pow": [2, "$value"]}, doc


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_pow_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $pow rejects invalid BSON types per input position."""
    expression, doc = _build_pow_expr(spec, sample_value)
    result = execute_expression_with_insert(collection, expression, doc)
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg}: {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_pow_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $pow accepts valid numeric BSON types (and null) per position."""
    expression, doc = _build_pow_expr(spec, sample_value)
    result = execute_expression_with_insert(collection, expression, doc)
    assertNotError(result, msg=f"$pow {spec.keyword} should accept {bson_type.value}")
