"""Tests for partial index query behavior — coverage, filters, nested fields, edge cases."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

_DOCS_GT5 = (
    {"_id": 1, "a": 3},
    {"_id": 2, "a": 7},
    {"_id": 3, "a": 10},
    {"_id": 4, "a": 1},
)

_IDX_GT5 = (
    {"key": {"a": 1}, "name": "idx_partial_gt5", "partialFilterExpression": {"a": {"$gt": 5}}},
)

PARTIAL_QUERY_USAGE: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="exact_match_uses_index",
        doc=_DOCS_GT5,
        indexes=_IDX_GT5,
        filter={"a": {"$gt": 5}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        msg="Query matching partialFilterExpression exactly uses the index",
    ),
    IndexQueryTestCase(
        id="superset_uses_index",
        doc=_DOCS_GT5,
        indexes=_IDX_GT5,
        filter={"a": {"$gt": 8}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 3, "a": 10}],
        msg="Query with superset predicate (more restrictive) uses the index",
    ),
    IndexQueryTestCase(
        id="subset_does_not_cover",
        doc=_DOCS_GT5,
        indexes=_IDX_GT5,
        filter={"a": {"$gt": 2}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        msg="Query with weaker predicate only returns docs in the index when hint forces use",
    ),
]

_DOCS_EXISTS_B = (
    {"_id": 1, "a": 10, "b": "x"},
    {"_id": 2, "a": 20},
    {"_id": 3, "a": 30, "b": "y"},
)

_IDX_EXISTS_B = (
    {"key": {"a": 1}, "name": "idx_exists_b", "partialFilterExpression": {"b": {"$exists": True}}},
)

PARTIAL_QUERY_EXISTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="exists_query_covers_filter",
        doc=_DOCS_EXISTS_B,
        indexes=_IDX_EXISTS_B,
        filter={"b": {"$exists": True}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 10, "b": "x"}, {"_id": 3, "a": 30, "b": "y"}],
        msg="Query including $exists: true on filter field uses partial index",
    ),
    IndexQueryTestCase(
        id="without_filter_incomplete",
        doc=_DOCS_EXISTS_B,
        indexes=_IDX_EXISTS_B,
        filter={"a": {"$gt": 0}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 10, "b": "x"}, {"_id": 3, "a": 30, "b": "y"}],
        msg="Query without filter field returns only indexed docs when hint forces index",
    ),
]

PARTIAL_QUERY_RANGE: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="range_conjunction",
        doc=(
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 5},
            {"_id": 3, "a": 10},
            {"_id": 4, "a": 15},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_range",
                "partialFilterExpression": {"a": {"$gte": 5, "$lte": 10}},
            },
        ),
        filter={"a": {"$gte": 5, "$lte": 10}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 5}, {"_id": 3, "a": 10}],
        msg="Partial index with range conjunction works correctly",
    ),
]

PARTIAL_COMPLEX_FILTERS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="and_multiple_conditions",
        doc=(
            {"_id": 1, "a": 3, "b": 1},
            {"_id": 2, "a": 7, "b": 5},
            {"_id": 3, "a": 10, "b": 2},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_and",
                "partialFilterExpression": {"$and": [{"a": {"$gt": 5}}, {"b": {"$gt": 3}}]},
            },
        ),
        filter={"$and": [{"a": {"$gt": 5}}, {"b": {"$gt": 3}}]},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 7, "b": 5}],
        msg="Partial index with $and combining multiple conditions",
    ),
    IndexQueryTestCase(
        id="or_conditions",
        doc=(
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 50},
            {"_id": 4, "a": 100},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_or",
                "partialFilterExpression": {"$or": [{"a": {"$lt": 5}}, {"a": {"$gt": 80}}]},
            },
        ),
        filter={"$or": [{"a": {"$lt": 5}}, {"a": {"$gt": 80}}]},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 3}, {"_id": 4, "a": 100}],
        msg="Partial index with $or combining multiple conditions",
    ),
    IndexQueryTestCase(
        id="in_large_array",
        doc=(
            {"_id": 1, "status": "active"},
            {"_id": 2, "status": "pending"},
            {"_id": 3, "status": "closed"},
            {"_id": 4, "status": "active"},
        ),
        indexes=(
            {
                "key": {"status": 1},
                "name": "idx_in",
                "partialFilterExpression": {"status": {"$in": ["active", "pending"]}},
            },
        ),
        filter={"status": {"$in": ["active", "pending"]}},
        hint={"status": 1},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "status": "active"},
            {"_id": 2, "status": "pending"},
            {"_id": 4, "status": "active"},
        ],
        msg="Partial index with $in with multiple values",
    ),
    IndexQueryTestCase(
        id="in_query_subset_of_filter",
        doc=(
            {"_id": 1, "status": "active"},
            {"_id": 2, "status": "pending"},
            {"_id": 3, "status": "closed"},
        ),
        indexes=(
            {
                "key": {"status": 1},
                "name": "idx_in",
                "partialFilterExpression": {"status": {"$in": ["active", "pending", "review"]}},
            },
        ),
        filter={"status": {"$in": ["active", "pending"]}},
        hint={"status": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "status": "active"}, {"_id": 2, "status": "pending"}],
        msg="Query $in subset of filter $in — uses partial index correctly",
    ),
    IndexQueryTestCase(
        id="in_query_superset_of_filter",
        doc=(
            {"_id": 1, "status": "active"},
            {"_id": 2, "status": "pending"},
            {"_id": 3, "status": "closed"},
        ),
        indexes=(
            {
                "key": {"status": 1},
                "name": "idx_in",
                "partialFilterExpression": {"status": {"$in": ["active"]}},
            },
        ),
        filter={"status": {"$in": ["active", "pending"]}},
        hint={"status": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "status": "active"}],
        msg="Query $in superset of filter $in — only indexed docs returned with hint",
    ),
]

PARTIAL_NESTED_FIELDS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="nested_field_exists",
        doc=(
            {"_id": 1, "a": {"b": 1}},
            {"_id": 2, "a": {"c": 2}},
            {"_id": 3, "a": {"b": 5}},
        ),
        indexes=(
            {
                "key": {"a.b": 1},
                "name": "idx_nested",
                "partialFilterExpression": {"a.b": {"$exists": True}},
            },
        ),
        filter={"a.b": {"$exists": True}},
        hint={"a.b": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": {"b": 1}}, {"_id": 3, "a": {"b": 5}}],
        msg="Partial index on nested field with $exists: true",
    ),
    IndexQueryTestCase(
        id="nested_field_gt",
        doc=(
            {"_id": 1, "a": {"b": 1}},
            {"_id": 2, "a": {"b": 10}},
            {"_id": 3, "a": {"b": 20}},
        ),
        indexes=(
            {
                "key": {"a.b": 1},
                "name": "idx_nested_gt",
                "partialFilterExpression": {"a.b": {"$gt": 5}},
            },
        ),
        filter={"a.b": {"$gt": 5}},
        hint={"a.b": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": {"b": 10}}, {"_id": 3, "a": {"b": 20}}],
        msg="Partial index on nested field with $gt",
    ),
    IndexQueryTestCase(
        id="array_element_path",
        doc=(
            {"_id": 1, "arr": [10, 20, 30]},
            {"_id": 2, "arr": [1, 2, 3]},
            {"_id": 3, "arr": [5, 50, 500]},
        ),
        indexes=(
            {
                "key": {"arr.0": 1},
                "name": "idx_arr0",
                "partialFilterExpression": {"arr.0": {"$gt": 4}},
            },
        ),
        filter={"arr.0": {"$gt": 4}},
        hint={"arr.0": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "arr": [10, 20, 30]}, {"_id": 3, "arr": [5, 50, 500]}],
        msg="Partial index on arr.0 targets first array element",
    ),
]

PARTIAL_NON_KEY_FIELD: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="key_a_filter_b",
        doc=(
            {"_id": 1, "a": 10, "b": 1},
            {"_id": 2, "a": 20, "b": 5},
            {"_id": 3, "a": 30, "b": 10},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_a_filter_b",
                "partialFilterExpression": {"b": {"$gt": 3}},
            },
        ),
        filter={"b": {"$gt": 3}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 20, "b": 5}, {"_id": 3, "a": 30, "b": 10}],
        msg="Index on field 'a' with filter on field 'b'",
    ),
    IndexQueryTestCase(
        id="compound_key_filter_on_third_field",
        doc=(
            {"_id": 1, "a": 1, "b": 2, "c": 10},
            {"_id": 2, "a": 3, "b": 4, "c": 1},
            {"_id": 3, "a": 5, "b": 6, "c": 20},
        ),
        indexes=(
            {
                "key": {"a": 1, "b": 1},
                "name": "idx_ab_filter_c",
                "partialFilterExpression": {"c": {"$gt": 5}},
            },
        ),
        filter={"c": {"$gt": 5}},
        hint={"a": 1, "b": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1, "b": 2, "c": 10}, {"_id": 3, "a": 5, "b": 6, "c": 20}],
        msg="Compound index {a: 1, b: 1} with filter on field 'c'",
    ),
]

_DOCS_EXISTS_A = (
    {"_id": 1, "a": 10},
    {"_id": 2, "a": None},
    {"_id": 3},
)

_IDX_EXISTS_A = (
    {
        "key": {"a": 1},
        "name": "idx_partial_exists",
        "partialFilterExpression": {"a": {"$exists": True}},
    },
)

PARTIAL_NULL_MISSING: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="exists_includes_null",
        doc=_DOCS_EXISTS_A,
        indexes=_IDX_EXISTS_A,
        filter={"a": None},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": None}],
        msg="Partial index with $exists: true includes documents with null value",
    ),
    IndexQueryTestCase(
        id="exists_includes_valued",
        doc=_DOCS_EXISTS_A,
        indexes=_IDX_EXISTS_A,
        filter={"a": 10},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 10}],
        msg="Partial index with $exists: true includes documents with actual values",
    ),
    IndexQueryTestCase(
        id="gt_filter_null_handling",
        # Verifies null (_id: 4) and missing (_id: 5) do NOT satisfy $gt N —
        # differentiator from gt_zero_boundary, which only covers numeric boundaries.
        doc=(
            {"_id": 1, "a": 0},
            {"_id": 2, "a": 5},
            {"_id": 3, "a": 10},
            {"_id": 4, "a": None},
            {"_id": 5},
        ),
        indexes=(
            {"key": {"a": 1}, "name": "idx_gt5", "partialFilterExpression": {"a": {"$gt": 5}}},
        ),
        filter={"a": {"$gt": 5}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 3, "a": 10}],
        msg="Partial index with $gt filter — documents at or below threshold not indexed",
    ),
]

PARTIAL_EDGE_CASES: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="gt_zero_boundary",
        doc=(
            {"_id": 1, "a": -1},
            {"_id": 2, "a": 0},
            {"_id": 3, "a": 1},
        ),
        indexes=(
            {"key": {"a": 1}, "name": "idx_gt0", "partialFilterExpression": {"a": {"$gt": 0}}},
        ),
        filter={"a": {"$gt": 0}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 3, "a": 1}],
        msg="Filter {a: {$gt: 0}} — document with a=0 NOT indexed",
    ),
    IndexQueryTestCase(
        id="gte_zero_boundary",
        doc=(
            {"_id": 1, "a": -1},
            {"_id": 2, "a": 0},
            {"_id": 3, "a": 1},
        ),
        indexes=(
            {"key": {"a": 1}, "name": "idx_gte0", "partialFilterExpression": {"a": {"$gte": 0}}},
        ),
        filter={"a": {"$gte": 0}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 0}, {"_id": 3, "a": 1}],
        msg="Filter {a: {$gte: 0}} — document with a=0 IS indexed",
    ),
]

PARTIAL_ARRAY_MULTIKEY: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="array_field_with_gt_filter",
        doc=(
            {"_id": 1, "a": [3, 7, 10]},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [8, 20]},
        ),
        indexes=(
            {"key": {"a": 1}, "name": "idx_gt5", "partialFilterExpression": {"a": {"$gt": 5}}},
        ),
        filter={"a": {"$gt": 5}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": [3, 7, 10]}, {"_id": 3, "a": [8, 20]}],
        msg="Array with any element > 5 matches partial filter",
    ),
]

PARTIAL_NUMERIC_EQUIVALENCE: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="int_long_equivalence",
        doc=(
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 10},
        ),
        indexes=(
            {"key": {"a": 1}, "name": "idx_int", "partialFilterExpression": {"a": {"$gt": 5}}},
        ),
        filter={"a": {"$gt": Int64(5)}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        msg="{a: {$gt: int(5)}} matches same docs as {a: {$gt: long(5)}}",
    ),
    IndexQueryTestCase(
        id="double_int_equivalence",
        doc=(
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 10},
        ),
        indexes=(
            {"key": {"a": 1}, "name": "idx_double", "partialFilterExpression": {"a": {"$gt": 5.0}}},
        ),
        filter={"a": {"$gt": 5}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        msg="{a: {$gt: 5.0}} matches same docs as {a: {$gt: 5}}",
    ),
    IndexQueryTestCase(
        id="decimal128_int_equivalence",
        doc=(
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 10},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_dec",
                "partialFilterExpression": {"a": {"$gt": Decimal128("5")}},
            },
        ),
        filter={"a": {"$gt": 5}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        msg="{a: {$gt: Decimal128('5')}} matches same docs as {a: {$gt: int(5)}}",
    ),
]

PARTIAL_NAN_INFINITY: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="gt_nan",
        doc=(
            {"_id": 1, "a": float("nan")},
            {"_id": 2, "a": 3},
            {"_id": 3, "a": 10},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_nan",
                "partialFilterExpression": {"a": {"$gt": float("nan")}},
            },
        ),
        filter={"a": {"$gt": float("nan")}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[],
        msg="partialFilterExpression {$gt: NaN} indexes no documents (NaN comparison always false)",
    ),
    IndexQueryTestCase(
        id="gt_infinity",
        doc=(
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 10},
            {"_id": 3, "a": float("inf")},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_inf",
                "partialFilterExpression": {"a": {"$gt": float("inf")}},
            },
        ),
        filter={"a": {"$gt": float("inf")}},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[],
        msg="partialFilterExpression {$gt: Infinity} matches nothing",
    ),
]

PARTIAL_BSON_TYPE_DISTINCTION: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="bool_vs_int_distinction",
        doc=(
            {"_id": 1, "a": True},
            {"_id": 2, "a": 1},
            {"_id": 3, "a": False},
            {"_id": 4, "a": 0},
        ),
        indexes=(
            {"key": {"a": 1}, "name": "idx_bool_true", "partialFilterExpression": {"a": True}},
        ),
        filter={"a": True},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": True}],
        msg="partialFilterExpression {a: true} vs {a: 1} — different documents match",
    ),
    IndexQueryTestCase(
        id="null_matches_explicit_null_only",
        doc=(
            {"_id": 1, "a": None},
            {"_id": 2},
            {"_id": 3, "a": 0},
        ),
        indexes=({"key": {"a": 1}, "name": "idx_null", "partialFilterExpression": {"a": None}},),
        filter={"a": None},
        hint={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": None}, {"_id": 2}],
        msg="partialFilterExpression {a: null} matches docs with explicit null and missing",
    ),
]


PARTIAL_QUERY_FIND = (
    PARTIAL_QUERY_USAGE
    + PARTIAL_QUERY_EXISTS
    + PARTIAL_QUERY_RANGE
    + PARTIAL_COMPLEX_FILTERS
    + PARTIAL_NESTED_FIELDS
    + PARTIAL_NON_KEY_FIELD
    + PARTIAL_NULL_MISSING
    + PARTIAL_EDGE_CASES
    + PARTIAL_ARRAY_MULTIKEY
    + PARTIAL_NUMERIC_EQUIVALENCE
    + PARTIAL_NAN_INFINITY
    + PARTIAL_BSON_TYPE_DISTINCTION
)


@pytest.mark.parametrize("test", pytest_params(PARTIAL_QUERY_FIND))
def test_partial_query_find(collection, test):
    """Test partial index query behavior using the find command."""
    collection.insert_many(list(test.doc))
    execute_command(collection, {"createIndexes": collection.name, "indexes": list(test.indexes)})
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter, "hint": test.hint, "sort": test.sort},
    )
    assertSuccess(result, test.expected, msg=test.msg)


PARTIAL_QUERY_COUNT: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="exists_excludes_missing",
        doc=_DOCS_EXISTS_A,
        indexes=_IDX_EXISTS_A,
        filter={},
        hint={"a": 1},
        expected={"n": 2, "ok": 1.0},
        msg="Partial index with $exists: true excludes documents missing the field",
    ),
    IndexQueryTestCase(
        id="type_number_indexes_all_numerics",
        doc=(
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2.5},
            {"_id": 3, "a": Int64(3)},
            {"_id": 4, "a": "not_number"},
            {"_id": 5, "a": True},
        ),
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_type_num",
                "partialFilterExpression": {"a": {"$type": "number"}},
            },
        ),
        filter={"a": {"$type": "number"}},
        hint={"a": 1},
        expected={"n": 3, "ok": 1.0},
        msg="Filter {a: {$type: 'number'}} indexes all numeric types",
    ),
    IndexQueryTestCase(
        id="multikey_partial_index",
        # Empty-array edge case: tags: [] satisfies {$exists: true} and is indexed
        # as a single `undefined` multikey entry, so it counts toward the partial
        # index. _id: 4 (no `tags` field) does not match $exists and is excluded.
        # Expected n=3: _id 1 (["a","b"]), 2 (["c"]), 3 ([]).
        doc=(
            {"_id": 1, "tags": ["a", "b"]},
            {"_id": 2, "tags": ["c"]},
            {"_id": 3, "tags": []},
            {"_id": 4},
        ),
        indexes=(
            {
                "key": {"tags": 1},
                "name": "idx_tags_exists",
                "partialFilterExpression": {"tags": {"$exists": True}},
            },
        ),
        filter={"tags": {"$exists": True}},
        hint={"tags": 1},
        expected={"n": 3, "ok": 1.0},
        msg="Multikey partial index with $exists indexes docs with array field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PARTIAL_QUERY_COUNT))
def test_partial_query_count(collection, test):
    """Test partial index query behavior using the count command."""
    collection.insert_many(list(test.doc))
    execute_command(collection, {"createIndexes": collection.name, "indexes": list(test.indexes)})
    result = execute_command(
        collection,
        {"count": collection.name, "query": test.filter, "hint": test.hint},
    )
    assertSuccess(result, test.expected, raw_res=True, msg=test.msg)
