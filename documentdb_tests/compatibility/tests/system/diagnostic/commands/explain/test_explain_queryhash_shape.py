"""Tests for explain queryPlanner.queryHash shape equivalence.

Parametrized over (queryA, queryB, same_shape) triples. For each pair the test
runs explain on both queries and asserts that their queryPlanner.queryHash
values either match (same_shape=True) or differ (same_shape=False).
"""

from dataclasses import dataclass
from typing import Any, Optional

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


def get_query_hash(
    collection,
    find_filter: dict,
    sort: Optional[dict] = None,
    projection: Optional[dict] = None,
    collation: Optional[dict] = None,
) -> str:
    """Return the queryPlanner.queryHash from explain for a find filter."""
    cmd: dict[str, Any] = {"find": collection.name, "filter": find_filter}
    if sort is not None:
        cmd["sort"] = sort
    if projection is not None:
        cmd["projection"] = projection
    if collation is not None:
        cmd["collation"] = collation
    result = execute_command(collection, {"explain": cmd, "verbosity": "queryPlanner"})
    if isinstance(result, Exception):
        raise RuntimeError(f"explain command failed: {result}")
    query_planner = result.get("queryPlanner", {})
    if "queryHash" not in query_planner:
        raise RuntimeError(f"explain did not return queryPlanner.queryHash; got: {result}")
    return str(query_planner["queryHash"])


@dataclass(frozen=True)
class QueryHashCase(BaseTestCase):
    """Test case comparing the queryHash of two find queries."""

    filter_a: Optional[dict] = None
    filter_b: Optional[dict] = None
    sort_a: Optional[dict] = None
    sort_b: Optional[dict] = None
    projection_a: Optional[dict] = None
    projection_b: Optional[dict] = None
    collation_a: Optional[dict] = None
    collation_b: Optional[dict] = None


