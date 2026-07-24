"""Tests for explain queryPlanner.queryHash shape equivalence.

Parametrized over (queryA, queryB, same_shape) triples. For each pair the test
runs explain on both queries and asserts that their queryPlanner.queryHash
values either match (same_shape=True) or differ (same_shape=False).
"""

from dataclasses import dataclass
from typing import Any, Optional

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


def get_query_hash(
    collection,
    find_filter: dict,
    sort: Optional[dict] = None,
    projection: Optional[dict] = None,
    collation: Optional[dict] = None,
) -> str:
    """Return queryPlanner.planCacheShapeHash from explain for a find filter."""
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
    if "planCacheShapeHash" not in query_planner:
        raise RuntimeError(f"explain did not return queryPlanner.planCacheShapeHash; got: {result}")
    return str(query_planner["planCacheShapeHash"])


def get_query_shape_hash(
    collection,
    find_filter: dict,
    sort: Optional[dict] = None,
    projection: Optional[dict] = None,
    collation: Optional[dict] = None,
) -> str:
    """Return the top-level queryShapeHash from explain for a find filter."""
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
    if "queryShapeHash" not in result:
        raise RuntimeError(f"explain did not return queryShapeHash; got: {result}")
    return str(result["queryShapeHash"])


@dataclass(frozen=True)
class QueryHashCase(BaseTestCase):
    """Test case comparing the queryHash of two find queries.

    query_shape_same overrides the expected same/different verdict specifically
    for queryShapeHash when it differs from planCacheShapeHash behaviour.
    Leave as None to inherit the planCacheShapeHash expectation.
    """

    filter_a: Optional[dict] = None
    filter_b: Optional[dict] = None
    sort_a: Optional[dict] = None
    sort_b: Optional[dict] = None
    projection_a: Optional[dict] = None
    projection_b: Optional[dict] = None
    collation_a: Optional[dict] = None
    collation_b: Optional[dict] = None
    query_shape_same: Optional[bool] = None


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
        query_shape_same=False,
        msg="reversed top-level field order should share a query shape",
    ),
    QueryHashCase(
        id="and_clause_order",
        filter_a={"$and": [{"a": 1}, {"b": 2}]},
        filter_b={"$and": [{"b": 2}, {"a": 1}]},
        query_shape_same=False,
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
        query_shape_same=False,
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
        query_shape_same=False,
        msg="$expr operators are not part of the shape; different operators share a query shape",
    ),
    QueryHashCase(
        id="type_argument_variation",
        filter_a={"a": {"$type": "int"}},
        filter_b={"a": {"$type": "string"}},
        query_shape_same=False,
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
    assertProperties(
        {"planCacheShapeHash": hash_a},
        {"planCacheShapeHash": Eq(hash_b)},
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
        query_shape_same=True,
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
    assertProperties(
        {"planCacheShapeHash": hash_a},
        {"planCacheShapeHash": Ne(hash_b)},
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(SAME_SHAPE_TESTS))
def test_explain_queryshapehash_same_shape(collection, test):
    """Test that structurally equivalent queries produce the same top-level queryShapeHash.

    Cases annotated with query_shape_same=False diverge from planCacheShapeHash
    behaviour: queryShapeHash preserves field order, $and clause order,
    projection order, $expr operators, and $type arguments.
    """
    expected_same = test.query_shape_same if test.query_shape_same is not None else True
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "s": str(i)} for i in range(20)]
    )
    hash_a = get_query_shape_hash(
        collection, test.filter_a, test.sort_a, test.projection_a, test.collation_a
    )
    hash_b = get_query_shape_hash(
        collection, test.filter_b, test.sort_b, test.projection_b, test.collation_b
    )
    check = Eq(hash_b) if expected_same else Ne(hash_b)
    assertProperties(
        {"queryShapeHash": hash_a}, {"queryShapeHash": check}, msg=test.msg, raw_res=True
    )


@pytest.mark.parametrize("test", pytest_params(DIFF_SHAPE_TESTS))
def test_explain_queryshapehash_different_shape(collection, test):
    """Test that structurally distinct queries produce different top-level queryShapeHash values.

    Cases annotated with query_shape_same=True diverge from planCacheShapeHash
    behaviour: queryShapeHash treats $in array length as irrelevant.
    """
    expected_same = test.query_shape_same if test.query_shape_same is not None else False
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "s": str(i)} for i in range(20)]
    )
    hash_a = get_query_shape_hash(
        collection, test.filter_a, test.sort_a, test.projection_a, test.collation_a
    )
    hash_b = get_query_shape_hash(
        collection, test.filter_b, test.sort_b, test.projection_b, test.collation_b
    )
    check = Eq(hash_b) if expected_same else Ne(hash_b)
    assertProperties(
        {"queryShapeHash": hash_a}, {"queryShapeHash": check}, msg=test.msg, raw_res=True
    )
