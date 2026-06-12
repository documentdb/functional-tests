"""Tests for $changeStream namespace-related rejections (view, reserved, cluster)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ExistingDatabase, ViewCollection

# Property [View Namespace Rejection]: opening a stream on a view is rejected
# because change streams are not allowed on views.
CHANGESTREAM_VIEW_NAMESPACE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view",
        target_collection=ViewCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$changeStream should reject opening a stream on a view",
    ),
]

# Property [Reserved Namespace Rejection]: opening a stream on a reserved
# database or a reserved system collection is rejected as an invalid namespace.
CHANGESTREAM_RESERVED_NAMESPACE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "reserved_db_admin",
        target_collection=ExistingDatabase(db_name="admin"),
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$changeStream should reject a collection-scoped stream on the admin database",
    ),
    CommandTestCase(
        "reserved_db_local",
        target_collection=ExistingDatabase(db_name="local"),
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$changeStream should reject a collection-scoped stream on the local database",
    ),
    CommandTestCase(
        "reserved_db_config",
        target_collection=ExistingDatabase(db_name="config"),
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$changeStream should reject a collection-scoped stream on the config database",
    ),
    CommandTestCase(
        "system_views",
        docs=[{"_id": 1}],
        command={"aggregate": "system.views", "pipeline": [{"$changeStream": {}}], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$changeStream should reject a stream on the system.views collection",
    ),
    CommandTestCase(
        "system_profile",
        docs=[{"_id": 1}],
        command={"aggregate": "system.profile", "pipeline": [{"$changeStream": {}}], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$changeStream should reject a stream on the system.profile collection",
    ),
]

# Property [allChangesForCluster Namespace Rejection]: allChangesForCluster true
# is rejected as an invalid option anywhere other than a collection-less stream
# on the admin database, including a non-admin database and the admin database
# with a collection name present.
CHANGESTREAM_ALL_CHANGES_NAMESPACE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_changes_true_non_admin",
        docs=[{"_id": 1}],
        command={
            "aggregate": 1,
            "pipeline": [{"$changeStream": {"allChangesForCluster": True}}],
            "cursor": {},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="$changeStream should reject allChangesForCluster true on a non-admin database",
    ),
    CommandTestCase(
        "all_changes_true_admin_collection",
        target_collection=ExistingDatabase(db_name="admin"),
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {"allChangesForCluster": True}}],
            "cursor": {},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=(
            "$changeStream should reject allChangesForCluster true on the admin"
            " database with a collection name"
        ),
    ),
]

CHANGESTREAM_NAMESPACE_ERROR_TESTS = (
    CHANGESTREAM_VIEW_NAMESPACE_ERROR_TESTS
    + CHANGESTREAM_RESERVED_NAMESPACE_ERROR_TESTS
    + CHANGESTREAM_ALL_CHANGES_NAMESPACE_ERROR_TESTS
)


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(CHANGESTREAM_NAMESPACE_ERROR_TESTS))
def test_changeStream_namespace_errors(database_client, collection, test):
    """Test $changeStream rejects disallowed namespaces and option/namespace combinations."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg, raw_res=True)
