"""Tests for logRotate BSON type validation.

The value field accepts numeric/bool types and the string "server"; other
types are rejected with TypeMismatch. The comment field accepts all BSON
types and is consumed by the server rather than echoed back in the response.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import FILE_RENAME_FAILED_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import (
    execute_admin_command,
    execute_admin_with_retry_command,
)
from documentdb_tests.framework.property_checks import Eq, NotExists

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


LOG_ROTATE_VALUE_PARAMS = [
    BsonTypeTestCase(
        id="logRotate_value",
        msg="logRotate value should accept numeric, bool, and the 'server' string",
        keyword="logRotate",
        valid_types=[
            BsonType.INT,
            BsonType.DOUBLE,
            BsonType.LONG,
            BsonType.BOOL,
            BsonType.DECIMAL,
            BsonType.STRING,
        ],
        valid_inputs={BsonType.STRING: "server"},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

COMMENT_PARAMS = [
    BsonTypeTestCase(
        id="comment",
        msg="logRotate should accept all BSON types for the comment field",
        keyword="comment",
        valid_types=list(BsonType),
    ),
]


LOG_ROTATE_VALUE_ACCEPTANCE = generate_bson_acceptance_test_cases(LOG_ROTATE_VALUE_PARAMS)
LOG_ROTATE_VALUE_REJECTIONS = generate_bson_rejection_test_cases(LOG_ROTATE_VALUE_PARAMS)
COMMENT_ACCEPTANCE = generate_bson_acceptance_test_cases(COMMENT_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", LOG_ROTATE_VALUE_ACCEPTANCE)
def test_logRotate_value_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test logRotate accepts numeric, bool, and the 'server' string value."""
    result = execute_admin_with_retry_command(
        collection, {"logRotate": sample_value}, retry_code=FILE_RENAME_FAILED_ERROR
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg=f"{spec.msg} (bson_type={bson_type.value})",
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", COMMENT_ACCEPTANCE)
def test_logRotate_comment_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test comment field accepts all BSON types and is consumed, not echoed back."""
    result = execute_admin_with_retry_command(
        collection, {"logRotate": 1, "comment": sample_value}, retry_code=FILE_RENAME_FAILED_ERROR
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "comment": NotExists()},
        msg=f"comment should be accepted and not echoed back ({bson_type.value})",
        raw_res=True,
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", LOG_ROTATE_VALUE_REJECTIONS)
def test_logRotate_value_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test logRotate value rejects non-numeric, non-string BSON types."""
    result = execute_admin_command(collection, {"logRotate": sample_value})
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"logRotate should reject {bson_type.value} for the command value",
    )
