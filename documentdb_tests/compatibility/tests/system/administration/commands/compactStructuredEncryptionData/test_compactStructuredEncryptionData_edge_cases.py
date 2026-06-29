"""Tests for compactStructuredEncryptionData edge cases.

Covers collection name edge cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    NAMESPACE_NOT_FOUND_ERROR,
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
        msg="compactStructuredEncryptionData should reject system.* prefix"
        " collection names with namespace-not-found",
    ),
    CommandTestCase(
        "dotted_name",
        command=lambda ctx: {
            "compactStructuredEncryptionData": "a.b.c",
            "compactionTokens": {},
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="compactStructuredEncryptionData should reject multi-segment"
        " dotted names with namespace-not-found",
    ),
    CommandTestCase(
        "dollar_prefix",
        command=lambda ctx: {
            "compactStructuredEncryptionData": "$myCollection",
            "compactionTokens": {},
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="compactStructuredEncryptionData should reject dollar-prefixed"
        " collection names with namespace-not-found",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLECTION_NAME_TESTS))
def test_compactStructuredEncryptionData_collection_name_edge_cases(
    database_client, collection, test
):
    """Test compactStructuredEncryptionData rejects special collection name patterns."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
