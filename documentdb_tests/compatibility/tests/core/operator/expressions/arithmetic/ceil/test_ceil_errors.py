"""Tests for $ceil type mismatch and arity error cases."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    NON_NUMERIC_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

_NUMERIC_AND_NULL_TYPES = [
    BsonType.DOUBLE,
    BsonType.INT,
    BsonType.LONG,
    BsonType.DECIMAL,
    BsonType.NULL,
]

# Property [Type Strictness]: $ceil rejects all non-numeric, non-null BSON types.
CEIL_TYPE_SPEC = BsonTypeTestCase(
    id="ceil_input",
    msg="$ceil should reject non-numeric input",
    keyword="$ceil",
    valid_types=_NUMERIC_AND_NULL_TYPES,
    default_error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
)

CEIL_TYPE_REJECTION_CASES = generate_bson_rejection_test_cases([CEIL_TYPE_SPEC])


@pytest.mark.parametrize("bson_type,sample_value,spec", CEIL_TYPE_REJECTION_CASES)
def test_ceil_rejects_non_numeric_input(collection, bson_type, sample_value, spec):
    """Test $ceil rejects non-numeric BSON types."""
    result = execute_expression_with_insert(
        collection, {"$ceil": ["$value"]}, {"value": sample_value}
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


# Property [Array Input]: $ceil rejects array-typed input; it does not apply element-wise.
# Property [Arity]: $ceil requires exactly one argument.
CEIL_ARGUMENT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_field_path",
        doc={"a": [{"b": 1.5}]},
        expression={"$ceil": "$a.b"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$ceil should reject a field path that resolves to an array",
    ),
    ExpressionTestCase(
        "arity_zero",
        doc={},
        expression={"$ceil": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$ceil should reject zero arguments",
    ),
    ExpressionTestCase(
        "arity_two",
        doc={},
        expression={"$ceil": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$ceil should reject two arguments",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CEIL_ARGUMENT_ERROR_TESTS))
def test_ceil_argument_errors(collection, test_case: ExpressionTestCase):
    """Test $ceil rejects invalid argument count and array-typed input."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
