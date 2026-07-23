"""$toLong return-type invariant and idempotency tests."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64

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
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    MISSING,
)

# Property [Return Type]: $toLong always returns BSON type long for successful conversions
# and null for null or missing inputs.
# NULL is skipped from rejection because $toLong(null) returns null (not an error).
# OBJECT and ARRAY are skipped because they need $literal wrapping to avoid being parsed
# as MongoDB expressions — their rejection is verified in test_toLong_datetime_binary.py.
RETURN_TYPE_LONG_SPEC = [
    BsonTypeTestCase(
        id="toLong_return_type",
        msg="$toLong always returns BSON type long for a successful conversion",
        valid_types=[
            BsonType.BOOL,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.STRING,
            BsonType.DATE,
            BsonType.BIN_DATA,
        ],
        skip_rejection_types=[
            BsonType.NULL,
            BsonType.OBJECT,
            BsonType.ARRAY,
        ],
        default_error_code=CONVERSION_FAILURE_ERROR,
        valid_inputs={
            BsonType.STRING: "42",
            BsonType.BIN_DATA: Binary(b"\x05"),
        },
    ),
]

RETURN_TYPE_LONG_CASES = generate_bson_acceptance_test_cases(RETURN_TYPE_LONG_SPEC)
REJECTION_LONG_CASES = generate_bson_rejection_test_cases(RETURN_TYPE_LONG_SPEC)

_LONG_EXPR_FORMS = [
    pytest.param(lambda v: {"$toLong": v}, id="toLong"),
    pytest.param(lambda v: {"$convert": {"input": v, "to": "long"}}, id="convert"),
]


@pytest.mark.parametrize("expr_fn", _LONG_EXPR_FORMS)
@pytest.mark.parametrize("bson_type,sample_value,spec", RETURN_TYPE_LONG_CASES)
def test_toLong_return_type_is_long(collection, bson_type, sample_value, spec, expr_fn):
    """$toLong and $convert to long always return BSON type 'long'."""
    result = execute_expression(collection, {"$type": expr_fn(sample_value)})
    assert_expression_result(result, expected="long", msg=f"{spec.msg} ({bson_type.value} input)")


@pytest.mark.parametrize("expr_fn", _LONG_EXPR_FORMS)
@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_LONG_CASES)
def test_toLong_rejects_unsupported_type(collection, bson_type, sample_value, spec, expr_fn):
    """$toLong and $convert to long reject BSON types they cannot convert."""
    result = execute_expression(collection, expr_fn(sample_value))
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"$toLong should reject {bson_type.value} input",
    )


# Property [Return Type — Null]: $toLong returns BSON type null for null or missing inputs.
TOLONG_RETURN_TYPE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="$toLong of null returns null type",
        expression={"$type": {"$toLong": None}},
        expected="null",
    ),
    ExpressionTestCase(
        "missing",
        msg="$toLong of missing returns null type",
        expression={"$type": {"$toLong": MISSING}},
        expected="null",
    ),
]


# Property [Idempotency]: applying $toLong twice produces the same result as applying it once.
TOLONG_IDEMPOTENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "idempotent_bool",
        msg="$toLong is idempotent for bool",
        expression={"$toLong": {"$toLong": True}},
        expected=Int64(1),
    ),
    ExpressionTestCase(
        "idempotent_int32",
        msg="$toLong is idempotent for int32",
        expression={"$toLong": {"$toLong": 42}},
        expected=Int64(42),
    ),
    ExpressionTestCase(
        "idempotent_int64",
        msg="$toLong is idempotent for int64",
        expression={"$toLong": {"$toLong": Int64(99)}},
        expected=Int64(99),
    ),
    ExpressionTestCase(
        "idempotent_double",
        msg="$toLong is idempotent for double",
        expression={"$toLong": {"$toLong": 3.7}},
        expected=Int64(3),
    ),
    ExpressionTestCase(
        "idempotent_decimal128",
        msg="$toLong is idempotent for Decimal128",
        expression={"$toLong": {"$toLong": Decimal128("8.9")}},
        expected=Int64(8),
    ),
    ExpressionTestCase(
        "idempotent_string",
        msg="$toLong is idempotent for numeric string",
        expression={"$toLong": {"$toLong": "55"}},
        expected=Int64(55),
    ),
    ExpressionTestCase(
        "idempotent_datetime",
        msg="$toLong is idempotent for datetime",
        expression={"$toLong": {"$toLong": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        expected=Int64(1_704_067_200_000),
    ),
    ExpressionTestCase(
        "idempotent_binary",
        msg="$toLong is idempotent for 1-byte binary",
        expression={"$toLong": {"$toLong": Binary(b"\x05")}},
        expected=Int64(5),
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOLONG_RETURN_TYPE_NULL_TESTS + TOLONG_IDEMPOTENCY_TESTS)
)
def test_toLong_return_type_null(collection, test: ExpressionTestCase):
    """$toLong returns BSON type 'null' for null or missing input."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
