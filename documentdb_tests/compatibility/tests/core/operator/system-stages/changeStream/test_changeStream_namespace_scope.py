"""Tests for $changeStream namespace scope (collection, database, cluster)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ExistingDatabase,
    TargetDatabase,
)

# Property [Namespace Scope]: a stream opens on a collection-scoped, a
# database-scoped, and the cluster-wide namespace.
CHANGESTREAM_NAMESPACE_SCOPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_existing",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open a collection-scoped stream on an existing collection",
    ),
    CommandTestCase(
        "collection_nonexistent",
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open a collection-scoped stream on a non-existent collection",
    ),
    CommandTestCase(
        "collection_capped",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open a collection-scoped stream on a capped collection",
    ),
    CommandTestCase(
        "database_existing",
        docs=[{"_id": 1}],
        command={"aggregate": 1, "pipeline": [{"$changeStream": {}}], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open a database-scoped stream on an existing database",
    ),
    CommandTestCase(
        "database_nonexistent",
        target_collection=TargetDatabase(suffix="absent"),
        docs=None,
        command={"aggregate": 1, "pipeline": [{"$changeStream": {}}], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open a database-scoped stream on a non-existent database",
    ),
    CommandTestCase(
        "cluster_admin",
        target_collection=ExistingDatabase(db_name="admin"),
        docs=None,
        command={
            "aggregate": 1,
            "pipeline": [{"$changeStream": {"allChangesForCluster": True}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open a cluster-wide stream on the admin database",
    ),
]


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(CHANGESTREAM_NAMESPACE_SCOPE_TESTS))
def test_changeStream_namespace_scope(database_client, collection, register_db_cleanup, test):
    """Test $changeStream opens across collection, database, and cluster namespace scopes."""
    target = test.prepare(database_client, collection)
    if isinstance(test.target_collection, TargetDatabase):
        register_db_cleanup(target.database.name)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg, raw_res=True)
