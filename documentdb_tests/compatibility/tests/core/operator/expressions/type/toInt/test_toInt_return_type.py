"""$toInt return-type invariant and idempotency tests."""

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
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Return Type]: $toInt always returns BSON type int for successful conversions
# and null for null or missing inputs.
RETURN_TYPE_INT_SPEC = [
    BsonTypeTestCase(
        id="toInt_return_type",
        msg="$toInt always returns BSON type int for a successful conversion",
        valid_types=[
            BsonType.BOOL,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.STRING,
            BsonType.BIN_DATA,
        ],
        valid_inputs={
            BsonType.LONG: Int64(42),
            BsonType.STRING: "42",
            BsonType.BIN_DATA: Binary(b"\x2a\x00\x00\x00", 0),
        },
    ),
]

RETURN_TYPE_INT_CASES = generate_bson_acceptance_test_cases(RETURN_TYPE_INT_SPEC)

_INT_EXPR_FORMS = [
    pytest.param(lambda v: {"$toInt": v}, id="toInt"),
    pytest.param(lambda v: {"$convert": {"input": v, "to": "int"}}, id="convert"),
]


@pytest.mark.parametrize("expr_fn", _INT_EXPR_FORMS)
@pytest.mark.parametrize("bson_type,sample_value,spec", RETURN_TYPE_INT_CASES)
def test_toInt_return_type_is_int(collection, bson_type, sample_value, spec, expr_fn):
    """$toInt and $convert to int always return BSON type 'int'."""
    result = execute_expression(collection, {"$type": expr_fn(sample_value)})
    assert_expression_result(result, expected="int", msg=f"{spec.msg} ({bson_type.value} input)")


# Property [Return Type — Null]: $toInt returns BSON type null for null or missing inputs.
TOINT_RETURN_TYPE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="$toInt of null returns null type",
        expression={"$type": {"$toInt": None}},
        expected="null",
    ),
    ExpressionTestCase(
        "missing",
        msg="$toInt of missing returns null type",
        expression={"$type": {"$toInt": MISSING}},
        expected="null",
    ),
]


# Property [Idempotency]: applying $toInt twice produces the same result as applying it once.
TOINT_IDEMPOTENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "idempotent_bool",
        msg="$toInt is idempotent for bool",
        expression={"$toInt": {"$toInt": True}},
        expected=1,
    ),
    ExpressionTestCase(
        "idempotent_int32",
        msg="$toInt is idempotent for int32",
        expression={"$toInt": {"$toInt": 42}},
        expected=42,
    ),
    ExpressionTestCase(
        "idempotent_int64",
        msg="$toInt is idempotent for int64 (within int32 range)",
        expression={"$toInt": {"$toInt": Int64(99)}},
        expected=99,
    ),
    ExpressionTestCase(
        "idempotent_double",
        msg="$toInt is idempotent for double (truncated first pass)",
        expression={"$toInt": {"$toInt": 3.14}},
        expected=3,
    ),
    ExpressionTestCase(
        "idempotent_decimal128",
        msg="$toInt is idempotent for Decimal128",
        expression={"$toInt": {"$toInt": Decimal128("7")}},
        expected=7,
    ),
    ExpressionTestCase(
        "idempotent_string",
        msg="$toInt is idempotent for numeric string",
        expression={"$toInt": {"$toInt": "123"}},
        expected=123,
    ),
    ExpressionTestCase(
        "idempotent_binary",
        msg="$toInt is idempotent for 4-byte binary",
        expression={"$toInt": {"$toInt": Binary(b"\x2a\x00\x00\x00", 0)}},
        expected=42,
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOINT_RETURN_TYPE_NULL_TESTS + TOINT_IDEMPOTENCY_TESTS)
)
def test_toInt_return_type_null(collection, test: ExpressionTestCase):
    """$toInt returns BSON type 'null' for null or missing input."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
