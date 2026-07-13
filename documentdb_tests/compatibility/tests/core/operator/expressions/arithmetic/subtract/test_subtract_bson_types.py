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

# Property [Minuend type acceptance]: $subtract accepts numeric and date types as minuend.
# Property [Minuend type rejection]: $subtract rejects all other BSON types as minuend.
SUBTRACT_MINUEND_SPEC = BsonTypeTestCase(
    id="subtract_minuend",
    msg="$subtract minuend type",
    valid_types=[
        BsonType.DOUBLE,
        BsonType.INT,
        BsonType.LONG,
        BsonType.DECIMAL,
        BsonType.DATE,
        BsonType.NULL,
    ],
)

# Property [Subtrahend type acceptance]: $subtract accepts numeric types as subtrahend.
# Property [Subtrahend type rejection]: $subtract rejects all other BSON types as subtrahend,
# including Date when the minuend is numeric.
SUBTRACT_SUBTRAHEND_SPEC = BsonTypeTestCase(
    id="subtract_subtrahend",
    msg="$subtract subtrahend type",
    valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL, BsonType.NULL],
)

MINUEND_REJECTION_CASES = generate_bson_rejection_test_cases([SUBTRACT_MINUEND_SPEC])
MINUEND_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases([SUBTRACT_MINUEND_SPEC])
SUBTRAHEND_REJECTION_CASES = generate_bson_rejection_test_cases([SUBTRACT_SUBTRAHEND_SPEC])
SUBTRAHEND_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases([SUBTRACT_SUBTRAHEND_SPEC])


@pytest.mark.parametrize("bson_type,sample_value,spec", MINUEND_REJECTION_CASES)
def test_subtract_rejects_invalid_minuend(collection, bson_type, sample_value, spec):
    """Test $subtract rejects invalid BSON types as the minuend."""
    result = execute_expression_with_insert(collection, {"$subtract": [sample_value, 1]}, {})
    assert_expression_result(result, error_code=spec.expected_code(bson_type))


@pytest.mark.parametrize("bson_type,sample_value,spec", MINUEND_ACCEPTANCE_CASES)
def test_subtract_accepts_valid_minuend(collection, bson_type, sample_value, spec):
    """Test $subtract accepts valid BSON types (numeric and date) as the minuend."""
    result = execute_expression_with_insert(collection, {"$subtract": [sample_value, 1]}, {})
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


@pytest.mark.parametrize("bson_type,sample_value,spec", SUBTRAHEND_REJECTION_CASES)
def test_subtract_rejects_invalid_subtrahend(collection, bson_type, sample_value, spec):
    """Test $subtract rejects invalid BSON types as the subtrahend."""
    result = execute_expression_with_insert(collection, {"$subtract": [10, sample_value]}, {})
    assert_expression_result(result, error_code=spec.expected_code(bson_type))


@pytest.mark.parametrize("bson_type,sample_value,spec", SUBTRAHEND_ACCEPTANCE_CASES)
def test_subtract_accepts_valid_subtrahend(collection, bson_type, sample_value, spec):
    """Test $subtract accepts valid BSON types (numeric) as the subtrahend."""
    result = execute_expression_with_insert(collection, {"$subtract": [10, sample_value]}, {})
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")
