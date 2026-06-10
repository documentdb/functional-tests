"""Tests for planCacheSetFilter interaction with planCacheClearFilters."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Len

# Property [ClearFilters Interaction]: planCacheClearFilters removes filters
# set by planCacheSetFilter.
SET_FILTER_CLEAR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clear_specific_filter",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"b": 1}, "indexes": [{"b": 1}]},
            ),
            execute_command(
                coll,
                {"planCacheClearFilters": coll.name, "query": {"a": 1}},
            ),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(1)},
        msg="planCacheClearFilters should remove only the matching filter",
    ),
    CommandTestCase(
        "clear_all_filters",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        setup=lambda coll: (
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"a": 1}, "indexes": [{"a": 1}]},
            ),
            execute_command(
                coll,
                {"planCacheSetFilter": coll.name, "query": {"b": 1}, "indexes": [{"b": 1}]},
            ),
            execute_command(coll, {"planCacheClearFilters": coll.name}),
        ),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": Len(0)},
        msg="planCacheClearFilters without query should remove all filters",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_CLEAR_TESTS))
def test_planCacheSetFilter_clear_filters(database_client, collection, test):
    """Test planCacheSetFilter interaction with planCacheClearFilters."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertProperties(result, test.build_expected(ctx), msg=test.msg, raw_res=True)
