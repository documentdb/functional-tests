import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.target_collection import (
    NamedCollection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Drop Response]: drop returns ok:1 with expected fields
# for various collection states.
DROP_BASIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "with_documents",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should return nIndexesWas, ns, and ok",
    ),
    CommandTestCase(
        "empty_collection",
        target_collection=NamedCollection(),
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Explicitly created empty collection should have nIndexesWas=1",
    ),
    CommandTestCase(
        "nonexistent",
        command={"drop": "nonexistent_coll_xyz"},
        expected={"ok": 1.0},
        msg="Non-existent collection drop should return ok:1",
    ),
]

# Property [Special Name Acceptance]: drop accepts collection names with
# spaces, unicode, and dots.
DROP_SPECIAL_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "spaces",
        target_collection=NamedCollection(suffix=" spaces"),
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with spaces in name",
    ),
    CommandTestCase(
        "unicode",
        target_collection=NamedCollection(suffix="_drôp_ünïcödé"),
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with unicode in name",
    ),
    CommandTestCase(
        "dots",
        target_collection=NamedCollection(suffix=".dots"),
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with dots in name",
    ),
]

# Property [Null Document Values]: drop succeeds regardless of null values
# in documents.
DROP_NULL_HANDLING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_document_values",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "b": None, "c": None}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Drop should succeed regardless of null document values",
    ),
]

DROP_BASIC_ALL_TESTS: list[CommandTestCase] = (
    DROP_BASIC_TESTS + DROP_SPECIAL_NAME_TESTS + DROP_NULL_HANDLING_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_BASIC_ALL_TESTS))
def test_drop_basic(database_client, collection, test):
    """Test basic drop command response."""
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
