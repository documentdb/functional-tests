"""
BSON type validation tests for $mod expression.

Verifies that $mod rejects invalid BSON types for its dividend and divisor
input positions, and accepts valid numeric types, via the shared
bson_type_validator harness.
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
from documentdb_tests.framework.error_codes import MODULO_NON_NUMERIC_ERROR

# $mod accepts the four numeric types in either position. null is not a type
# error — it propagates to a null result — so it is treated as accepted
# (assertNotError below tolerates the null result). Every other BSON type is
# rejected with MODULO_NON_NUMERIC_ERROR (16611).
NUMERIC_AND_NULL = [
    BsonType.DOUBLE,
    BsonType.INT,
    BsonType.LONG,
    BsonType.DECIMAL,
    BsonType.NULL,
]

MOD_BSON_PARAMS = [
    BsonTypeTestCase(
        id="dividend",
        msg="$mod dividend should reject non-numeric types",
        keyword="dividend",
        valid_types=NUMERIC_AND_NULL,
        default_error_code=MODULO_NON_NUMERIC_ERROR,
    ),
    BsonTypeTestCase(
        id="divisor",
        msg="$mod divisor should reject non-numeric types",
        keyword="divisor",
        valid_types=NUMERIC_AND_NULL,
        default_error_code=MODULO_NON_NUMERIC_ERROR,
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(MOD_BSON_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(MOD_BSON_PARAMS)


def _build_mod_expr(spec, sample_value):
    """Build a $mod expression with sample_value in the position under test.

    The sample is injected via a field reference ("$value") so BSON types that
    cannot appear as aggregation literals are still exercised. The opposite
    operand is a fixed, valid numeric literal.
    """
    doc = {"value": sample_value}
    if spec.keyword == "dividend":
        return {"$mod": ["$value", 3]}, doc
    return {"$mod": [10, "$value"]}, doc


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_mod_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies $mod rejects invalid BSON types per input position."""
    expression, doc = _build_mod_expr(spec, sample_value)
    result = execute_expression_with_insert(collection, expression, doc)
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg}: {bson_type.value}",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_mod_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies $mod accepts valid numeric BSON types (and null) per position."""
    expression, doc = _build_mod_expr(spec, sample_value)
    result = execute_expression_with_insert(collection, expression, doc)
    assertNotError(result, msg=f"$mod {spec.keyword} should accept {bson_type.value}")
