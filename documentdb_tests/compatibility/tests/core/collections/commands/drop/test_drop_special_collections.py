import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.target_collection import (
    CappedCollection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Capped Collection Acceptance]: drop succeeds on capped collections.
DROP_CAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Drop on capped collection should succeed",
    ),
]

# Property [Large Collection Acceptance]: drop succeeds on collections with
# many or large documents.
DROP_LARGE_COLLECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "many_documents",
        docs=[{"_id": i, "val": i} for i in range(1000)],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Drop on collection with 1000 docs should succeed",
    ),
    CommandTestCase(
        "large_documents",
        docs=[{"_id": i, "data": "x" * 10_000} for i in range(10)],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Drop on collection with large documents should succeed",
    ),
]

DROP_SPECIAL_TESTS: list[CommandTestCase] = DROP_CAPPED_TESTS + DROP_LARGE_COLLECTION_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_SPECIAL_TESTS))
def test_drop_special(database_client, collection, test):
    """Test drop on special collection types."""
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