SAME_SHAPE_TESTS: list[QueryHashCase] = [
    QueryHashCase(
        id="literal_value_scalar",
        filter_a={"a": {"$eq": 1}},
        filter_b={"a": {"$eq": 3}},
        msg="different scalar values with same operator should share a query shape",
    ),
    QueryHashCase(
        id="literal_value_array",
        filter_a={"a": {"$in": [1, 2, 3]}},
        filter_b={"a": {"$in": [4, 5, 6]}},
        msg="$in with same array length but different values should share a query shape",
    ),
    QueryHashCase(
        id="literal_value_document",
        filter_a={"a": {"$gt": 1}},
        filter_b={"a": {"$gt": 4}},
        msg="$gt with different operands should share a query shape",
    ),
    QueryHashCase(
        id="implicit_explicit_eq",
        filter_a={"a": 1},
        filter_b={"a": {"$eq": 1}},
        msg="implicit equality and explicit $eq should share a query shape",
    ),
    QueryHashCase(
        id="implicit_explicit_and",
        filter_a={"a": 1, "b": 2},
        filter_b={"$and": [{"a": 1}, {"b": 2}]},
        msg="implicit multi-field filter and explicit $and should share a query shape",
    ),
    QueryHashCase(
        id="field_clause_order",
        filter_a={"a": 1, "b": 2},
        filter_b={"b": 2, "a": 1},
        msg="reversed top-level field order should share a query shape",
    ),
    QueryHashCase(
        id="and_clause_order",
        filter_a={"$and": [{"a": 1}, {"b": 2}]},
        filter_b={"$and": [{"b": 2}, {"a": 1}]},
        msg="reversed $and clause order should share a query shape",
    ),
    QueryHashCase(
        id="comparison_operand_variation_gt",
        filter_a={"a": {"$gt": 0}},
        filter_b={"a": {"$gt": 10}},
        msg="$gt with different operands should share a query shape",
    ),
    QueryHashCase(
        id="comparison_operand_variation_lte",
        filter_a={"a": {"$lte": 2}},
        filter_b={"a": {"$lte": 4}},
        msg="$lte with different operands should share a query shape",
    ),
    QueryHashCase(
        id="in_value_variation",
        filter_a={"a": {"$in": [1, 2]}},
        filter_b={"a": {"$in": [3, 4]}},
        msg="$in with same length but different values should share a query shape",
    ),
    QueryHashCase(
        id="nin_value_variation",
        filter_a={"a": {"$nin": [1, 2]}},
        filter_b={"a": {"$nin": [3, 4]}},
        msg="$nin with same length but different values should share a query shape",
    ),
    QueryHashCase(
        id="all_value_variation",
        filter_a={"arr": {"$all": [1, 2]}},
        filter_b={"arr": {"$all": [3, 4]}},
        msg="$all with same length but different values should share a query shape",
    ),
    QueryHashCase(
        id="projection_field_order",
        filter_a={"a": 1},
        filter_b={"a": 1},
        projection_a={"a": 1, "b": 1},
        projection_b={"b": 1, "a": 1},
        msg="same projection fields in different order should share a query shape",
    ),
    QueryHashCase(
        id="not_operand_variation",
        filter_a={"a": {"$not": {"$gt": 1}}},
        filter_b={"a": {"$not": {"$gt": 3}}},
        msg="$not with different inner operands should share a query shape",
    ),
    QueryHashCase(
        id="mod_argument_variation",
        filter_a={"a": {"$mod": [2, 0]}},
        filter_b={"a": {"$mod": [3, 1]}},
        msg="$mod with different divisor/remainder should share a query shape",
    ),
    QueryHashCase(
        id="size_argument_variation",
        filter_a={"arr": {"$size": 2}},
        filter_b={"arr": {"$size": 3}},
        msg="$size with different values should share a query shape",
    ),
    QueryHashCase(
        id="elemMatch_inner_operand_variation",
        filter_a={"arr": {"$elemMatch": {"$gt": 0}}},
        filter_b={"arr": {"$elemMatch": {"$gt": 5}}},
        msg="$elemMatch with different inner operands should share a query shape",
    ),
    QueryHashCase(
        id="expr_arithmetic_operand_variation",
        filter_a={"$expr": {"$gt": ["$a", 1]}},
        filter_b={"$expr": {"$gt": ["$a", 3]}},
        msg="$expr with different literal operands should share a query shape",
    ),
    QueryHashCase(
        id="or_value_variation",
        filter_a={"$or": [{"a": 1}, {"b": 2}]},
        filter_b={"$or": [{"a": 3}, {"b": 4}]},
        msg="$or with different operand values should share a query shape",
    ),
    QueryHashCase(
        id="nor_value_variation",
        filter_a={"$nor": [{"a": 1}, {"b": 2}]},
        filter_b={"$nor": [{"a": 3}, {"b": 4}]},
        msg="$nor with different operand values should share a query shape",
    ),
    QueryHashCase(
        id="empty_filter",
        filter_a={},
        filter_b={},
        msg="two empty filters should share a query shape",
    ),
    QueryHashCase(
        id="dot_notation_value_variation",
        filter_a={"a.b": 1},
        filter_b={"a.b": 2},
        msg="dot-notation field path with different values should share a query shape",
    ),
    QueryHashCase(
        id="comparison_operand_variation_gte",
        filter_a={"a": {"$gte": 1}},
        filter_b={"a": {"$gte": 4}},
        msg="$gte with different operands should share a query shape",
    ),
    QueryHashCase(
        id="comparison_operand_variation_lt",
        filter_a={"a": {"$lt": 3}},
        filter_b={"a": {"$lt": 7}},
        msg="$lt with different operands should share a query shape",
    ),
    QueryHashCase(
        id="comparison_operand_variation_ne",
        filter_a={"a": {"$ne": 1}},
        filter_b={"a": {"$ne": 4}},
        msg="$ne with different operands should share a query shape",
    ),
    QueryHashCase(
        id="in_element_order_variation",
        filter_a={"a": {"$in": [1, 2, 3]}},
        filter_b={"a": {"$in": [3, 1, 2]}},
        msg="$in with same elements in different order should share a query shape",
    ),
    QueryHashCase(
        id="sort_absent_vs_no_sort",
        filter_a={"a": 1},
        filter_b={"a": 2},
        msg="same filter structure with no sort and different values should share a query shape",
    ),
    QueryHashCase(
        id="collation_strength_variation",
        filter_a={"s": "hello"},
        filter_b={"s": "world"},
        collation_a={"locale": "en", "strength": 1},
        collation_b={"locale": "en", "strength": 1},
        msg="same collation locale and strength with different values should share a query shape",
    ),
    QueryHashCase(
        id="regex_pattern_variation",
        filter_a={"s": {"$regex": "^1"}},
        filter_b={"s": {"$regex": "^2"}},
        msg="different $regex patterns are treated as literals and share a query shape",
    ),
    QueryHashCase(
        id="expr_operator_variation",
        filter_a={"$expr": {"$gt": ["$a", "$b"]}},
        filter_b={"$expr": {"$lt": ["$a", "$b"]}},
        msg="$expr operators are not part of the shape; different operators share a query shape",
    ),
    QueryHashCase(
        id="type_argument_variation",
        filter_a={"a": {"$type": "int"}},
        filter_b={"a": {"$type": "string"}},
        msg="$type argument is treated as a literal and shares a query shape",
    ),
    QueryHashCase(
        id="type_array_vs_string",
        filter_a={"a": {"$type": ["int"]}},
        filter_b={"a": {"$type": "int"}},
        msg="$type array form vs string form shares a query shape",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SAME_SHAPE_TESTS))
