"""Tests for compactStructuredEncryptionData edge cases.

Covers collection name edge cases and compactionTokens document content
edge cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    NAMESPACE_NOT_FOUND_ERROR,
    NOT_ENCRYPTED_COLLECTION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin

# Property [Collection Name Edge Cases]: compactStructuredEncryptionData handles
# special collection name patterns correctly.
COLLECTION_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_prefix",
        command=lambda ctx: {
            "compactStructuredEncryptionData": "system.buckets.test",
            "compactionTokens": {},
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="compactStructuredEncryptionData should error on non-existent system prefix collection",
    ),
    CommandTestCase(
        "dotted_name",
        command=lambda ctx: {
            "compactStructuredEncryptionData": "a.b.c",
            "compactionTokens": {},
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="compactStructuredEncryptionData should error on non-existent dotted collection",
    ),
    CommandTestCase(
        "dollar_prefix",
        command=lambda ctx: {
            "compactStructuredEncryptionData": "$cmd",
            "compactionTokens": {},
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="compactStructuredEncryptionData should error on non-existent"
        " dollar-prefixed collection",
    ),
]

# Property [CompactionTokens Content Edge Cases]: compactStructuredEncryptionData
# handles various compactionTokens document content correctly.
COMPACTION_TOKENS_CONTENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_token_value",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"ssn": None},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should handle null token values",
    ),
    CommandTestCase(
        "empty_string_key",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"": b"\x00\x01"},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should handle empty string key in tokens",
    ),
    CommandTestCase(
        "dot_notation_key",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"a.b": b"\x00\x01"},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should handle dot-notation key in tokens",
    ),
    CommandTestCase(
        "nested_document_value",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"field": {"nested": b"\x00\x01"}},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should handle nested document in token value",
    ),
]

EDGE_CASE_TESTS = COLLECTION_NAME_TESTS + COMPACTION_TOKENS_CONTENT_TESTS


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_compactStructuredEncryptionData_edge_cases(database_client, collection, test):
    """Test compactStructuredEncryptionData edge cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
