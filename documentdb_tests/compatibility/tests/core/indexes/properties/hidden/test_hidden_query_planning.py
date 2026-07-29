"""Tests for hidden index query-planner behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.properties.hidden.utils.helpers import (
    all_plan_index_names,
    all_plans_execution_index_names,
    is_covered,
    ixscan_index_names,
    uses_collscan,
    uses_index,
)
from documentdb_tests.framework.assertions import assertNotError, assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index


def test_query_uses_index_when_not_hidden(collection):
    """Test non-hidden index is used by the planner."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_1"),
        msg="Non-hidden index should be used by the query planner",
    )


def test_query_uses_collscan_when_index_hidden(collection):
    """Test a hidden index's field falls back to a collection scan."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        (False, True),
        raw_res=True,
        transform=lambda r: (uses_index(r, "a_1"), uses_collscan(r)),
        msg="Hidden index should not be used; a collection scan should be used instead",
    )


def test_hidden_index_absent_from_execution_stats_plans(collection):
    """Test hidden index absent from executionStats plans."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "executionStats"},
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: "a_1" in all_plan_index_names(r),
        msg="Hidden index must not appear as winning or rejected plan in executionStats",
    )


def test_hidden_index_absent_from_all_plans_execution(collection):
    """Test hidden index absent from allPlansExecution candidate plans."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(1000)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1, "b": 1}, "name": "ab"},
                {"key": {"a": 1, "c": 1}, "name": "ac"},
                {"key": {"a": 1, "d": 1}, "name": "ad_hidden", "hidden": True},
            ],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": {"a": {"$gte": 500}}},
            "verbosity": "allPlansExecution",
        },
    )
    assertSuccess(
        result,
        (True, False),
        raw_res=True,
        transform=lambda r: (
            len(r["executionStats"]["allPlansExecution"]) > 0,
            "ad_hidden" in all_plans_execution_index_names(r),
        ),
        msg="Hidden index must not appear as a candidate in allPlansExecution",
    )


def test_planner_uses_index_after_unhide(collection):
    """Test planner uses index immediately after unhide."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": False}}
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_1"),
        msg="Index should be immediately usable by the planner after unhide",
    )


def test_planner_uses_non_hidden_index_in_mix(collection):
    """Test planner uses non-hidden index in a mix."""
    collection.insert_many([{"a": i, "b": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1", "hidden": True},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"b": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: uses_index(r, "b_1"),
        msg="Non-hidden index should be used when a mix of indexes exists",
    )


def test_planner_ignores_hidden_index_in_mix(collection):
    """Test hidden index ignored even when other indexes exist."""
    collection.insert_many([{"a": i, "b": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1", "hidden": True},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_1"),
        msg="Hidden index must not be used even when other indexes are present",
    )


def test_planner_uses_visible_index_among_multiple_hidden(collection):
    """Test planner uses visible index when others are hidden."""
    collection.insert_many([{"a": i, "b": i, "c": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1", "hidden": True},
                {"key": {"b": 1}, "name": "b_1", "hidden": True},
                {"key": {"c": 1}, "name": "c_1"},
            ],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"c": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: uses_index(r, "c_1"),
        msg="Planner should use the only visible index when others are hidden",
    )


def test_meta_indexkey_absent_when_index_hidden(collection):
    """Test $meta:indexKey absent when index is hidden."""
    collection.insert_many([{"_id": i, "a": i} for i in range(10)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"a": 5}, "projection": {"ik": {"$meta": "indexKey"}}},
    )
    assertSuccess(
        result,
        False,
        transform=lambda docs: any("ik" in d for d in docs),
        msg="$meta indexKey should not return an index key for a hidden index",
    )


def test_meta_indexkey_present_after_unhide(collection):
    """Test $meta:indexKey present after unhide."""
    collection.insert_many([{"_id": i, "a": i} for i in range(10)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": False}}
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"a": 5}, "projection": {"ik": {"$meta": "indexKey"}}},
    )
    assertSuccess(
        result,
        True,
        transform=lambda docs: all("ik" in d for d in docs) and len(docs) > 0,
        msg="$meta indexKey should return the index key once the index is unhidden",
    )


def test_meta_indexkey_present_with_non_hidden_index(collection):
    """Test $meta:indexKey present for non-hidden index."""
    collection.insert_many([{"_id": i, "a": i} for i in range(10)])
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"a": 5}, "projection": {"ik": {"$meta": "indexKey"}}},
    )
    assertSuccess(
        result,
        True,
        transform=lambda docs: all("ik" in d for d in docs) and len(docs) > 0,
        msg="$meta indexKey should return the index key for a non-hidden index",
    )