def test_explain_queryhash_same_shape(collection, test):
    """Test that structurally equivalent queries produce the same queryPlanner.queryHash."""
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "s": str(i)} for i in range(20)]
    )
    hash_a = get_query_hash(
        collection, test.filter_a, test.sort_a, test.projection_a, test.collation_a
    )
    hash_b = get_query_hash(
        collection, test.filter_b, test.sort_b, test.projection_b, test.collation_b
    )
    assertSuccess(
        {"queryHash": hash_a},
        {"queryHash": hash_b},
        msg=test.msg,
        raw_res=True,
    )


DIFF_SHAPE_TESTS: list[QueryHashCase] = [
    QueryHashCase(
        id="different_field_names",
        filter_a={"a": 1},
        filter_b={"b": 1},
        msg="queries on different fields should have different query shapes",
    ),
    QueryHashCase(
        id="comparison_operator_variation",
        filter_a={"a": {"$gt": 1}},
        filter_b={"a": {"$lt": 1}},
        msg="different comparison operators on the same field should have different query shapes",
    ),
    QueryHashCase(
        id="in_vs_nin",
        filter_a={"a": {"$in": [1, 2]}},
        filter_b={"a": {"$nin": [1, 2]}},
        msg="$in vs $nin should have different query shapes",
    ),
    QueryHashCase(
        id="and_vs_or",
        filter_a={"$and": [{"a": 1}, {"b": 2}]},
        filter_b={"$or": [{"a": 1}, {"b": 2}]},
        msg="$and vs $or should have different query shapes",
    ),
    QueryHashCase(
        id="or_vs_nor",
        filter_a={"$or": [{"a": 1}, {"b": 2}]},
        filter_b={"$nor": [{"a": 1}, {"b": 2}]},
        msg="$or vs $nor should have different query shapes",
    ),
    QueryHashCase(
        id="and_clause_count",
        filter_a={"$and": [{"a": 1}]},
        filter_b={"$and": [{"a": 1}, {"b": 2}]},
        msg="$and with different clause counts should have different query shapes",
    ),
    QueryHashCase(
        id="exists_true_vs_false",
        filter_a={"a": {"$exists": True}},
        filter_b={"a": {"$exists": False}},
        msg="$exists true vs false should have different query shapes",
    ),
    QueryHashCase(
        id="in_length_variation",
        filter_a={"a": {"$in": [1]}},
        filter_b={"a": {"$in": [1, 2]}},
        msg="$in with different array lengths should have different query shapes",
    ),
    QueryHashCase(
        id="not_inner_operator_variation",
        filter_a={"a": {"$not": {"$gt": 1}}},
        filter_b={"a": {"$not": {"$lt": 1}}},
        msg="$not with different inner operators should have different query shapes",
    ),
    QueryHashCase(
        id="sort_field_variation",
        filter_a={"a": {"$gt": 0}},
        filter_b={"a": {"$gt": 0}},
        sort_a={"a": 1},
        sort_b={"b": 1},
        msg="same filter sorted on different fields should have different query shapes",
    ),
    QueryHashCase(
        id="projection_field_set",
        filter_a={"a": 1},
        filter_b={"a": 1},
        projection_a={"a": 1},
        projection_b={"b": 1},
        msg="different projection field sets should have different query shapes",
    ),
    QueryHashCase(
        id="collation_locale_variation",
        filter_a={"s": "hello"},
        filter_b={"s": "hello"},
        collation_a={"locale": "en"},
        collation_b={"locale": "fr"},
        msg="different collation locales should have different query shapes",
    ),
    QueryHashCase(
        id="elemMatch_inner_operator_variation",
        filter_a={"arr": {"$elemMatch": {"$gt": 0}}},
        filter_b={"arr": {"$elemMatch": {"$lt": 0}}},
        msg="$elemMatch with different inner operators should have different query shapes",
    ),
    QueryHashCase(
        id="jsonSchema_field_variation",
        filter_a={"$jsonSchema": {"required": ["a"]}},
        filter_b={"$jsonSchema": {"required": ["b"]}},
        msg="$jsonSchema requiring different fields should have different query shapes",
    ),
    QueryHashCase(
        id="sort_direction_variation",
        filter_a={"a": {"$gt": 0}},
        filter_b={"a": {"$gt": 0}},
        sort_a={"a": 1},
        sort_b={"a": -1},
        msg="same filter with different sort directions should have different query shapes",
    ),
    QueryHashCase(
        id="compound_sort_field_order",
        filter_a={"a": {"$gt": 0}},
        filter_b={"a": {"$gt": 0}},
        sort_a={"a": 1, "b": 1},
        sort_b={"b": 1, "a": 1},
        msg="compound sort with different field order should have different query shapes",
    ),
    QueryHashCase(
        id="ne_vs_eq",
        filter_a={"a": {"$ne": 1}},
        filter_b={"a": {"$eq": 1}},
        msg="$ne vs $eq on the same field should have different query shapes",
    ),
    QueryHashCase(
        id="exists_vs_equality",
        filter_a={"a": {"$exists": True}},
        filter_b={"a": 1},
        msg="$exists:true vs equality predicate should have different query shapes",
    ),
    QueryHashCase(
        id="dot_notation_vs_top_level",
        filter_a={"a.b": 1},
        filter_b={"a": 1},
        msg="dot-notation path vs top-level field should have different query shapes",
    ),
    QueryHashCase(
        id="or_clause_count",
        filter_a={"$or": [{"a": 1}]},
        filter_b={"$or": [{"a": 1}, {"b": 2}]},
        msg="$or with different clause counts should have different query shapes",
    ),
    QueryHashCase(
        id="nor_clause_count",
        filter_a={"$nor": [{"a": 1}]},
        filter_b={"$nor": [{"a": 1}, {"b": 2}]},
        msg="$nor with different clause counts should have different query shapes",
    ),
    QueryHashCase(
        id="all_vs_in",
        filter_a={"arr": {"$all": [1, 2]}},
        filter_b={"arr": {"$in": [1, 2]}},
        msg="$all vs $in on the same field should have different query shapes",
    ),
    QueryHashCase(
        id="collation_present_vs_absent",
        filter_a={"s": "hello"},
        filter_b={"s": "hello"},
        collation_a={"locale": "en"},
        collation_b=None,
        msg="collation present vs absent should produce different query shapes",
    ),
    QueryHashCase(
        id="sort_present_vs_absent",
        filter_a={"a": 1},
        filter_b={"a": 1},
        sort_a={"a": 1},
        sort_b=None,
        msg="query with sort vs same query without sort should have different query shapes",
    ),
    QueryHashCase(
        id="projection_present_vs_absent",
        filter_a={"a": 1},
        filter_b={"a": 1},
        projection_a={"a": 1},
        projection_b=None,
        msg="projection present vs absent should produce different query shapes",
    ),
    QueryHashCase(
        id="projection_inclusion_vs_exclusion",
        filter_a={"a": 1},
        filter_b={"a": 1},
        projection_a={"b": 1},
        projection_b={"b": 0},
        msg="projection inclusion vs exclusion on the same field should differ in query shape",
    ),
    QueryHashCase(
        id="collation_strength_variation",
        filter_a={"s": "hello"},
        filter_b={"s": "hello"},
        collation_a={"locale": "en", "strength": 1},
        collation_b={"locale": "en", "strength": 2},
        msg="same locale with different collation strength should have different query shapes",
    ),
    QueryHashCase(
        id="in_length_all",
        filter_a={"arr": {"$all": [1]}},
        filter_b={"arr": {"$all": [1, 2]}},
        msg="$all with different array lengths should have different query shapes",
    ),
    QueryHashCase(
        id="jsonSchema_keyword_variation",
        filter_a={"$jsonSchema": {"required": ["a"]}},
        filter_b={"$jsonSchema": {"properties": {"a": {"bsonType": "int"}}}},
        msg="$jsonSchema with different keywords should have different query shapes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DIFF_SHAPE_TESTS))
def test_explain_queryhash_different_shape(collection, test):
    """Test that structurally distinct queries produce different queryPlanner.queryHash values."""
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "s": str(i)} for i in range(20)]
    )
    hash_a = get_query_hash(
        collection, test.filter_a, test.sort_a, test.projection_a, test.collation_a
    )
    hash_b = get_query_hash(
        collection, test.filter_b, test.sort_b, test.projection_b, test.collation_b
    )
    assertSuccess(
        {"hashes_differ": hash_a != hash_b},
        {"hashes_differ": True},
        msg=test.msg,
        raw_res=True,
    )


