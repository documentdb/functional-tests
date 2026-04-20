"""
Tests for combining comparison query operators in the same query.

Covers range combinations ($gt/$lt/$gte/$lte), range with exclusions ($ne/$nin),
$in/$nin with comparisons, $not with comparisons, $or disjoint ranges,
multi-field combinations, and array field interactions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

RANGE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="open_range",
        filter={"a": {"$gt": 1, "$lt": 5}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 3}, {"_id": 3, "a": 5}],
        expected=[{"_id": 2, "a": 3}],
        msg="Open range excludes both endpoints",
    ),
    QueryTestCase(
        id="closed_range",
        filter={"a": {"$gte": 1, "$lte": 5}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 1}, {"_id": 3, "a": 5}, {"_id": 4, "a": 6}],
        expected=[{"_id": 2, "a": 1}, {"_id": 3, "a": 5}],
        msg="Closed range includes both endpoints",
    ),
    QueryTestCase(
        id="half_open_gt_lte",
        filter={"a": {"$gt": 1, "$lte": 5}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 3}, {"_id": 3, "a": 5}],
        expected=[{"_id": 2, "a": 3}, {"_id": 3, "a": 5}],
        msg="Half-open range: excludes lower, includes upper",
    ),
    QueryTestCase(
        id="half_open_gte_lt",
        filter={"a": {"$gte": 1, "$lt": 5}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 3}, {"_id": 3, "a": 5}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 3}],
        msg="Half-open range: includes lower, excludes upper",
    ),
    QueryTestCase(
        id="impossible_range",
        filter={"a": {"$gt": 5, "$lt": 1}},
        doc=[{"_id": 1, "a": 0}, {"_id": 2, "a": 3}, {"_id": 3, "a": 6}],
        expected=[],
        msg="Impossible range returns empty",
    ),
]

RANGE_EXCLUSION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="ne_with_gt_same_field",
        filter={"a": {"$ne": 3, "$gt": 0}},
        doc=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": 1},
            {"_id": 3, "a": 3},
            {"_id": 4, "a": 5},
        ],
        expected=[{"_id": 2, "a": 1}, {"_id": 4, "a": 5}],
        msg="$ne with $gt on same field — greater than 0 but not 3",
    ),
    QueryTestCase(
        id="ne_with_lt_same_field",
        filter={"a": {"$ne": 2, "$lt": 5}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
            {"_id": 4, "a": 6},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="$ne with $lt on same field — less than 5 but not 2",
    ),
    QueryTestCase(
        id="ne_inside_range_same_level",
        filter={"a": {"$ne": 3, "$gte": 1, "$lt": 5}},
        doc=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": 1},
            {"_id": 3, "a": 3},
            {"_id": 4, "a": 4},
            {"_id": 5, "a": 5},
        ],
        expected=[{"_id": 2, "a": 1}, {"_id": 4, "a": 4}],
        msg="$ne with range on same level — three operators",
    ),
    QueryTestCase(
        id="in_with_gt_same_level",
        filter={"a": {"$in": [1, 2, 3, 4, 5], "$gt": 3}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 3},
            {"_id": 3, "a": 4},
            {"_id": 4, "a": 5},
        ],
        expected=[{"_id": 3, "a": 4}, {"_id": 4, "a": 5}],
        msg="$in with $gt on same level",
    ),
    QueryTestCase(
        id="nin_with_range_same_level",
        filter={"a": {"$nin": [3, 5], "$gte": 1, "$lte": 7}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 3},
            {"_id": 3, "a": 5},
            {"_id": 4, "a": 7},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 4, "a": 7}],
        msg="$nin with range on same level",
    ),
]

IN_NIN_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nin_with_lte",
        filter={"a": {"$nin": [1, 2]}, "b": {"$lte": 5}},
        doc=[
            {"_id": 1, "a": 1, "b": 3},
            {"_id": 2, "a": 3, "b": 3},
            {"_id": 3, "a": 3, "b": 10},
        ],
        expected=[{"_id": 2, "a": 3, "b": 3}],
        msg="$nin with $lte on different fields",
    ),
]

EQ_NE_WITH_INEQUALITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="implicit_eq_with_lt",
        filter={"a": 1, "b": {"$lt": 10}},
        doc=[
            {"_id": 1, "a": 1, "b": 5},
            {"_id": 2, "a": 1, "b": 15},
            {"_id": 3, "a": 2, "b": 5},
        ],
        expected=[{"_id": 1, "a": 1, "b": 5}],
        msg="Implicit $eq with $lt on different fields",
    ),
]

NOT_WITH_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_gt",
        filter={"a": {"$not": {"$gt": 5}}},
        doc=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3},
        ],
        expected=[{"_id": 1, "a": 3}, {"_id": 3}],
        msg="$not $gt matches lte AND missing",
    ),
    QueryTestCase(
        id="not_lt",
        filter={"a": {"$not": {"$lt": 5}}},
        doc=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3},
        ],
        expected=[{"_id": 2, "a": 7}, {"_id": 3}],
        msg="$not $lt matches gte AND missing",
    ),
    QueryTestCase(
        id="not_in",
        filter={"a": {"$not": {"$in": [1, 2]}}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 3},
            {"_id": 3},
        ],
        expected=[{"_id": 2, "a": 3}, {"_id": 3}],
        msg="$not $in equivalent to $nin (includes missing)",
    ),
]

OR_DISJOINT_RANGE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="or_disjoint_ranges",
        filter={"$or": [{"a": {"$lt": 0}}, {"a": {"$gt": 10}}]},
        doc=[
            {"_id": 1, "a": -1},
            {"_id": 2, "a": 5},
            {"_id": 3, "a": 11},
        ],
        expected=[{"_id": 1, "a": -1}, {"_id": 3, "a": 11}],
        msg="$or with disjoint ranges (outside 0-10)",
    ),
    QueryTestCase(
        id="multi_field_three_operators",
        filter={"a": {"$gt": 0}, "b": {"$lt": 10}, "c": {"$ne": "x"}},
        doc=[
            {"_id": 1, "a": 1, "b": 5, "c": "x"},
            {"_id": 2, "a": 1, "b": 5, "c": "y"},
            {"_id": 3, "a": 0, "b": 5, "c": "y"},
            {"_id": 4, "a": 1, "b": 15, "c": "y"},
        ],
        expected=[{"_id": 2, "a": 1, "b": 5, "c": "y"}],
        msg="Three fields with $gt, $lt, and $ne",
    ),
]

ARRAY_RANGE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_field_range",
        filter={"scores": {"$gt": 80, "$lt": 90}},
        doc=[
            {"_id": 1, "scores": [70, 85, 95]},
            {"_id": 2, "scores": [60, 75]},
            {"_id": 3, "scores": [85]},
        ],
        expected=[
            {"_id": 1, "scores": [70, 85, 95]},
            {"_id": 3, "scores": [85]},
        ],
        msg="Range on array matches if any element in range",
    ),
    QueryTestCase(
        id="and_array_range",
        filter={"$and": [{"scores": {"$gte": 80}}, {"scores": {"$lte": 90}}]},
        doc=[
            {"_id": 1, "scores": [70, 95]},
            {"_id": 2, "scores": [85]},
            {"_id": 3, "scores": [60]},
        ],
        expected=[
            {"_id": 1, "scores": [70, 95]},
            {"_id": 2, "scores": [85]},
        ],
        msg="$and range on array — each condition matched independently",
    ),
]

MISSING_PAIR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="eq_with_gt_different_fields",
        filter={"a": {"$eq": 1}, "b": {"$gt": 5}},
        doc=[
            {"_id": 1, "a": 1, "b": 3},
            {"_id": 2, "a": 1, "b": 7},
            {"_id": 3, "a": 2, "b": 7},
        ],
        expected=[{"_id": 2, "a": 1, "b": 7}],
        msg="$eq with $gt on different fields",
    ),
    QueryTestCase(
        id="gt_with_nin_same_field",
        filter={"$and": [{"a": {"$gt": 0}}, {"a": {"$nin": [2, 4]}}]},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
            {"_id": 4, "a": 4},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="$gt with $nin on same field via $and",
    ),
    QueryTestCase(
        id="in_with_ne_different_fields",
        filter={"a": {"$in": [1, 2, 3]}, "b": {"$ne": "x"}},
        doc=[
            {"_id": 1, "a": 1, "b": "x"},
            {"_id": 2, "a": 2, "b": "y"},
            {"_id": 3, "a": 4, "b": "y"},
        ],
        expected=[{"_id": 2, "a": 2, "b": "y"}],
        msg="$in with $ne on different fields",
    ),
    QueryTestCase(
        id="in_and_nin_different_fields",
        filter={"a": {"$in": [1, 2, 3]}, "b": {"$nin": [10, 20]}},
        doc=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 2, "b": 30},
            {"_id": 3, "a": 4, "b": 30},
        ],
        expected=[{"_id": 2, "a": 2, "b": 30}],
        msg="$in and $nin on different fields",
    ),
]


ALL_TESTS = (
    RANGE_TESTS
    + RANGE_EXCLUSION_TESTS
    + IN_NIN_COMBINATION_TESTS
    + EQ_NE_WITH_INEQUALITY_TESTS
    + NOT_WITH_COMPARISON_TESTS
    + OR_DISJOINT_RANGE_TESTS
    + ARRAY_RANGE_TESTS
    + MISSING_PAIR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_query_combination_operators(collection, test):
    """Test comparison operator combinations in queries."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
