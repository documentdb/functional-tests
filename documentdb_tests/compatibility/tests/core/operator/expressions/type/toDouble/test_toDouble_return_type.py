"""$toDouble return-type invariant and idempotency tests."""

import struct
from datetime import datetime, timezone

import pytest
from bson import Binary, Int64

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
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_TWO_AND_HALF,
    MISSING,
)

# Property [Return Type]: $toDouble always returns BSON type double for successful conversions
# and null for null or missing inputs.
RETURN_TYPE_DOUBLE_SPEC = [
    BsonTypeTestCase(
        id="toDouble_return_type",
        msg="$toDouble always returns BSON type double for a successful conversion",
        valid_types=[
            BsonType.BOOL,
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.STRING,
            BsonType.DATE,
            BsonType.BIN_DATA,
        ],
        valid_inputs={
            BsonType.STRING: "7.5",
            BsonType.BIN_DATA: Binary(struct.pack("<d", 1.0)),
        },
    ),
]

RETURN_TYPE_DOUBLE_CASES = generate_bson_acceptance_test_cases(RETURN_TYPE_DOUBLE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", RETURN_TYPE_DOUBLE_CASES)
def test_toDouble_return_type_is_double(collection, bson_type, sample_value, spec):
    """$toDouble always returns BSON type 'double' for a successful conversion."""
    result = execute_expression(collection, {"$type": {"$toDouble": sample_value}})
    assert_expression_result(result, expected="double", msg=f"{spec.msg} ({bson_type.value} input)")


# Property [Return Type — Null]: $toDouble returns BSON type null for null or missing inputs.
TODOUBLE_RETURN_TYPE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="$toDouble of null returns null type",
        expression={"$type": {"$toDouble": None}},
        expected="null",
    ),
    ExpressionTestCase(
        "missing",
        msg="$toDouble of missing returns null type",
        expression={"$type": {"$toDouble": MISSING}},
        expected="null",
    ),
]


# Property [Idempotency]: applying $toDouble twice produces the same result as applying it once.
TODOUBLE_IDEMPOTENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "idempotent_bool",
        msg="$toDouble is idempotent for bool",
        expression={"$toDouble": {"$toDouble": True}},
        expected=1.0,
    ),
    ExpressionTestCase(
        "idempotent_double",
        msg="$toDouble is idempotent for double",
        expression={"$toDouble": {"$toDouble": 3.14}},
        expected=3.14,
    ),
    ExpressionTestCase(
        "idempotent_int32",
        msg="$toDouble is idempotent for int32",
        expression={"$toDouble": {"$toDouble": 42}},
        expected=42.0,
    ),
    ExpressionTestCase(
        "idempotent_int64",
        msg="$toDouble is idempotent for int64",
        expression={"$toDouble": {"$toDouble": Int64(99)}},
        expected=99.0,
    ),
    ExpressionTestCase(
        "idempotent_decimal128",
        msg="$toDouble is idempotent for Decimal128",
        expression={"$toDouble": {"$toDouble": DECIMAL128_TWO_AND_HALF}},
        expected=DOUBLE_TWO_AND_HALF,
    ),
    ExpressionTestCase(
        "idempotent_string",
        msg="$toDouble is idempotent for numeric string",
        expression={"$toDouble": {"$toDouble": "7.5"}},
        expected=7.5,
    ),
    ExpressionTestCase(
        "idempotent_datetime",
        msg="$toDouble is idempotent for datetime",
        expression={"$toDouble": {"$toDouble": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        expected=1_704_067_200_000.0,
    ),
    ExpressionTestCase(
        "idempotent_binary_8byte",
        msg="$toDouble is idempotent for 8-byte binary",
        expression={"$toDouble": {"$toDouble": Binary(struct.pack("<d", 5.0))}},
        expected=5.0,
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TODOUBLE_RETURN_TYPE_NULL_TESTS + TODOUBLE_IDEMPOTENCY_TESTS)
)
def test_toDouble_return_type_null(collection, test: ExpressionTestCase):
    """$toDouble returns BSON type 'null' for null or missing input."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