def test_explain_queryhash_plan_cache_filter_collapses_same_shape(collection):
    """Test that same-shape queries map to a single planCacheSetFilter entry.

    Pins the shape function across subsystems: planner -> plan-cache-filter ->
    explain. A divergence between them would cause planCacheListFilters to
    return two separate filter entries for queries that share a queryHash.
    """
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "s": str(i)} for i in range(20)]
    )
    collection.create_index([("a", 1)])
    collection.database.command({"planCacheClear": collection.name})

    filter_a = {"a": {"$eq": 1}}
    filter_b = {"a": {"$eq": 3}}

    hash_a = get_query_hash(collection, filter_a)
    hash_b = get_query_hash(collection, filter_b)
    if hash_a != hash_b:
        raise RuntimeError(
            f"pre-condition failed: filter_a and filter_b must share a query shape "
            f"(hash_a={hash_a!r}, hash_b={hash_b!r})"
        )

    set_result = execute_command(
        collection,
        {"planCacheSetFilter": collection.name, "query": filter_a, "indexes": [{"a": 1}]},
    )
    if isinstance(set_result, Exception) or set_result.get("ok") != 1.0:
        raise RuntimeError(f"planCacheSetFilter failed: {set_result}")

    list_result = execute_command(collection, {"planCacheListFilters": collection.name})
    if isinstance(list_result, Exception) or "filters" not in list_result:
        raise RuntimeError(f"planCacheListFilters failed: {list_result}")

    assertSuccess(
        {"filter_count": len(list_result["filters"])},
        {"filter_count": 1},
        msg="same-shape queries should map to exactly one plan cache filter entry",
        raw_res=True,
    )


