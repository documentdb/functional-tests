"""$toDecimal return-type invariant and idempotency tests."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_ZERO,
    DOUBLE_TWO_AND_HALF,
    MISSING,
)

# Property [Return Type]: $toDecimal always returns BSON type 'decimal' for successful
# conversions and null for null or missing inputs.
RETURN_TYPE_DECIMAL_SPEC = [
    BsonTypeTestCase(
        id="toDecimal_return_type",
        msg="$toDecimal always returns BSON type decimal for a successful conversion",
        valid_types=[
            BsonType.BOOL,
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.STRING,
            BsonType.DATE,
        ],
        valid_inputs={
            BsonType.STRING: "7.5",
        },
    ),
]

RETURN_TYPE_DECIMAL_CASES = generate_bson_acceptance_test_cases(RETURN_TYPE_DECIMAL_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", RETURN_TYPE_DECIMAL_CASES)
def test_toDecimal_return_type_is_decimal(collection, bson_type, sample_value, spec):
    """$toDecimal always returns BSON type 'decimal' for a successful conversion."""
    result = execute_expression(collection, {"$type": {"$toDecimal": sample_value}})
    assert_expression_result(
        result, expected="decimal", msg=f"{spec.msg} ({bson_type.value} input)"
    )


# Property [Return Type — Null]: $toDecimal returns BSON type null for null or missing inputs.
TODECIMAL_RETURN_TYPE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_null",
        msg="$toDecimal of null returns null type",
        expression={"$type": {"$toDecimal": None}},
        expected="null",
    ),
    ExpressionTestCase(
        "return_type_missing",
        msg="$toDecimal of missing returns null type",
        expression={"$type": {"$toDecimal": MISSING}},
        expected="null",
    ),
]


# Property [Idempotency]: applying $toDecimal twice produces the same result as once.
TODECIMAL_IDEMPOTENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "idempotent_bool",
        msg="$toDecimal is idempotent for bool",
        expression={"$toDecimal": {"$toDecimal": True}},
        expected=Decimal128("1"),
    ),
    ExpressionTestCase(
        "idempotent_int32",
        msg="$toDecimal is idempotent for int32",
        expression={"$toDecimal": {"$toDecimal": 42}},
        expected=Decimal128("42"),
    ),
    ExpressionTestCase(
        "idempotent_int64",
        msg="$toDecimal is idempotent for int64",
        expression={"$toDecimal": {"$toDecimal": Int64(99)}},
        expected=Decimal128("99"),
    ),
    ExpressionTestCase(
        "idempotent_decimal128",
        msg="$toDecimal is idempotent for Decimal128",
        expression={"$toDecimal": {"$toDecimal": DECIMAL128_HALF}},
        expected=DECIMAL128_HALF,
    ),
    ExpressionTestCase(
        "idempotent_zero",
        msg="$toDecimal is idempotent for zero",
        expression={"$toDecimal": {"$toDecimal": DECIMAL128_ZERO}},
        expected=DECIMAL128_ZERO,
    ),
    ExpressionTestCase(
        "idempotent_double",
        msg="$toDecimal is idempotent for double",
        expression={"$toDecimal": {"$toDecimal": DOUBLE_TWO_AND_HALF}},
        expected=Decimal128("2.50000000000000"),
    ),
    ExpressionTestCase(
        "idempotent_string",
        msg="$toDecimal is idempotent for numeric string",
        expression={"$toDecimal": {"$toDecimal": "7.5"}},
        expected=Decimal128("7.5"),
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TODECIMAL_RETURN_TYPE_NULL_TESTS + TODECIMAL_IDEMPOTENCY_TESTS)
)
def test_toDecimal_return_type_null(collection, test: ExpressionTestCase):
    """$toDecimal returns BSON type 'null' for null or missing input."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
