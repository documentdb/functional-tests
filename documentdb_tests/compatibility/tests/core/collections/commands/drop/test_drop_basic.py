import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
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
        setup=lambda db: db.create_collection("empty_via_create"),
        command={"drop": "empty_via_create"},
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
        setup=lambda db: db.create_collection("test drop spaces"),
        command={"drop": "test drop spaces"},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with spaces in name",
    ),
    CommandTestCase(
        "unicode",
        setup=lambda db: db.create_collection("test_drôp_ünïcödé"),
        command={"drop": "test_drôp_ünïcödé"},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with unicode in name",
    ),
    CommandTestCase(
        "dots",
        setup=lambda db: db.create_collection("test.drop.dots"),
        command={"drop": "test.drop.dots"},
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
    target = test.setup(database_client) if test.setup else collection
    if test.docs:
        target.insert_many(test.docs)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
