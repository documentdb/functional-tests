"""Tests for read operations on views."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Find on View]: find queries on a view return documents filtered
# through the view's pipeline.
VIEWS_FIND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_with_filter",
        target_collection=ViewCollection(options={"pipeline": [{"$match": {"x": {"$gte": 20}}}]}),
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        command=lambda ctx: {"find": ctx.collection, "sort": {"_id": 1}},
        expected=[{"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        msg="find on view with $match pipeline should return only matching documents",
    ),
    CommandTestCase(
        "find_with_query_filter",
        target_collection=ViewCollection(options={"pipeline": [{"$match": {"x": {"$gte": 20}}}]}),
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$lte": 20}},
            "sort": {"_id": 1},
        },
        expected=[{"_id": 2, "x": 20}],
        msg="find filter should compose with view pipeline filter",
    ),
]

# Property [Aggregate on View]: aggregate pipelines on a view compose with
# the view's pipeline.
VIEWS_AGGREGATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "aggregate_group",
        target_collection=ViewCollection(options={"pipeline": [{"$match": {"dept": "eng"}}]}),
        docs=[
            {"_id": 1, "dept": "eng", "val": 10},
            {"_id": 2, "dept": "sales", "val": 20},
            {"_id": 3, "dept": "eng", "val": 30},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$group": {"_id": None, "total": {"$sum": "$val"}}}],
            "cursor": {},
        },
        expected=[{"_id": None, "total": 40}],
        msg="aggregate on filtered view should only see view-filtered documents",
    ),
]

VIEWS_CURSOR_TESTS: list[CommandTestCase] = VIEWS_FIND_TESTS + VIEWS_AGGREGATE_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VIEWS_CURSOR_TESTS))
def test_views_cursor_operations(database_client, collection, test):
    """Test find and aggregate operations on views."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )


# Property [Distinct on View]: distinct returns unique values from the view's
# visible documents.
VIEWS_DISTINCT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "distinct_all",
        target_collection=ViewCollection(),
        docs=[
            {"_id": 1, "cat": "a"},
            {"_id": 2, "cat": "b"},
            {"_id": 3, "cat": "a"},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "cat"},
        expected={"values": ["a", "b"], "ok": 1},
        ignore_order_in=["values"],
        msg="distinct on view should return unique values",
    ),
    CommandTestCase(
        "distinct_filtered_view",
        target_collection=ViewCollection(options={"pipeline": [{"$match": {"x": {"$gte": 20}}}]}),
        docs=[
            {"_id": 1, "x": 10, "cat": "a"},
            {"_id": 2, "x": 20, "cat": "b"},
            {"_id": 3, "x": 30, "cat": "b"},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "cat"},
        expected={"values": ["b"], "ok": 1},
        ignore_order_in=["values"],
        msg="distinct on filtered view should only see visible documents",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VIEWS_DISTINCT_TESTS))
def test_views_distinct(database_client, collection, test):
    """Test distinct on views."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
