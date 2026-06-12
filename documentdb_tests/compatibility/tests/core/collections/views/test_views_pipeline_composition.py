"""Tests for view pipeline composition and source reflection."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection


# Property [Source Reflection Insert]: a view reflects documents inserted
# into the source collection immediately.
@pytest.mark.collection_mgmt
def test_views_source_reflection_insert(database_client, collection):
    """Test view reflects inserted documents."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}])
    view_name = f"{collection.name}_view"
    database_client.command("create", view_name, viewOn=collection.name, pipeline=[])
    view = database_client[view_name]

    collection.insert_one({"_id": 3, "x": 30})
    result = execute_command(view, {"find": view_name, "sort": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        msg="view should reflect inserted document immediately",
    )


# Property [Source Reflection Update]: a view reflects updates to the source
# collection immediately.
@pytest.mark.collection_mgmt
def test_views_source_reflection_update(database_client, collection):
    """Test view reflects updated documents."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}])
    view_name = f"{collection.name}_view"
    database_client.command("create", view_name, viewOn=collection.name, pipeline=[])
    view = database_client[view_name]

    collection.update_one({"_id": 1}, {"$set": {"x": 99}})
    result = execute_command(view, {"find": view_name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "x": 99}],
        msg="view should reflect updated document immediately",
    )


# Property [Source Reflection Delete]: a view reflects deletions from the
# source collection immediately.
@pytest.mark.collection_mgmt
def test_views_source_reflection_delete(database_client, collection):
    """Test view reflects deleted documents."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}])
    view_name = f"{collection.name}_view"
    database_client.command("create", view_name, viewOn=collection.name, pipeline=[])
    view = database_client[view_name]

    collection.delete_one({"_id": 2})
    result = execute_command(view, {"find": view_name, "sort": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "x": 10}],
        msg="view should reflect deleted document immediately",
    )


# Property [Filtered Reflection Insert Matching]: a newly inserted document
# that matches the view's filter appears in the view.
@pytest.mark.collection_mgmt
def test_views_filtered_reflection_insert_matching(database_client, collection):
    """Test view includes newly inserted document that matches filter."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}])
    view_name = f"{collection.name}_filt_view"
    database_client.command(
        "create", view_name, viewOn=collection.name, pipeline=[{"$match": {"x": {"$gte": 20}}}]
    )
    view = database_client[view_name]

    collection.insert_one({"_id": 3, "x": 30})
    result = execute_command(view, {"find": view_name, "sort": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        msg="view should include newly inserted document that matches filter",
    )


# Property [Filtered Reflection Insert Non-Matching]: a newly inserted document
# that does not match the view's filter does not appear in the view.
@pytest.mark.collection_mgmt
def test_views_filtered_reflection_insert_non_matching(database_client, collection):
    """Test view excludes newly inserted document that does not match filter."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}])
    view_name = f"{collection.name}_filt_view"
    database_client.command(
        "create", view_name, viewOn=collection.name, pipeline=[{"$match": {"x": {"$gte": 20}}}]
    )
    view = database_client[view_name]

    collection.insert_one({"_id": 3, "x": 5})
    result = execute_command(view, {"find": view_name, "sort": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 2, "x": 20}],
        msg="view should exclude newly inserted document that does not match filter",
    )


# Property [Filtered Reflection Update Out]: a document disappears from the
# view when updated to no longer match the view's filter.
@pytest.mark.collection_mgmt
def test_views_filtered_reflection_update_out(database_client, collection):
    """Test document disappears from view when updated to no longer match."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}])
    view_name = f"{collection.name}_filt_view"
    database_client.command(
        "create", view_name, viewOn=collection.name, pipeline=[{"$match": {"x": {"$gte": 20}}}]
    )
    view = database_client[view_name]

    collection.update_one({"_id": 2}, {"$set": {"x": 5}})
    result = execute_command(view, {"find": view_name, "sort": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 3, "x": 30}],
        msg="document should disappear from view when updated out of filter",
    )


# Property [Filtered Reflection Update In]: a document appears in the view
# when updated to match the view's filter.
@pytest.mark.collection_mgmt
def test_views_filtered_reflection_update_in(database_client, collection):
    """Test document appears in view when updated to match filter."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}])
    view_name = f"{collection.name}_filt_view"
    database_client.command(
        "create", view_name, viewOn=collection.name, pipeline=[{"$match": {"x": {"$gte": 20}}}]
    )
    view = database_client[view_name]

    collection.update_one({"_id": 1}, {"$set": {"x": 25}})
    result = execute_command(view, {"find": view_name, "sort": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "x": 25}, {"_id": 2, "x": 20}],
        msg="document should appear in view when updated to match filter",
    )


