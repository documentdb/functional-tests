"""$toBool return-type invariant and idempotency tests."""

import pytest

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
from documentdb_tests.framework.test_constants import INT32_ZERO, MISSING

# Property [Return Type]: $toBool always returns BSON type "bool" for any non-null, non-missing
# input. ARRAY and OBJECT samples are wrapped with $literal to pass as plain values rather than
# being parsed as expressions.
RETURN_TYPE_BOOL_SPEC = [
    BsonTypeTestCase(
        id="toBool_return_type",
        msg="$toBool always returns BSON type bool for a successful conversion",
        valid_types=[
            BsonType.BOOL,
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.STRING,
            BsonType.DATE,
            BsonType.BIN_DATA,
            BsonType.OBJECT_ID,
            BsonType.REGEX,
            BsonType.JAVASCRIPT,
            BsonType.TIMESTAMP,
            BsonType.MIN_KEY,
            BsonType.MAX_KEY,
            BsonType.ARRAY,
            BsonType.OBJECT,
        ],
        valid_inputs={
            BsonType.ARRAY: {"$literal": ["a", "b", "c"]},
            BsonType.OBJECT: {"$literal": {"key": "value"}},
        },
    ),
]

RETURN_TYPE_BOOL_CASES = generate_bson_acceptance_test_cases(RETURN_TYPE_BOOL_SPEC)

_BOOL_EXPR_FORMS = [
    pytest.param(lambda v: {"$toBool": v}, id="toBool"),
    pytest.param(lambda v: {"$convert": {"input": v, "to": "bool"}}, id="convert"),
]


@pytest.mark.parametrize("expr_fn", _BOOL_EXPR_FORMS)
@pytest.mark.parametrize("bson_type,sample_value,spec", RETURN_TYPE_BOOL_CASES)
def test_toBool_return_type_is_bool(collection, bson_type, sample_value, spec, expr_fn):
    """$toBool and $convert to bool always return BSON type 'bool' for a successful conversion."""
    result = execute_expression(collection, {"$type": expr_fn(sample_value)})
    assert_expression_result(result, expected="bool", msg=f"{spec.msg} ({bson_type.value} input)")


# Property [Return Type - Null]: $toBool returns BSON type "null" for null or missing inputs.
TOBOOL_RETURN_TYPE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="$toBool of null returns null type",
        expression={"$type": {"$toBool": None}},
        expected="null",
    ),
    ExpressionTestCase(
        "missing",
        msg="$toBool of missing field returns null type",
        expression={"$type": {"$toBool": MISSING}},
        expected="null",
    ),
]

# Property [Idempotency]: applying $toBool twice produces the same result as applying it once
# for representative truthy, falsy, and null inputs.
TOBOOL_IDEMPOTENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "idempotent_true",
        msg="$toBool is idempotent for true",
        expression={"$toBool": {"$toBool": True}},
        expected=True,
    ),
    ExpressionTestCase(
        "idempotent_false",
        msg="$toBool is idempotent for false",
        expression={"$toBool": {"$toBool": False}},
        expected=False,
    ),
    ExpressionTestCase(
        "idempotent_null",
        msg="$toBool is idempotent for null",
        expression={"$toBool": {"$toBool": None}},
        expected=None,
    ),
    ExpressionTestCase(
        "idempotent_int_truthy",
        msg="$toBool is idempotent for a truthy int32 (once converts to bool, twice is same)",
        expression={"$toBool": {"$toBool": 1}},
        expected=True,
    ),
    ExpressionTestCase(
        "idempotent_int_falsy",
        msg="$toBool is idempotent for a falsy int32 (once converts to bool, twice is same)",
        expression={"$toBool": {"$toBool": INT32_ZERO}},
        expected=False,
    ),
    ExpressionTestCase(
        "idempotent_string",
        msg="$toBool is idempotent for a string (truthy string converts to bool, then stays)",
        expression={"$toBool": {"$toBool": "hello"}},
        expected=True,
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOBOOL_RETURN_TYPE_NULL_TESTS + TOBOOL_IDEMPOTENCY_TESTS)
)
def test_toBool_return_type_null_and_idempotency(collection, test: ExpressionTestCase):
    """$toBool returns BSON type 'null' for null or missing input and is idempotent."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
