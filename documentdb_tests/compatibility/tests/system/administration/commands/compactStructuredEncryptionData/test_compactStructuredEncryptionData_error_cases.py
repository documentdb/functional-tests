"""Tests for compactStructuredEncryptionData error cases.

Covers unrecognized fields and collection type variants (views, capped).
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    NOT_ENCRYPTED_COLLECTION_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CappedCollection, ViewCollection

pytestmark = pytest.mark.admin

# Property [Unrecognized Field Rejection]: compactStructuredEncryptionData rejects
# commands with unrecognized fields.
UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "extra_field",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {},
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="compactStructuredEncryptionData should reject unrecognized fields",
    ),
    CommandTestCase(
        "similar_field_name",
        docs=[],
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {},
            "compactionToken": {},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="compactStructuredEncryptionData should reject fields with similar names",
    ),
]

# Property [Collection Type Rejection]: compactStructuredEncryptionData rejects
# views and returns non-encrypted error for capped collections.
COLLECTION_VARIANT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "on_view",
        docs=[{"_id": 1}],
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {},
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="compactStructuredEncryptionData should reject views",
    ),
    CommandTestCase(
        "on_capped_collection",
        docs=[{"_id": 1}],
        target_collection=CappedCollection(),
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {},
        },
        error_code=NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should reject non-encrypted capped collection",
    ),
]

ERROR_TESTS = UNRECOGNIZED_FIELD_TESTS + COLLECTION_VARIANT_TESTS


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_compactStructuredEncryptionData_errors(database_client, collection, test):
    """Test compactStructuredEncryptionData error conditions."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
