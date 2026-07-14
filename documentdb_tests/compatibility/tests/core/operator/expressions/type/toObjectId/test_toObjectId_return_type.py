"""$toObjectId return-type invariant, idempotency, and type rejection tests."""

import pytest
from bson import ObjectId

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
from documentdb_tests.framework.test_constants import MISSING

# Property [Return Type / Type Rejection]: STRING (valid 24-char hex) and OBJECT_ID are the
# only accepted types; all others produce a conversion failure. STRING rejection is tested by
# content in test_toObjectId_string.py; ARRAY triggers arity semantics in
# test_toObjectId_arity.py — both are skipped here.
TOOBJECTID_BSON_TYPE_SPEC = [
    BsonTypeTestCase(
        id="toObjectId",
        msg="$toObjectId BSON type",
        valid_types=[BsonType.OBJECT_ID, BsonType.STRING],
        valid_inputs={BsonType.STRING: "507f1f77bcf86cd799439011"},
        skip_rejection_types=[BsonType.STRING, BsonType.NULL, BsonType.ARRAY],
        default_error_code=CONVERSION_FAILURE_ERROR,
    ),
]

RETURN_TYPE_OBJECTID_CASES = generate_bson_acceptance_test_cases(TOOBJECTID_BSON_TYPE_SPEC)
TOOBJECTID_REJECTION_CASES = generate_bson_rejection_test_cases(TOOBJECTID_BSON_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", RETURN_TYPE_OBJECTID_CASES)
def test_toObjectId_return_type_is_objectId(collection, bson_type, sample_value, spec):
    """$toObjectId always returns BSON type 'objectId' for a successful conversion."""
    result = execute_expression(collection, {"$type": {"$toObjectId": sample_value}})
    assert_expression_result(
        result, expected="objectId", msg=f"{spec.msg} ({bson_type.value} input)"
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", TOOBJECTID_REJECTION_CASES)
def test_toObjectId_type_rejection(collection, bson_type, sample_value, spec):
    """$toObjectId rejects all non-string, non-objectId BSON types with conversion failure."""
    result = execute_expression(collection, {"$toObjectId": sample_value})
    assert_expression_result(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.msg} ({bson_type.value} rejected)",
    )


# Property [Return Type - Null]: $toObjectId returns BSON type null for null or missing inputs.
TOOBJECTID_RETURN_TYPE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="$toObjectId of null returns null type",
        expression={"$type": {"$toObjectId": None}},
        expected="null",
    ),
    ExpressionTestCase(
        "missing",
        msg="$toObjectId of a missing field returns null type",
        expression={"$type": {"$toObjectId": MISSING}},
        expected="null",
    ),
]

# Property [Idempotency]: applying $toObjectId twice produces the same result as once.
TOOBJECTID_IDEMPOTENCY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "idempotent_string",
        msg="$toObjectId is idempotent for a valid hex string (string → ObjectId → ObjectId)",
        expression={"$toObjectId": {"$toObjectId": "507f1f77bcf86cd799439011"}},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "idempotent_objectid",
        msg="$toObjectId is idempotent for ObjectId input",
        expression={"$toObjectId": {"$toObjectId": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")}},
        expected=ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"),
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOOBJECTID_RETURN_TYPE_NULL_TESTS + TOOBJECTID_IDEMPOTENCY_TESTS)
)
def test_toObjectId_return_type_null_and_idempotency(collection, test: ExpressionTestCase):
    """$toObjectId returns null type for null/missing input and is idempotent."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
