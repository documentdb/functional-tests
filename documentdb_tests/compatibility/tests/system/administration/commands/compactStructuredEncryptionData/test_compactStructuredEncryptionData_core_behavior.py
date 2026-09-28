"""Tests for compactStructuredEncryptionData core behavior.

Verifies the command correctly rejects non-encrypted collections with error 6346807
and handles non-existent collections.
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

# Property [Non-Encrypted Rejection]: compactStructuredEncryptionData rejects
# collections that are not configured for Queryable Encryption with error 6346807.
CORE_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_compaction_tokens",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should reject non-encrypted collection"
        " with empty tokens",
    ),
    CommandTestCase(
        "non_empty_compaction_tokens",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"field": b"\x00\x01\x02"},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should reject non-encrypted collection with tokens",
    ),
    CommandTestCase(
        "collection_with_documents",
        docs=[{"_id": 1, "name": "test"}, {"_id": 2, "name": "data"}],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should reject non-encrypted collection with documents",
    ),
    CommandTestCase(
        "nonexistent_collection",
        command=lambda ctx: {
            "compactStructuredEncryptionData": "nonexistent_collection_xyz",
            "compactionTokens": {},
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="compactStructuredEncryptionData should error on non-existent collection",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_BEHAVIOR_TESTS))
def test_compactStructuredEncryptionData_core_behavior(database_client, collection, test):
    """Test compactStructuredEncryptionData core behavior on non-encrypted collections."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
