"""Tests for planCacheSetFilter behavior on collection variants."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    TimeseriesCollection,
    ViewCollection,
)


# Property [View Collection]: planCacheSetFilter rejects views.
# Property [Capped Collection]: planCacheSetFilter behavior on capped collections.
# Property [Timeseries Collection]: planCacheSetFilter behavior on timeseries collections.
COLLECTION_VARIANT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_collection",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheSetFilter should reject views",
    ),
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should succeed on a capped collection",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(COLLECTION_VARIANT_TESTS))
def test_planCacheSetFilter_collection_variants(database_client, collection, test):
    """Test planCacheSetFilter on collection variants."""
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
