"""$toString return type, type rejection, idempotency, and field reference tests."""

import pytest
from bson import Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_HALF, MISSING

# Property [Return Type / Type Rejection]: BOOL, DOUBLE, INT, LONG, DECIMAL, STRING, DATE,
# OBJECT_ID, and BIN_DATA are the accepted types; all others produce a conversion failure.
# NULL is skipped from rejection because it returns null (not an error).
# ARRAY is skipped because it triggers arity semantics tested in test_toString_arity.py.
TOSTRING_BSON_TYPE_SPEC = [
    BsonTypeTestCase(
        id="toString",
        msg="$toString BSON type",
        valid_types=[
            BsonType.BOOL,
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.STRING,
            BsonType.DATE,
            BsonType.OBJECT_ID,
            BsonType.BIN_DATA,
        ],
        skip_rejection_types=[BsonType.NULL, BsonType.ARRAY],
        default_error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOSTRING_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TOSTRING_BSON_TYPE_SPEC)
TOSTRING_REJECTION_CASES = generate_bson_rejection_test_cases(TOSTRING_BSON_TYPE_SPEC)

_STRING_EXPR_FORMS = [
    pytest.param(lambda v: {"$toString": v}, id="toString"),
    pytest.param(
        lambda v: {"$convert": {"input": v, "to": "string", "format": "auto"}}, id="convert"
    ),
]


@pytest.mark.parametrize("expr_fn", _STRING_EXPR_FORMS)
@pytest.mark.parametrize("bson_type,sample_value,spec", TOSTRING_ACCEPTANCE_CASES)
def test_toString_return_type_is_string(collection, bson_type, sample_value, spec, expr_fn):
    """$toString and $convert to string always return BSON type 'string'."""
    result = execute_expression(collection, {"$type": expr_fn(sample_value)})
    assert_expression_result(result, expected="string", msg=f"{spec.msg} ({bson_type.value} input)")


@pytest.mark.parametrize("expr_fn", _STRING_EXPR_FORMS)
@pytest.mark.parametrize("bson_type,sample_value,spec", TOSTRING_REJECTION_CASES)
def test_toString_type_rejection(collection, bson_type, sample_value, spec, expr_fn):
    """$toString and $convert to string reject unsupported BSON types with a conversion failure."""
    result = execute_expression(collection, expr_fn(sample_value))
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg} ({bson_type.value} rejected)",
    )


# Property [Return Type — Null]: $toString returns BSON type null for null or missing inputs.
TOSTRING_RETURN_TYPE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="$toString of null returns BSON type 'null'",
        expression={"$type": {"$toString": None}},
        expected="null",
    ),
    ExpressionTestCase(
        "missing",
        msg="$toString of a missing field returns BSON type 'null'",
        expression={"$type": {"$toString": MISSING}},
        expected="null",
    ),
]

# Property [Idempotency]: applying $toString twice produces the same result as once,
# since the output of $toString is always a string, which $toString passes through unchanged.
TOSTRING_IDEMPOTENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "idempotent_int32",
        msg="$toString is idempotent for int32",
        expression={"$toString": {"$toString": -1}},
        expected="-1",
    ),
    ExpressionTestCase(
        "idempotent_int64",
        msg="$toString is idempotent for int64",
        expression={"$toString": {"$toString": Int64(99)}},
        expected="99",
    ),
    ExpressionTestCase(
        "idempotent_double",
        msg="$toString is idempotent for double",
        expression={"$toString": {"$toString": DOUBLE_HALF}},
        expected="0.5",
    ),
    ExpressionTestCase(
        "idempotent_bool",
        msg="$toString is idempotent for bool",
        expression={"$toString": {"$toString": False}},
        expected="false",
    ),
    ExpressionTestCase(
        "idempotent_decimal128",
        msg="$toString is idempotent for Decimal128",
        expression={"$toString": {"$toString": Decimal128("1.50")}},
        expected="1.50",
    ),
    ExpressionTestCase(
        "idempotent_objectid",
        msg="$toString is idempotent for ObjectId",
        expression={"$toString": {"$toString": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")}},
        expected="aaaaaaaaaaaaaaaaaaaaaaaa",
    ),
]

# Property [Field Reference]: $toString resolves field paths from inserted documents;
# missing fields return null.
TOSTRING_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_field",
        msg="int32 document field converts to its decimal string",
        expression={"$toString": "$v"},
        doc={"v": 42},
        expected="42",
    ),
    ExpressionTestCase(
        "string_field",
        msg="String document field passes through unchanged",
        expression={"$toString": "$v"},
        doc={"v": "hello"},
        expected="hello",
    ),
    ExpressionTestCase(
        "double_field",
        msg="double document field converts to its string representation",
        expression={"$toString": "$v"},
        doc={"v": 3.14},
        expected="3.14",
    ),
    ExpressionTestCase(
        "bool_field",
        msg="bool document field converts to 'true' or 'false'",
        expression={"$toString": "$v"},
        doc={"v": True},
        expected="true",
    ),
    ExpressionTestCase(
        "nested_field",
        msg="Nested dot-notation field path resolves and converts",
        expression={"$toString": "$doc.v"},
        doc={"doc": {"v": 42}},
        expected="42",
    ),
    ExpressionTestCase(
        "missing_field",
        msg="Missing top-level field returns null",
        expression={"$toString": "$v"},
        doc={},
        expected=None,
    ),
    ExpressionTestCase(
        "missing_nested_field",
        msg="Missing nested field returns null",
        expression={"$toString": "$doc.missing"},
        doc={"doc": {"x": 1}},
        expected=None,
    ),
    ExpressionTestCase(
        "composite_array_path",
        msg="Field path resolving to a composite array is a conversion failure",
        expression={"$toString": "$a.b"},
        doc={"a": [{"b": 1}, {"b": 2}]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(
        TOSTRING_RETURN_TYPE_NULL_TESTS
        + TOSTRING_IDEMPOTENCY_TESTS
        + with_convert_variants(TOSTRING_FIELD_REF_TESTS, "$toString", "string")
    ),
)
def test_toString_return_type_null_idempotency_and_field_ref(collection, test: ExpressionTestCase):
    """$toString returns null for null/missing, is idempotent, and resolves field paths."""
    if test.doc is not None:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
