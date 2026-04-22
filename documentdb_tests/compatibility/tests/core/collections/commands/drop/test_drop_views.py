import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [View Drop Acceptance]: drop succeeds on views and returns
# expected response fields.
DROP_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view",
        setup=lambda db: (
            db.create_collection("test_drop_view_src"),
            db.command("create", "test_drop_view_v", viewOn="test_drop_view_src", pipeline=[]),
            db["test_drop_view_v"],
        )[-1],
        command={"drop": "test_drop_view_v"},
        expected=lambda ctx: {"ns": ctx.namespace, "ok": 1.0},
        msg="Drop on view should return ns and ok without nIndexesWas",
    ),
]

# Property [Underlying Collection Drop]: drop succeeds on the source
# collection underlying a view.
DROP_UNDERLYING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "succeeds",
        setup=lambda db: (
            db["test_drop_under_src"].insert_one({"_id": 1, "a": 1}),
            db.command("create", "test_drop_under_v", viewOn="test_drop_under_src", pipeline=[]),
            db["test_drop_under_src"],
        )[-1],
        command={"drop": "test_drop_under_src"},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Drop underlying collection should succeed",
    ),
]

# Property [system.views Drop]: drop succeeds on the system.views collection.
DROP_SYSTEM_VIEWS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_views",
        setup=lambda db: (
            db.create_collection("test_drop_sysviews_src"),
            db.command(
                "create", "test_drop_sysviews_v", viewOn="test_drop_sysviews_src", pipeline=[]
            ),
            db["system.views"],
        )[-1],
        command={"drop": "system.views"},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Drop on system.views should succeed",
    ),
]

DROP_VIEW_ALL_TESTS: list[CommandTestCase] = (
    DROP_VIEW_TESTS + DROP_UNDERLYING_TESTS + DROP_SYSTEM_VIEWS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_VIEW_ALL_TESTS))
def test_drop_views(database_client, collection, test):
    """Test drop command behavior on views."""
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
