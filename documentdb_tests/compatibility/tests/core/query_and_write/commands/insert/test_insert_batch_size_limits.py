"""
Insert batch size limit tests.

Tests maxWriteBatchSize enforcement and document size rejection.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import BSON_OBJECT_TOO_LARGE_ERROR, INVALID_LENGTH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Document and Batch Rejection]: insert rejects an empty documents array
# and a document exceeding the BSON size limit.
BATCH_LIMIT_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_documents_array",
        command=lambda ctx: {"insert": ctx.collection, "documents": []},
        error_code=INVALID_LENGTH_ERROR,
        msg="insert should reject an empty documents array.",
    ),
    CommandTestCase(
        "document_exceeds_size_limit",
        # A string value of 16MB plus document overhead exceeds the size limit.
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "value": "x" * (16 * 1024 * 1024)}],
        },
        error_code=BSON_OBJECT_TOO_LARGE_ERROR,
        msg="insert should reject a document exceeding the BSON size limit.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(BATCH_LIMIT_REJECTED_TESTS))
def test_insert_batch_limit_rejected(collection, test: CommandTestCase):
    """Test insert rejects empty batch and oversized documents."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


@pytest.mark.insert
def test_insert_large_batch_succeeds(collection):
    """Test insert succeeds with a large batch of documents.

    This is a wiring test: it confirms the server accepts multi-document
    inserts without error. It does not test the maxWriteBatchSize boundary
    because inserting up to 100,000 documents is impractical in a functional
    test suite. See the Property [Document and Batch Rejection] cases above
    for rejection behavior.
    """
    docs = [{"_id": i} for i in range(1000)]
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": docs},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1000},
        msg="insert should succeed with a batch of 1000 documents.",
    )
