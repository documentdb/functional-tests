"""Delete command error cases.

All error code assertions for the delete command consolidated in one file.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertExceptionType, assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_LENGTH_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Field Validation]: the delete command rejects invalid field types and values.
# Wire-protocol namespace validation (INVALID_NAMESPACE_ERROR for non-string collection name
# types) is foundational behavior per TEST_COVERAGE.md §19. One representative case wires
# delete to that behavior; the full type matrix belongs in the centralized namespace test
# site (currently TBD).
DELETE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "delete_field_non_string_int",
        docs=[],
        command=lambda ctx: {
            "delete": 32,
            "deletes": [{"q": {}, "limit": 1}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="delete should reject non-string collection name",
    ),
    CommandTestCase(
        "delete_field_empty_string",
        docs=[],
        command=lambda ctx: {
            "delete": "",
            "deletes": [{"q": {}, "limit": 1}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="delete should reject empty string collection name",
    ),
    CommandTestCase(
        "delete_field_null_byte",
        docs=[],
        command=lambda ctx: {
            "delete": "test\x00evil",
            "deletes": [{"q": {}, "limit": 1}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="delete should reject null byte in collection name",
    ),
    CommandTestCase(
        "missing_deletes_field",
        docs=[],
        command=lambda ctx: {"delete": ctx.collection},
        error_code=MISSING_FIELD_ERROR,
        msg="delete should require deletes field",
    ),
    CommandTestCase(
        "empty_deletes_array",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [],
        },
        error_code=INVALID_LENGTH_ERROR,
        msg="delete should reject empty deletes array",
    ),
    CommandTestCase(
        "unknown_top_level_field",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 1}],
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="delete should reject unknown top-level fields",
    ),
    CommandTestCase(
        "let_non_object",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 1}],
            "let": "invalid",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="delete should reject non-object let field",
    ),
    CommandTestCase(
        "statement_missing_q",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"limit": 1}],
        },
        error_code=MISSING_FIELD_ERROR,
        msg="delete should require q field in statement",
    ),
    CommandTestCase(
        "statement_missing_limit",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}}],
        },
        error_code=MISSING_FIELD_ERROR,
        msg="delete should require limit field in statement",
    ),
    CommandTestCase(
        "statement_q_non_object",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": "not_object", "limit": 1}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="delete should reject non-object q field",
    ),
    CommandTestCase(
        "statement_limit_value_2",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 2}],
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="delete should reject limit values other than 0 or 1",
    ),
    CommandTestCase(
        "statement_limit_negative",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": -1}],
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="delete should reject negative limit",
    ),
    CommandTestCase(
        "statement_unknown_field",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 1, "unknownField": 1}],
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="delete should reject unknown fields in statement",
    ),
    CommandTestCase(
        "hint_nonexistent_index",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": 1}, "limit": 1, "hint": {"nonexistent": 1}}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="delete should reject hint pointing to non-existent index",
    ),
    CommandTestCase(
        "ordered_non_boolean_string",
        docs=[],
        command=lambda ctx: {
            "delete": ctx.collection,
            "ordered": "true",
            "deletes": [{"q": {}, "limit": 1}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="delete should reject non-boolean ordered field",
    ),
]

# Property [Collection Variant Rejection]: the delete command rejects unsupported collection types.
COLLECTION_VARIANT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "delete_on_view",
        target_collection=ViewCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {}, "limit": 0}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="delete should not work on views",
    ),
]

DELETE_ERROR_TESTS_ALL: list[CommandTestCase] = DELETE_ERROR_TESTS + COLLECTION_VARIANT_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(DELETE_ERROR_TESTS_ALL))
def test_delete_error_cases(database_client, collection, test):
    """Test delete command error cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_delete_deletes_non_array_object_fails(collection):
    """Test delete with non-array deletes field raises client-side error."""
    result = execute_command(
        collection,
        {"delete": collection.name, "deletes": {"a": 1}},
    )
    assertExceptionType(result, TypeError, msg="deletes field must be an array")


def test_delete_deletes_non_array_string_fails(collection):
    """Test delete with non-array deletes field raises client-side error."""
    result = execute_command(
        collection,
        {"delete": collection.name, "deletes": "invalid"},
    )
    assertExceptionType(result, TypeError, msg="deletes field must be an array")
