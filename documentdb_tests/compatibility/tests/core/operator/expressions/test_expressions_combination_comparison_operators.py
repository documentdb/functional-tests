"""
Tests for comparison operators combined with other expression operators.

Covers $eq/$ne edge cases, $gt/$gte/$lt/$lte/$cmp operator compositions,
and cross-operator combinations.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EQ_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "eq_add_int_vs_double",
        expression={"$eq": [{"$add": [1, 2]}, 3.0]},
        expected=True,
        msg="$add returns int, compared to double — cross-type numeric equality",
    ),
    ExpressionTestCase(
        "eq_subtract_negative_zero",
        expression={"$eq": [{"$multiply": [-1, 0.0]}, 0]},
        expected=True,
        msg="$subtract producing -0.0 equals int 0",
    ),
    ExpressionTestCase(
        "eq_multiply_overflow_to_double",
        expression={"$eq": [{"$multiply": [2147483647, 2]}, 4294967294]},
        expected=True,
        msg="$multiply overflowing int32 promotes correctly",
    ),
    ExpressionTestCase(
        "eq_ifNull_null_propagation",
        expression={"$eq": [{"$ifNull": [None, None]}, None]},
        expected=True,
        msg="$ifNull with both null returns null, equals null literal",
    ),
]

NE_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ne_concat_empty_vs_literal",
        expression={"$ne": [{"$concat": ["", ""]}, ""]},
        expected=False,
        msg="$concat of empty strings equals empty string",
    ),
]

EQ_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "eq_ifNull_missing_field_fallback",
        expression={"$eq": [{"$ifNull": ["$missing", "default"]}, "default"]},
        doc={"a": 1},
        expected=True,
        msg="$ifNull falls back to default for missing field",
    ),
    ExpressionTestCase(
        "eq_ifNull_null_field_fallback",
        expression={"$eq": [{"$ifNull": ["$a", "default"]}, "default"]},
        doc={"a": None},
        expected=True,
        msg="$ifNull falls back to default for null field",
    ),
    ExpressionTestCase(
        "eq_ifNull_existing_field_no_fallback",
        expression={"$eq": [{"$ifNull": ["$a", "default"]}, 42]},
        doc={"a": 42},
        expected=True,
        msg="$ifNull returns existing non-null field, not default",
    ),
    ExpressionTestCase(
        "eq_let_null_vs_missing",
        expression={"$let": {"vars": {"x": None}, "in": {"$eq": ["$$x", "$missing"]}}},
        doc={"a": 1},
        expected=False,
        msg="$let null variable not equal to missing field",
    ),
    ExpressionTestCase(
        "eq_filter_null_elements",
        expression={
            "$filter": {
                "input": [1, None, 2, None, 3],
                "as": "val",
                "cond": {"$ne": ["$$val", None]},
            }
        },
        doc={"a": 1},
        expected=[1, 2, 3],
        msg="$filter with $ne null removes null elements",
    ),
    ExpressionTestCase(
        "eq_root",
        expression={"$eq": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"a": 5, "b": 5},
        expected=True,
        msg="$$ROOT.a == $$ROOT.b",
    ),
    ExpressionTestCase(
        "eq_current",
        expression={"$eq": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"a": 5, "b": 5},
        expected=True,
        msg="$$CURRENT.a == $$CURRENT.b",
    ),
    ExpressionTestCase(
        "eq_add",
        expression={"$eq": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 7},
        expected=True,
        msg="$eq: add(3,4)=7 == 7",
    ),
    ExpressionTestCase(
        "eq_subtract",
        expression={"$eq": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 7},
        expected=True,
        msg="$eq: subtract(10,3)=7 == 7",
    ),
]

NE_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ne_cond_nested_eq_as_condition",
        expression={"$ne": [{"$cond": [{"$eq": ["$a", 1]}, "match", "no"]}, "match"]},
        doc={"a": 1},
        expected=False,
        msg="$cond with $eq condition feeds into $ne",
    ),
    ExpressionTestCase(
        "ne_filter",
        expression={"$filter": {"input": "$arr", "as": "x", "cond": {"$ne": ["$$x", 2]}}},
        doc={"arr": [1, 2, 3, 4]},
        expected=[1, 3, 4],
        msg="$filter with $ne != 2",
    ),
    ExpressionTestCase(
        "ne_root",
        expression={"$ne": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"a": 10, "b": 5},
        expected=True,
        msg="$$ROOT.a != $$ROOT.b",
    ),
    ExpressionTestCase(
        "ne_current",
        expression={"$ne": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"a": 10, "b": 5},
        expected=True,
        msg="$$CURRENT.a != $$CURRENT.b",
    ),
    ExpressionTestCase(
        "ne_add",
        expression={"$ne": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 8},
        expected=True,
        msg="$ne: add(3,4)=7 != 8",
    ),
    ExpressionTestCase(
        "ne_subtract",
        expression={"$ne": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 8},
        expected=True,
        msg="$ne: subtract(10,3)=7 != 8",
    ),
]

GT_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "gt_let",
        expression={"$let": {"vars": {"x": 10, "y": 5}, "in": {"$gt": ["$$x", "$$y"]}}},
        expected=True,
        msg="$gt with $let: 10 > 5",
    ),
    ExpressionTestCase(
        "gt_cond",
        expression={"$cond": [{"$gt": [10, 5]}, "yes", "no"]},
        expected="yes",
        msg="$gt inside $cond",
    ),
    ExpressionTestCase(
        "gt_switch",
        expression={
            "$switch": {
                "branches": [{"case": {"$gt": [10, 5]}, "then": "matched"}],
                "default": "no",
            }
        },
        expected="matched",
        msg="$gt inside $switch",
    ),
    ExpressionTestCase(
        "gt_ifnull",
        expression={"$gt": [{"$ifNull": [None, 10]}, 5]},
        expected=True,
        msg="$gt with $ifNull(null,10)=10 > 5",
    ),
]

GT_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "gt_filter",
        expression={"$filter": {"input": "$arr", "as": "x", "cond": {"$gt": ["$$x", 2]}}},
        doc={"arr": [1, 2, 3, 4]},
        expected=[3, 4],
        msg="$filter with $gt > 2",
    ),
    ExpressionTestCase(
        "gt_root",
        expression={"$gt": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"a": 10, "b": 5},
        expected=True,
        msg="$$ROOT.a > $$ROOT.b",
    ),
    ExpressionTestCase(
        "gt_current",
        expression={"$gt": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"a": 10, "b": 5},
        expected=True,
        msg="$$CURRENT.a > $$CURRENT.b",
    ),
    ExpressionTestCase(
        "gt_add",
        expression={"$gt": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 6},
        expected=True,
        msg="$gt: add(3,4)=7 > 6",
    ),
    ExpressionTestCase(
        "gt_subtract",
        expression={"$gt": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 6},
        expected=True,
        msg="$gt: subtract(10,3)=7 > 6",
    ),
]

GTE_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "gte_let",
        expression={"$let": {"vars": {"x": 10, "y": 5}, "in": {"$gte": ["$$x", "$$y"]}}},
        expected=True,
        msg="$gte with $let: 10 >= 5",
    ),
    ExpressionTestCase(
        "gte_cond",
        expression={"$cond": [{"$gte": [10, 5]}, "yes", "no"]},
        expected="yes",
        msg="$gte inside $cond",
    ),
    ExpressionTestCase(
        "gte_switch",
        expression={
            "$switch": {
                "branches": [{"case": {"$gte": [10, 10]}, "then": "matched"}],
                "default": "no",
            }
        },
        expected="matched",
        msg="$gte inside $switch (equal)",
    ),
    ExpressionTestCase(
        "gte_ifnull",
        expression={"$gte": [{"$ifNull": [None, 10]}, 10]},
        expected=True,
        msg="$gte with $ifNull(null,10)=10 >= 10",
    ),
]

GTE_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "gte_filter",
        expression={"$filter": {"input": "$arr", "as": "x", "cond": {"$gte": ["$$x", 3]}}},
        doc={"arr": [1, 2, 3, 4]},
        expected=[3, 4],
        msg="$filter with $gte >= 3",
    ),
    ExpressionTestCase(
        "gte_root",
        expression={"$gte": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"a": 10, "b": 5},
        expected=True,
        msg="$$ROOT.a >= $$ROOT.b",
    ),
    ExpressionTestCase(
        "gte_current",
        expression={"$gte": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"a": 10, "b": 5},
        expected=True,
        msg="$$CURRENT.a >= $$CURRENT.b",
    ),
    ExpressionTestCase(
        "gte_add",
        expression={"$gte": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 7},
        expected=True,
        msg="$gte: add(3,4)=7 >= 7",
    ),
    ExpressionTestCase(
        "gte_subtract",
        expression={"$gte": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 7},
        expected=True,
        msg="$gte: subtract(10,3)=7 >= 7",
    ),
]

LT_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "lt_let",
        expression={"$let": {"vars": {"x": 5, "y": 10}, "in": {"$lt": ["$$x", "$$y"]}}},
        expected=True,
        msg="$lt with $let: 5 < 10",
    ),
    ExpressionTestCase(
        "lt_cond",
        expression={"$cond": [{"$lt": [3, 5]}, "yes", "no"]},
        expected="yes",
        msg="$lt inside $cond",
    ),
    ExpressionTestCase(
        "lt_switch",
        expression={
            "$switch": {
                "branches": [{"case": {"$lt": [3, 5]}, "then": "matched"}],
                "default": "no",
            }
        },
        expected="matched",
        msg="$lt inside $switch",
    ),
    ExpressionTestCase(
        "lt_ifnull",
        expression={"$lt": [{"$ifNull": [None, 3]}, 5]},
        expected=True,
        msg="$lt with $ifNull(null,3)=3 < 5",
    ),
]

LT_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "lt_filter",
        expression={"$filter": {"input": "$arr", "as": "x", "cond": {"$lt": ["$$x", 3]}}},
        doc={"arr": [1, 2, 3, 4]},
        expected=[1, 2],
        msg="$filter with $lt < 3",
    ),
    ExpressionTestCase(
        "lt_root",
        expression={"$lt": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"a": 5, "b": 10},
        expected=True,
        msg="$$ROOT.a < $$ROOT.b",
    ),
    ExpressionTestCase(
        "lt_current",
        expression={"$lt": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"a": 5, "b": 10},
        expected=True,
        msg="$$CURRENT.a < $$CURRENT.b",
    ),
    ExpressionTestCase(
        "lt_add",
        expression={"$lt": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 8},
        expected=True,
        msg="$lt: add(3,4)=7 < 8",
    ),
    ExpressionTestCase(
        "lt_subtract",
        expression={"$lt": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 8},
        expected=True,
        msg="$lt: subtract(10,3)=7 < 8",
    ),
]

LTE_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "lte_let",
        expression={"$let": {"vars": {"x": 5, "y": 10}, "in": {"$lte": ["$$x", "$$y"]}}},
        expected=True,
        msg="$lte with $let: 5 <= 10",
    ),
    ExpressionTestCase(
        "lte_cond",
        expression={"$cond": [{"$lte": [3, 5]}, "yes", "no"]},
        expected="yes",
        msg="$lte inside $cond",
    ),
    ExpressionTestCase(
        "lte_switch",
        expression={
            "$switch": {
                "branches": [{"case": {"$lte": [5, 5]}, "then": "matched"}],
                "default": "no",
            }
        },
        expected="matched",
        msg="$lte inside $switch (equal)",
    ),
    ExpressionTestCase(
        "lte_ifnull",
        expression={"$lte": [{"$ifNull": [None, 3]}, 5]},
        expected=True,
        msg="$lte with $ifNull(null,3)=3 <= 5",
    ),
]

LTE_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "lte_filter",
        expression={"$filter": {"input": "$arr", "as": "x", "cond": {"$lte": ["$$x", 2]}}},
        doc={"arr": [1, 2, 3, 4]},
        expected=[1, 2],
        msg="$filter with $lte <= 2",
    ),
    ExpressionTestCase(
        "lte_root",
        expression={"$lte": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"a": 5, "b": 10},
        expected=True,
        msg="$$ROOT.a <= $$ROOT.b",
    ),
    ExpressionTestCase(
        "lte_current",
        expression={"$lte": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"a": 5, "b": 10},
        expected=True,
        msg="$$CURRENT.a <= $$CURRENT.b",
    ),
    ExpressionTestCase(
        "lte_add",
        expression={"$lte": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 7},
        expected=True,
        msg="$lte: add(3,4)=7 <= 7",
    ),
    ExpressionTestCase(
        "lte_subtract",
        expression={"$lte": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 7},
        expected=True,
        msg="$lte: subtract(10,3)=7 <= 7",
    ),
]

CMP_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "cmp_let_gt",
        expression={"$let": {"vars": {"x": 10, "y": 5}, "in": {"$cmp": ["$$x", "$$y"]}}},
        expected=1,
        msg="$cmp with $let: 10 > 5 returns 1",
    ),
    ExpressionTestCase(
        "cmp_let_eq",
        expression={"$let": {"vars": {"x": 5, "y": 5}, "in": {"$cmp": ["$$x", "$$y"]}}},
        expected=0,
        msg="$cmp with $let: 5 == 5 returns 0",
    ),
    ExpressionTestCase(
        "cmp_let_lt",
        expression={"$let": {"vars": {"x": 3, "y": 10}, "in": {"$cmp": ["$$x", "$$y"]}}},
        expected=-1,
        msg="$cmp with $let: 3 < 10 returns -1",
    ),
    ExpressionTestCase(
        "cmp_cond",
        expression={"$cond": [{"$eq": [{"$cmp": [10, 5]}, 1]}, "yes", "no"]},
        expected="yes",
        msg="$cmp inside $cond: 10 > 5 yields 1",
    ),
    ExpressionTestCase(
        "cmp_switch",
        expression={
            "$switch": {
                "branches": [{"case": {"$eq": [{"$cmp": [3, 5]}, -1]}, "then": "less"}],
                "default": "other",
            }
        },
        expected="less",
        msg="$cmp inside $switch: 3 < 5 yields -1",
    ),
    ExpressionTestCase(
        "cmp_ifnull",
        expression={"$cmp": [{"$ifNull": [None, 10]}, 5]},
        expected=1,
        msg="$cmp with $ifNull(null,10)=10 > 5 returns 1",
    ),
]

CMP_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "cmp_root",
        expression={"$cmp": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"a": 10, "b": 5},
        expected=1,
        msg="$cmp $$ROOT.a > $$ROOT.b returns 1",
    ),
    ExpressionTestCase(
        "cmp_current",
        expression={"$cmp": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"a": 5, "b": 10},
        expected=-1,
        msg="$cmp $$CURRENT.a < $$CURRENT.b returns -1",
    ),
    ExpressionTestCase(
        "cmp_field_refs_equal",
        expression={"$cmp": ["$a", "$b"]},
        doc={"a": 7, "b": 7},
        expected=0,
        msg="$cmp equal field refs returns 0",
    ),
    ExpressionTestCase(
        "cmp_filter",
        expression={
            "$filter": {
                "input": "$arr",
                "as": "x",
                "cond": {"$eq": [{"$cmp": ["$$x", 2]}, 1]},
            }
        },
        doc={"arr": [1, 2, 3, 4]},
        expected=[3, 4],
        msg="$filter with $cmp > 2",
    ),
    ExpressionTestCase(
        "cmp_add",
        expression={"$cmp": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 7},
        expected=0,
        msg="$cmp: add(3,4)=7 == 7 returns 0",
    ),
    ExpressionTestCase(
        "cmp_subtract",
        expression={"$cmp": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 8},
        expected=-1,
        msg="$cmp: subtract(10,3)=7 < 8 returns -1",
    ),
]

CROSS_OP_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "gt_and_lt_range_true",
        expression={"$and": [{"$gt": ["$a", 1]}, {"$lt": ["$a", 10]}]},
        doc={"a": 5},
        expected=True,
        msg="1 < 5 < 10",
    ),
    ExpressionTestCase(
        "gt_and_lt_range_false_low",
        expression={"$and": [{"$gt": ["$a", 1]}, {"$lt": ["$a", 10]}]},
        doc={"a": 0},
        expected=False,
        msg="0 not > 1",
    ),
    ExpressionTestCase(
        "gte_and_lte_range_boundary",
        expression={"$and": [{"$gte": ["$a", 1]}, {"$lte": ["$a", 10]}]},
        doc={"a": 1},
        expected=True,
        msg="1 >= 1 and 1 <= 10 (inclusive boundary)",
    ),
    ExpressionTestCase(
        "gt_and_lte_range_boundary_excluded",
        expression={"$and": [{"$gt": ["$a", 1]}, {"$lte": ["$a", 10]}]},
        doc={"a": 1},
        expected=False,
        msg="1 not > 1 (exclusive lower)",
    ),
    ExpressionTestCase(
        "or_gt_lt_false",
        expression={"$or": [{"$gt": ["$a", 10]}, {"$lt": ["$a", 1]}]},
        doc={"a": 5},
        expected=False,
        msg="5 not > 10 and 5 not < 1",
    ),
    ExpressionTestCase(
        "or_gt_lt_true",
        expression={"$or": [{"$gt": ["$a", 10]}, {"$lt": ["$a", 1]}]},
        doc={"a": 20},
        expected=True,
        msg="20 > 10",
    ),
]

ALL_LITERAL_TESTS = (
    EQ_LITERAL_TESTS
    + NE_LITERAL_TESTS
    + GT_LITERAL_TESTS
    + GTE_LITERAL_TESTS
    + LT_LITERAL_TESTS
    + LTE_LITERAL_TESTS
    + CMP_LITERAL_TESTS
)

ALL_INSERT_TESTS = (
    EQ_INSERT_TESTS
    + NE_INSERT_TESTS
    + GT_INSERT_TESTS
    + GTE_INSERT_TESTS
    + LT_INSERT_TESTS
    + LTE_INSERT_TESTS
    + CMP_INSERT_TESTS
    + CROSS_OP_INSERT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_LITERAL_TESTS))
def test_combination_literal(collection, test):
    """Test comparison operator compositions with literal inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_combination_insert(collection, test):
    """Test comparison operator compositions requiring document insertion."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_eq_remove_in_project(collection):
    """Test that $$REMOVE via $cond with $eq omits field from $project output."""
    collection.insert_one({"a": None, "b": "keep"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "b": 1,
                        "check": {"$cond": [{"$eq": ["$a", None]}, "$$REMOVE", "kept"]},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"b": "keep"}], "$$REMOVE omits field when $eq triggers it")


def test_ne_remove_in_project(collection):
    """Test that $$REMOVE in $cond else branch with $ne omits field."""
    collection.insert_one({"a": 1, "b": "keep"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "b": 1,
                        "check": {"$cond": [{"$ne": ["$a", 1]}, "kept", "$$REMOVE"]},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"b": "keep"}],
        "$$REMOVE omits field when $ne else branch selected",
    )