def test_hidden_sparse_index_not_used(collection):
    """Test hidden sparse index not used."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_sparse", "sparse": True, "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_sparse"),
        msg="Hidden sparse index should not be used",
    )


def test_hidden_partial_index_not_used(collection):
    """Test hidden partial index not used."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"a": 1},
                    "name": "a_partial",
                    "partialFilterExpression": {"a": {"$gt": 0}},
                    "hidden": True,
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_partial"),
        msg="Hidden partial index should not be used",
    )


def test_hidden_compound_index_not_used(collection):
    """Test hidden compound index not used."""
    collection.insert_many([{"a": i, "b": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": {"a": 5, "b": 5}},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_1_b_1"),
        msg="Hidden compound index should not be used",
    )


def test_hidden_wildcard_index_not_used(collection):
    """Test hidden wildcard index not used."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"$**": 1}, "name": "wild", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "wild"),
        msg="Hidden wildcard index should not be used",
    )


def test_hidden_wildcard_dotted_field_not_used(collection):
    """Test hidden dotted-path wildcard index not used."""
    collection.insert_many([{"a": {"b": i}} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a.$**": 1}, "name": "a_wild", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a.b": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_wild"),
        msg="Hidden dotted wildcard index should not be used",
    )


def test_hidden_hashed_index_not_used(collection):
    """Test hidden hashed index not used."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": "hashed"}, "name": "a_hashed", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_hashed"),
        msg="Hidden hashed index should not be used",
    )


def test_hidden_2dsphere_index_not_used(collection):
    """Test hidden 2dsphere index not used for geo queries."""
    collection.insert_many(
        [{"loc": {"type": "Point", "coordinates": [i * 0.001, 0]}} for i in range(20)]
    )
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2dsphere", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "loc_2dsphere"),
        msg="Hidden 2dsphere index should not be used for geo queries",
    )


def test_unhide_restores_2dsphere_use(collection):
    """Test unhiding 2dsphere index restores geo query use."""
    collection.insert_many(
        [{"loc": {"type": "Point", "coordinates": [i * 0.001, 0]}} for i in range(20)]
    )
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2dsphere", "hidden": True}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "loc_2dsphere", "hidden": False}}
    )
    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: uses_index(r, "loc_2dsphere"),
        msg="Unhidden 2dsphere index should be usable for geo queries",
    )


def test_unhide_restores_wildcard_use(collection):
    """Test unhiding a wildcard index restores planner use."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"$**": 1}, "name": "wild", "hidden": True}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "wild", "hidden": False}}
    )
    result = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": {"a": 5}}, "verbosity": "queryPlanner"},
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: uses_index(r, "wild"),
        msg="Unhidden wildcard index should be usable",
    )


_FILTER_QUERY = {"a": {"$gte": 0}, "b": {"$gte": 0}}


def test_index_filter_uses_a_listed_index(collection):
    """Test planner uses a filter index when none are hidden."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": _FILTER_QUERY,
            "indexes": [{"a": 1}, {"b": 1}],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": _FILTER_QUERY},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: bool(set(ixscan_index_names(r)) & {"a_1", "b_1"}),
        msg="Planner should use one of the filter's indexes when none are hidden",
    )


def test_hiding_one_filter_index_uses_the_other(collection):
    """Test hiding one filter index makes planner use the other."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": _FILTER_QUERY,
            "indexes": [{"a": 1}, {"b": 1}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": _FILTER_QUERY},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        (True, False),
        raw_res=True,
        transform=lambda r: (uses_index(r, "b_1"), uses_index(r, "a_1")),
        msg="Hiding one filter index should make the planner use the other",
    )


def test_hiding_all_filter_indexes_uses_collscan(collection):
    """Test hiding all filter indexes falls back to collscan."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": _FILTER_QUERY,
            "indexes": [{"a": 1}, {"b": 1}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "b_1", "hidden": True}}
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": _FILTER_QUERY},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=uses_collscan,
        msg="Hiding all filter indexes should fall back to a collection scan",
    )


