"""Tests for getLog command argument validation.

Covers BSON type handling for the ``getLog`` field value. Only a string is
accepted; every non-string type is rejected with TypeMismatch. Acceptance is
verified against the three documented filter strings ("global",
"startupWarnings", "*") rather than a generic string sample, because an
arbitrary string is not a valid log component.

Invalid string values (e.g. unknown components, the deprecated "rs") and
unrecognized command fields are covered in test_getLog_errors.py.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
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

# The three documented filter values accepted by getLog, paired with stable ids.
VALID_FILTERS = [
    ("global", "filter_global"),
    ("startupWarnings", "filter_startupWarnings"),
    ("*", "filter_wildcard"),
]
VALID_FILTER_IDS = [fid for _, fid in VALID_FILTERS]
VALID_FILTER_VALUES = [value for value, _ in VALID_FILTERS]


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_getLog_rejects_non_string_value(collection, bson_type, sample_value, spec):
    """Test getLog rejects each non-string BSON type for its value."""
    result = execute_admin_command(collection, {"getLog": sample_value})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("value", VALID_FILTER_VALUES, ids=VALID_FILTER_IDS)
def test_getLog_accepts_valid_filter(collection, value):
    """Test getLog accepts each documented filter string and returns ok:1."""
    result = execute_admin_command(collection, {"getLog": value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"getLog should accept '{value}'")
