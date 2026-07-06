"""Tests for renameCollection special collection types and system namespaces."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    ILLEGAL_OPERATION_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ExistingCollection,
    SiblingCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [System Namespace Restrictions - Oplog Accepted]: local.oplog
# (no suffix) as target and oplog-like names in non-local databases are
# accepted.
RENAME_OPLOG_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "oplog_no_suffix_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "local.oplog",
        },
        expected={"ok": 1.0},
        msg="local.oplog (no suffix) as target should be accepted",
        marks=(pytest.mark.requires(local_rename=True),),
    ),
    CommandTestCase(
        "oplog_rs_non_local_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.oplog.rs",
        },
        expected={"ok": 1.0},
        msg="oplog.rs in non-local database should be accepted",
    ),
]

# Property [Special Collection Types (Success)]: underlying collections
# of views and collections named "system" (without a dot suffix) can
# all be renamed successfully.
RENAME_VIEW_UNDERLYING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_underlying_rename",
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_view", view_on_source=True)],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
        },
        expected={"ok": 1.0},
        msg="Renaming underlying collection of a view should succeed",
    ),
]

# Property [Special Collection Types (Success) - System Name]: a
# collection named "system" (without a dot suffix) can be renamed.
RENAME_SYSTEM_NAME_WITHOUT_DOT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_name_without_dot",
        target_collection=ExistingCollection(name="system"),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
        },
        expected={"ok": 1.0},
        msg="Collection named 'system' without dot suffix should be renameable",
    ),
]

# Property [System Namespace Restrictions - Protected Names]: system.*
# collections are protected and cannot be used as source or target.
RENAME_SYSTEM_NAMESPACE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_users_as_source",
        docs=None,
        command=lambda ctx: {
            "renameCollection": f"{ctx.database}.system.users",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.users as source should be rejected",
    ),
    CommandTestCase(
        "system_users_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.system.users",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.users as target should be rejected",
    ),
    CommandTestCase(
        "system_js_as_source",
        docs=None,
        command=lambda ctx: {
            "renameCollection": f"{ctx.database}.system.js",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.js as source should be rejected",
    ),
    CommandTestCase(
        "system_js_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.system.js",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.js as target should be rejected",
    ),
    CommandTestCase(
        "system_views_as_source",
        docs=None,
        command=lambda ctx: {
            "renameCollection": f"{ctx.database}.system.views",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.views as source should be rejected",
    ),
    CommandTestCase(
        "system_profile_as_source",
        docs=None,
        command=lambda ctx: {
            "renameCollection": f"{ctx.database}.system.profile",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.profile as source should be rejected",
    ),
    CommandTestCase(
        "system_other_as_source",
        docs=None,
        command=lambda ctx: {
            "renameCollection": f"{ctx.database}.system.other",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.other (arbitrary system-prefixed) as source should be rejected",
    ),
    CommandTestCase(
        "system_other_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.system.other",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.other (arbitrary system-prefixed) as target should be rejected",
    ),
    CommandTestCase(
        "admin_system_version",
        docs=None,
        command=lambda ctx: {
            "renameCollection": "admin.system.version",
            "to": "admin.dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="admin.system.version should be specially protected",
    ),
    CommandTestCase(
        "system_views_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.system.views",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.views as target should be rejected",
    ),
    CommandTestCase(
        "system_profile_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.system.profile",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.profile as target should be rejected",
    ),
]

# Property [System Namespace Restrictions - Oplog Errors]: local.oplog.*
# (any non-empty suffix) as target produces an illegal operation error.
RENAME_OPLOG_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "oplog_rs_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "local.oplog.rs",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="local.oplog.rs as target should be rejected",
    ),
    CommandTestCase(
        "oplog_foo_as_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "local.oplog.foo",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="local.oplog.foo (any non-empty suffix) as target should be rejected",
    ),
]

# Property [Special Collection Types (Errors)]: views and timeseries
# collections cannot be renamed; attempting to do so produces a
# command-not-supported-on-view error.
RENAME_SPECIAL_COLLECTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rename_view_fails",
        target_collection=ViewCollection(),
        docs=None,
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="Renaming a view should be rejected",
    ),
    CommandTestCase(
        "rename_timeseries_fails",
        target_collection=TimeseriesCollection(),
        docs=None,
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="Renaming a timeseries collection should be rejected",
    ),
]

# Property [Special Collection Types (Success) - Capped]: a capped
# collection can be renamed successfully.
RENAME_CAPPED_COLLECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rename_capped_succeeds",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
        },
        expected={"ok": 1.0},
        msg="Renaming a capped collection should succeed",
    ),
]

# Property [Reserved Database Names]: renaming regular collections
# to the admin, local, and config databases is accepted.
RENAME_RESERVED_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "to_admin_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"admin.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Renaming to admin database (non-system collection) should succeed",
    ),
    CommandTestCase(
        "to_local_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"local.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Renaming to local database (non-oplog collection) should succeed",
        marks=(pytest.mark.requires(local_rename=True),),
    ),
    CommandTestCase(
        "to_config_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"config.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Renaming to config database should succeed",
    ),
]

RENAME_SPECIAL_COLLECTIONS_TESTS: list[CommandTestCase] = (
    RENAME_OPLOG_SUCCESS_TESTS
    + RENAME_VIEW_UNDERLYING_TESTS
    + RENAME_SYSTEM_NAME_WITHOUT_DOT_TESTS
    + RENAME_SYSTEM_NAMESPACE_ERROR_TESTS
    + RENAME_OPLOG_ERROR_TESTS
    + RENAME_SPECIAL_COLLECTION_TYPE_ERROR_TESTS
    + RENAME_CAPPED_COLLECTION_TESTS
    + RENAME_RESERVED_DB_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_SPECIAL_COLLECTIONS_TESTS))
def test_renameCollection_special_collections(
    database_client, collection, register_db_cleanup, test
):
    """Test renameCollection special collection types and system namespaces."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