def test_hidden_index_remains_in_filter_list(collection):
    """Test hiding an index doesn't remove it from the filter list."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": _FILTER_QUERY,
            "indexes": [{"a": 1}, {"b": 1}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    result = execute_command(collection, {"planCacheListFilters": collection.name})
    assertSuccess(
        result,
        [{"a": 1}, {"b": 1}],
        raw_res=True,
        transform=lambda r: sorted(
            (idx for f in r["filters"] for idx in f["indexes"]),
            key=lambda d: list(d.keys()),
        ),
        msg="Hiding an index should not change the plan cache filter list",
    )


def test_set_filter_referencing_hidden_index_succeeds(collection):
    """Test planCacheSetFilter can reference a hidden index."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1", "hidden": True},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    result = execute_command(
        collection,
        {"planCacheSetFilter": collection.name, "query": _FILTER_QUERY, "indexes": [{"a": 1}]},
    )
    assertNotError(result, msg="Setting an index filter on a hidden index should succeed")


def test_only_hidden_index_in_filter_uses_collscan(collection):
    """Test filter with only hidden index falls back to collscan."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection,
        {"planCacheSetFilter": collection.name, "query": _FILTER_QUERY, "indexes": [{"a": 1}]},
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": _FILTER_QUERY},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=uses_collscan,
        msg="A filter whose only index is hidden should use a collection scan",
    )


def test_unhide_filter_index_resumes_use(collection):
    """Test unhiding the sole filter index restores planner use."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection,
        {"planCacheSetFilter": collection.name, "query": _FILTER_QUERY, "indexes": [{"a": 1}]},
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": False}}
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": _FILTER_QUERY},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_1"),
        msg="Unhiding the filter's index should make the planner use it again",
    )


def test_unhide_all_restores_original_plan(collection):
    """Test unhiding all filter indexes restores planner use."""
    collection.insert_many([{"a": i, "b": i} for i in range(50)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection,
        {
            "planCacheSetFilter": collection.name,
            "query": _FILTER_QUERY,
            "indexes": [{"a": 1}, {"b": 1}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "b_1", "hidden": True}}
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": False}}
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "b_1", "hidden": False}}
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": _FILTER_QUERY},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: len(ixscan_index_names(r)) > 0
        and set(ixscan_index_names(r)) <= {"a_1", "b_1"},
        msg="Unhiding all filter indexes should restore planner use of a filtered index",
    )


def test_hidden_index_not_used_for_sort(collection):
    """Test hidden index not used to satisfy a sort."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {"find": collection.name, "filter": {}, "sort": {"a": 1}},
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_1"),
        msg="Hidden index should not be used to satisfy a sort",
    )


def test_covered_query_covered_when_index_visible(collection):
    """Test visible index produces a covered query plan."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"a": {"$gte": 0}},
                "projection": {"_id": 0, "a": 1},
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=is_covered,
        msg="A visible index should produce a covered query plan",
    )


def test_covered_query_not_covered_when_index_hidden(collection):
    """Test hidden index doesn't produce a covered query plan."""
    collection.insert_many([{"a": i} for i in range(20)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"a": {"$gte": 0}},
                "projection": {"_id": 0, "a": 1},
            },
            "verbosity": "queryPlanner",
        },
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=is_covered,
        msg="A hidden index must not produce a covered query plan",
    )


@pytest.mark.no_parallel
def test_capped_hidden_index_not_used(collection, database_client):
    """Test hidden index on capped collection is excluded from planning."""
    capped_name = f"{collection.name}_capped"
    coll = database_client[capped_name]
    execute_command(coll, {"create": capped_name, "capped": True, "size": 1_000_000})
    execute_command(coll, {"insert": capped_name, "documents": [{"a": i} for i in range(20)]})
    execute_command(
        coll,
        {
            "createIndexes": capped_name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        coll, {"explain": {"find": capped_name, "filter": {"a": 5}}, "verbosity": "queryPlanner"}
    )
    assertSuccess(
        result,
        False,
        raw_res=True,
        transform=lambda r: uses_index(r, "a_1"),
        msg="A hidden index on a capped collection should not be used by the planner",
    )
