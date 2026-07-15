"""
BSON type validation tests for $multiply expression.

Verifies that $multiply rejects invalid BSON types for its numeric operands and
accepts valid numeric types. Systematically covers every BSON type via the
shared bson_type_validator harness.

Arithmetic correctness for the accepted types lives in
test_operator_multiply_type_matrix.py; this file only asserts type acceptance
(no error) vs. type rejection (error code).
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

# $multiply accepts the four numeric types in every operand position. null is
# not a type error — it propagates to a null result — so it is treated as
# accepted. Every other BSON type is rejected with TYPE_MISMATCH_ERROR.
NUMERIC_AND_NULL = [
    BsonType.DOUBLE,
    BsonType.INT,
    BsonType.LONG,
    BsonType.DECIMAL,
    BsonType.NULL,
]

MULTIPLY_BSON_PARAMS = [
    BsonTypeTestCase(
        id="operand",
        msg="$multiply should reject non-numeric operands",
        keyword="operand",
        valid_types=NUMERIC_AND_NULL,
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="single_operand_literal",
        msg="$multiply should reject non-numeric single literal operand",
        keyword="single_operand_literal",
        valid_types=NUMERIC_AND_NULL,
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(MULTIPLY_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(MULTIPLY_BSON_PARAMS)


def _build_multiply_expr(spec, sample_value):
    """Build a $multiply expression exercising the given operand shape.

    "operand": two operands via field reference (the value under test plus a
    fixed valid literal) — exercises the arity-2, field-ref evaluation path.
    "single_operand_literal": a single operand embedded directly as a literal
    in the expression (no field reference, no document) — exercises the
    arity-1, literal-parsing path, which "operand" cannot reach.
    """
    if spec.id == "single_operand_literal":
        return {"$multiply": [sample_value]}, {}
    return {"$multiply": ["$value", 2]}, {"value": sample_value}


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_multiply_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $multiply rejects invalid BSON types for an operand."""
    expression, doc = _build_multiply_expr(spec, sample_value)
    result = execute_expression_with_insert(collection, expression, doc)
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg}: {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_multiply_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $multiply accepts valid numeric BSON types (and null)."""
    expression, doc = _build_multiply_expr(spec, sample_value)
    result = execute_expression_with_insert(collection, expression, doc)
    assertNotError(result, msg=f"$multiply should accept {bson_type.value}")
