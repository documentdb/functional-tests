"""Tests for planCacheListFilters command core behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
)

# Property [Basic Success]: planCacheListFilters returns ok: 1.0 and empty
# filters array on existing, empty, and non-existent collections.
LIST_FILTERS_BASIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "basic_with_documents",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on collection with documents",
    ),
    CommandTestCase(
        "basic_empty_collection",
        docs=[],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on empty collection",
    ),
    CommandTestCase(
        "basic_nonexistent_collection",
        docs=None,
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on non-existent collection",
    ),
]

# Property [Capped Collection]: planCacheListFilters succeeds on capped
# collections.
LIST_FILTERS_CAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on a capped collection",
    ),
]

# Property [Clustered Collection]: planCacheListFilters succeeds on clustered
# collections.
LIST_FILTERS_CLUSTERED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clustered_collection",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on a clustered collection",
    ),
]

# Property [Null Optional Parameters]: when comment is set to null, the
# command treats it as omitted and succeeds.
LIST_FILTERS_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_comment",
        command=lambda ctx: {"planCacheListFilters": ctx.collection, "comment": None},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should treat null comment as omitted",
    ),
]

LIST_FILTERS_CORE_TESTS: list[CommandTestCase] = (
    LIST_FILTERS_BASIC_TESTS
    + LIST_FILTERS_CAPPED_TESTS
    + LIST_FILTERS_CLUSTERED_TESTS
    + LIST_FILTERS_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(LIST_FILTERS_CORE_TESTS))
def test_planCacheListFilters_core(database_client, collection, test):
    """Test planCacheListFilters command core behavior."""
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
