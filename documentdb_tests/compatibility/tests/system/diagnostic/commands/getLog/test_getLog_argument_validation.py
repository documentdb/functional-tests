"""Tests for getLog command argument validation.

Covers BSON type handling for the ``getLog`` field value. Only a string is
accepted; every non-string type is rejected with TypeMismatch.

Invalid string values (e.g. unknown components, the deprecated "rs") and
unrecognized command fields are covered in test_getLog_errors.py.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import MISSING_FIELD_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

# getLog accepts only a string value; every other BSON type is rejected with
# TypeMismatch, except a null value, which is treated as an absent required
# field (MissingField).
BSON_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="getLog_value",
        msg="getLog should reject non-string value types",
        keyword="getLog",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(BSON_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_getLog_rejects_non_string_value(collection, bson_type, sample_value, spec):
    """Test getLog rejects each non-string BSON type for its value."""
    result = execute_admin_command(collection, {"getLog": sample_value})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)