def _explain_before_and_after_index(collection, find_filter: dict) -> tuple[dict, dict]:
    """Return (queryPlanner before index, queryPlanner after index) for find_filter."""
    result_before = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": find_filter}, "verbosity": "queryPlanner"},
    )
    if isinstance(result_before, Exception) or "queryPlanner" not in result_before:
        raise RuntimeError(f"explain before index failed: {result_before}")
    qp_before = result_before["queryPlanner"]
    if qp_before.get("queryHash") is None or qp_before.get("planCacheKey") is None:
        raise RuntimeError(f"explain did not return queryHash/planCacheKey: {result_before}")

    collection.create_index([("a", 1)])

    result_after = execute_command(
        collection,
        {"explain": {"find": collection.name, "filter": find_filter}, "verbosity": "queryPlanner"},
    )
    if isinstance(result_after, Exception) or "queryPlanner" not in result_after:
        raise RuntimeError(f"explain after index failed: {result_after}")
    return qp_before, result_after["queryPlanner"]


def test_explain_queryhash_stable_after_index_add(collection):
    """Test that queryHash is unchanged after an index is added.

    queryHash (planCacheShapeHash) depends only on the query shape, not on
    available indexes, so it must remain the same before and after index creation.
    """
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "s": str(i)} for i in range(20)]
    )
    qp_before, qp_after = _explain_before_and_after_index(collection, {"a": {"$eq": 1}})
    assertSuccess(
        {"queryHash": qp_after.get("queryHash")},
        {"queryHash": qp_before["queryHash"]},
        msg="queryHash must be stable across index creation",
        raw_res=True,
    )


def test_explain_planCacheKey_changes_after_index_add(collection):
    """Test that planCacheKey changes when an index is added.

    planCacheKey depends on both the query shape and the available indexes,
    so it must differ before and after index creation.
    """
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "s": str(i)} for i in range(20)]
    )
    qp_before, qp_after = _explain_before_and_after_index(collection, {"a": {"$eq": 1}})
    assertSuccess(
        {"planCacheKey_changed": qp_before["planCacheKey"] != qp_after.get("planCacheKey")},
        {"planCacheKey_changed": True},
        msg="planCacheKey must change after an index is added",
        raw_res=True,
    )
