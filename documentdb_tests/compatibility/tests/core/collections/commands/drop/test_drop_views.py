import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    ViewCollection,
)

# Property [View Drop Acceptance]: drop succeeds on views and returns
# expected response fields.
DROP_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view",
        target_collection=ViewCollection(),
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"ns": ctx.namespace, "ok": 1.0},
        msg="Drop on view should return ns and ok without nIndexesWas",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_VIEW_TESTS))
def test_drop_views(database_client, collection, test):
    """Test drop command behavior on views."""
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


# Property [Underlying Collection Drop]: drop succeeds on the source
# collection underlying a view.
@pytest.mark.collection_mgmt
def test_drop_underlying_collection(database_client, collection):
    """Drop the source collection underlying a view."""
    collection.insert_one({"_id": 1, "a": 1})
    view_name = f"{collection.name}_view"
    database_client.command("create", view_name, viewOn=collection.name, pipeline=[])
    result = execute_command(collection, {"drop": collection.name})
    ns = f"{database_client.name}.{collection.name}"
    assertResult(
        result,
        expected={"nIndexesWas": 1, "ns": ns, "ok": 1.0},
        msg="Drop underlying collection should succeed",
        raw_res=True,
    )


# Property [system.views Drop]: drop succeeds on the system.views collection.
@pytest.mark.collection_mgmt
def test_drop_system_views(database_client, collection):
    """Drop the system.views collection."""
    src_name = f"{collection.name}_src"
    view_name = f"{collection.name}_view"
    database_client.create_collection(src_name)
    database_client.command("create", view_name, viewOn=src_name, pipeline=[])
    system_views = database_client["system.views"]
    result = execute_command(system_views, {"drop": "system.views"})
    ns = f"{database_client.name}.system.views"
    assertResult(
        result,
        expected={"nIndexesWas": 1, "ns": ns, "ok": 1.0},
        msg="Drop on system.views should succeed",
        raw_res=True,
    )