# Property [Orphaned View]: a view whose source collection does not exist
# returns empty results without error.
@pytest.mark.collection_mgmt
def test_views_orphaned_source(database_client, collection):
    """Test view on non-existent source returns empty results."""
    view_name = f"{collection.name}_orphan_view"
    database_client.command(
        "create", view_name, viewOn="nonexistent_source_collection", pipeline=[]
    )
    view = database_client[view_name]
    result = execute_command(view, {"find": view_name})
    assertSuccess(
        result,
        [],
        msg="view on non-existent source should return empty results",
    )


# Property [Dropped Source]: dropping the source collection causes the view
# to return empty results.
@pytest.mark.collection_mgmt
def test_views_dropped_source(database_client, collection):
    """Test view returns empty after source is dropped."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}])
    view_name = f"{collection.name}_drop_view"
    database_client.command("create", view_name, viewOn=collection.name, pipeline=[])
    view = database_client[view_name]

    collection.drop()

    result = execute_command(view, {"find": view_name})
    assertSuccess(
        result,
        [],
        msg="view should return empty results after source is dropped",
    )


# Property [Pipeline Composition]: the view's pipeline is prepended to any
# additional pipeline specified in an aggregate command.
VIEWS_PIPELINE_COMPOSITION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "match_then_match",
        target_collection=ViewCollection(options={"pipeline": [{"$match": {"x": {"$gte": 20}}}]}),
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2, "x": 20},
            {"_id": 3, "x": 30},
            {"_id": 4, "x": 40},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$lte": 30}}}],
            "cursor": {},
        },
        expected=[{"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        msg="aggregate $match should compose with view $match pipeline",
    ),
    CommandTestCase(
        "project_then_match",
        target_collection=ViewCollection(
            options={
                "pipeline": [
                    {
                        "$project": {
                            "x": 1,
                            "label": {"$concat": ["item_", {"$toString": "$x"}]},
                        }
                    }
                ]
            }
        ),
        docs=[{"_id": 1, "x": 10, "y": "extra"}, {"_id": 2, "x": 20, "y": "extra"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"label": "item_10"}}],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": 10, "label": "item_10"}],
        msg="aggregate $match should see fields added by view $project",
    ),
    CommandTestCase(
        "addfields_then_sort",
        target_collection=ViewCollection(
            options={"pipeline": [{"$addFields": {"doubled": {"$multiply": ["$x", 2]}}}]}
        ),
        docs=[{"_id": 1, "x": 3}, {"_id": 2, "x": 1}, {"_id": 3, "x": 2}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"doubled": 1}}],
            "cursor": {},
        },
        expected=[
            {"_id": 2, "x": 1, "doubled": 2},
            {"_id": 3, "x": 2, "doubled": 4},
            {"_id": 1, "x": 3, "doubled": 6},
        ],
        msg="aggregate should be able to sort by fields added in view pipeline",
    ),
    CommandTestCase(
        "sort_limit_in_view",
        target_collection=ViewCollection(
            options={"pipeline": [{"$sort": {"x": -1}}, {"$limit": 2}]}
        ),
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"x": 1, "_id": 0}}],
            "cursor": {},
        },
        expected=[{"x": 30}, {"x": 20}],
        msg="view pipeline with $sort and $limit should restrict visible documents",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VIEWS_PIPELINE_COMPOSITION_TESTS))
def test_views_pipeline_composition(database_client, collection, test):
    """Test view pipeline composition."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
