"""Tests for explain command argument validation.

Covers the verbosity parameter (valid string modes and null, rejection of other
BSON types), the explain field (rejection of non-document types), and the
comment parameter (acceptance of any BSON type).
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccessPartial,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin


VERBOSITY_SPEC = [
    BsonTypeTestCase(
        id="verbosity",
        msg=(
            "verbosity should accept string modes and null, "
            "and reject other types with TypeMismatch"
        ),
        keyword="verbosity",
        valid_types=[BsonType.STRING, BsonType.NULL],
        valid_inputs={BsonType.STRING: "queryPlanner"},
        default_error_code=TYPE_MISMATCH_ERROR,
    )
]
VERBOSITY_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(VERBOSITY_SPEC)
VERBOSITY_REJECTION_CASES = generate_bson_rejection_test_cases(VERBOSITY_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", VERBOSITY_ACCEPTANCE_CASES)
def test_explain_accepts_valid_verbosity(collection, bson_type, sample_value, spec):
    """Test explain accepts valid verbosity values (string mode and null default)."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 1}}, "verbosity": sample_value},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", VERBOSITY_REJECTION_CASES)
def test_explain_rejects_non_string_verbosity(collection, bson_type, sample_value, spec):
    """Test explain rejects non-string verbosity for every invalid BSON type."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 1}}, "verbosity": sample_value},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


EXPLAIN_ARGUMENT_TYPE_SPEC = [
    BsonTypeTestCase(
        id="explain",
        msg="explain field should reject non-document types with TypeMismatch",
        keyword="explain",
        valid_types=[BsonType.OBJECT],
        default_error_code=TYPE_MISMATCH_ERROR,
    )
]
EXPLAIN_ARGUMENT_REJECTION_CASES = generate_bson_rejection_test_cases(EXPLAIN_ARGUMENT_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", EXPLAIN_ARGUMENT_REJECTION_CASES)
def test_explain_rejects_non_document_explain_field(collection, bson_type, sample_value, spec):
    """Test explain rejects non-document values for the explain field."""
    result = execute_command(
        collection,
        {"explain": sample_value, "verbosity": "queryPlanner"},
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


COMMENT_TYPE_SPEC = [
    BsonTypeTestCase(
        id="comment",
        msg="comment should accept any BSON type",
        keyword="comment",
        valid_types=list(BsonType),
    )
]
COMMENT_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(COMMENT_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", COMMENT_ACCEPTANCE_CASES)
def test_explain_accepts_comment_type(collection, bson_type, sample_value, spec):
    """Test explain accepts a comment of any BSON type at the explain level."""
    collection.insert_one({"_id": 1, "a": 1})
    cmd = {"explain": {"find": collection.name, "filter": {"a": 1}}, "comment": sample_value}
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)
