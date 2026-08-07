"""
Tests for $covarianceSamp with nested field paths, array field traversal,
expressions that return different types per document, and $project
removing fields before $setWindowFields.

Covers: dotted field paths, missing intermediate paths, array index access,
array-of-objects traversal, top-level array fields, expressions returning
mixed types per row, and pipeline stages removing expression fields.

$covarianceSamp takes two expressions: ["$x", "$y"]. These tests exercise
various field path forms for both expressions.

Key difference from $covariancePop: single valid pair returns null (N-1=0),
and computed values use N-1 divisor.
"""

from datetime import datetime, timezone

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

# Property [Dotted Field Path]:
# Tests that $covarianceSamp correctly accesses nested document values via dotted paths.


def test_covarianceSamp_dotted_field_path(collection):
    """$covarianceSamp with dotted field path accesses nested document value."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"x": 1, "y": 2}}},
        {"_id": 2, "partition": "A", "data": {"metrics": {"x": 2, "y": 4}}},
        {"_id": 3, "partition": "A", "data": {"metrics": {"x": 3, "y": 6}}},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$data.metrics.x", "$data.metrics.y"],
    )
    # x=[1,2,3], y=[2,4,6] -> covSamp = 4/2 = 2.0
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "data": {"metrics": {"x": 1, "y": 2}},
            "result": 2.0,
        },
        {
            "_id": 2,
            "partition": "A",
            "data": {"metrics": {"x": 2, "y": 4}},
            "result": 2.0,
        },
        {
            "_id": 3,
            "partition": "A",
            "data": {"metrics": {"x": 3, "y": 6}},
            "result": 2.0,
        },
    ]
    assertSuccess(
        result, expected, msg="dotted field path accesses nested value for both expressions"
    )


# Property [Missing Intermediate Path]:
# Tests that missing intermediate paths are treated as missing (row ignored).


def test_covarianceSamp_missing_intermediate_path_x(collection):
    """$covarianceSamp with missing intermediate path in first expression (x) — row ignored."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"x": 1}, "y": 2},
        {"_id": 2, "partition": "A", "y": 4},  # missing data.x entirely
        {"_id": 3, "partition": "A", "data": {"x": 3}, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$data.x", "$y"],
    )
    # Doc 2 has missing x -> ignored. Only pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covSamp = ((-1)(-2)+(1)(2))/1 = 4/1 = 4.0
    expected = [
        {"_id": 1, "partition": "A", "data": {"x": 1}, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "data": {"x": 3}, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="missing intermediate path in x -> row ignored")


def test_covarianceSamp_missing_intermediate_path_y(collection):
    """$covarianceSamp with missing intermediate path in second expression (y) — row ignored."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "data": {"y": 2}},
        {"_id": 2, "partition": "A", "x": 2, "data": {"other": 99}},  # missing data.y
        {"_id": 3, "partition": "A", "x": 3, "data": {"y": 6}},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$data.y"],
    )
    # Doc 2 has missing y -> ignored. Only pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covSamp = ((-1)(-2)+(1)(2))/1 = 4/1 = 4.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "data": {"y": 2}, "result": 4.0},
        {"_id": 2, "partition": "A", "x": 2, "data": {"other": 99}, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "data": {"y": 6}, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="missing intermediate path in y -> row ignored")


def test_covarianceSamp_top_level_missing_object(collection):
    """$covarianceSamp where the top-level field of a dotted path is missing."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"x": 1, "y": 2}},
        {"_id": 2, "partition": "A"},  # missing 'data' entirely
        {"_id": 3, "partition": "A", "data": {"x": 3, "y": 6}},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$data.x", "$data.y"],
    )
    # Doc 2 missing both x and y -> ignored. Pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covSamp = 4.0
    expected = [
        {"_id": 1, "partition": "A", "data": {"x": 1, "y": 2}, "result": 4.0},
        {"_id": 2, "partition": "A", "result": 4.0},
        {"_id": 3, "partition": "A", "data": {"x": 3, "y": 6}, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="top-level field missing in dotted path = row ignored")


# Property [Null Value in Nested Path]:
# Tests that a field existing with null value through a dotted path is ignored.


def test_covarianceSamp_nested_field_explicit_null(collection):
    """$covarianceSamp with nested field that exists but is null — row ignored."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"x": 1}, "y": 2},
        {"_id": 2, "partition": "A", "data": {"x": None}, "y": 4},  # x exists but null
        {"_id": 3, "partition": "A", "data": {"x": 3}, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$data.x", "$y"],
    )
    # Doc 2 has explicit null in data.x -> ignored. Pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covSamp = ((-1)(-2)+(1)(2))/1 = 4/1 = 4.0
    expected = [
        {"_id": 1, "partition": "A", "data": {"x": 1}, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "data": {"x": None}, "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "data": {"x": 3}, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="nested field with explicit null = row ignored")


# Property [Array Field Non-Numeric]:
# Tests that top-level array values are treated as non-numeric and ignored.


def test_covarianceSamp_array_field_is_non_numeric(collection):
    """$covarianceSamp on a top-level array field — arrays are non-numeric, should be ignored."""
    docs = [
        {"_id": 1, "partition": "A", "x": [1, 2, 3], "y": 10},
        {"_id": 2, "partition": "A", "x": 5, "y": 20},
        {"_id": 3, "partition": "A", "x": [4, 5], "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Docs 1 and 3 have array x -> non-numeric -> ignored
    # Only doc 2 has numeric x. Single numeric pair -> covSamp = null (N-1=0)
    expected = [
        {"_id": 1, "partition": "A", "x": [1, 2, 3], "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 5, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": [4, 5], "y": 30, "result": None},
    ]
    assertSuccess(
        result,
        expected,
        msg="array field values are non-numeric — ignored, single pair returns null",
    )


# Property [Array at Intermediate Path Level]:
# Tests that a dotted path traversing through an array-of-objects resolves to an
# array (non-numeric) and is ignored.


def test_covarianceSamp_array_of_objects_traversal(collection):
    """$covarianceSamp with path traversing array-of-objects — resolves to array, ignored."""
    docs = [
        {"_id": 1, "partition": "A", "items": [{"value": 10}, {"value": 20}], "y": 100},
        {"_id": 2, "partition": "A", "items": {"value": 5}, "y": 200},
        {"_id": 3, "partition": "A", "items": [{"value": 30}, {"value": 40}], "y": 300},
        {"_id": 4, "partition": "A", "items": {"value": 15}, "y": 400},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$items.value", "$y"],
    )
    # Docs 1,3: items is array-of-objects -> $items.value resolves to
    # [10,20]/[30,40] (array) -> ignored
    # Docs 2,4: items is plain object -> $items.value resolves to 5/15 (scalar) -> participates
    # Valid pairs: (5, 200) and (15, 400)
    # mean_x=10, mean_y=300, covSamp = ((-5)(-100)+(5)(100))/1 = 1000/1 = 1000.0
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "items": [{"value": 10}, {"value": 20}],
            "y": 100,
            "result": 1000.0,
        },
        {"_id": 2, "partition": "A", "items": {"value": 5}, "y": 200, "result": 1000.0},
        {
            "_id": 3,
            "partition": "A",
            "items": [{"value": 30}, {"value": 40}],
            "y": 300,
            "result": 1000.0,
        },
        {"_id": 4, "partition": "A", "items": {"value": 15}, "y": 400, "result": 1000.0},
    ]
    assertSuccess(result, expected, msg="path through array-of-objects resolves to array — ignored")


# Property [Expression Returns Mixed Types]:
# Tests that non-numeric expression results are ignored in the computation.


def test_covarianceSamp_expression_returns_different_types(collection):
    """$covarianceSamp expression returning different types per row — non-numeric ignored."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10, "y": 20},
        {"_id": 2, "partition": "A", "x": -5, "y": 40},
        {"_id": 3, "partition": "A", "x": 30, "y": 60},
        {"_id": 4, "partition": "A", "x": -1, "y": 80},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=[{"$cond": [{"$gt": ["$x", 0]}, "$x", "not_a_number"]}, "$y"],
    )
    # $cond on x returns: 10, "not_a_number", 30, "not_a_number"
    # Only rows 1 and 3 have numeric first expr: pairs (10,20) and (30,60)
    # mean_x=20, mean_y=40, covSamp = ((-10)(-20)+(10)(20))/1 = (200+200)/1 = 400.0
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "y": 20, "result": 400.0},
        {"_id": 2, "partition": "A", "x": -5, "y": 40, "result": 400.0},
        {"_id": 3, "partition": "A", "x": 30, "y": 60, "result": 400.0},
        {"_id": 4, "partition": "A", "x": -1, "y": 80, "result": 400.0},
    ]
    assertSuccess(result, expected, msg="expression returning mixed types — non-numeric ignored")


# Property [Expression Returns Null]:
# Tests that null expression results are ignored in the computation.


def test_covarianceSamp_expression_returns_null_for_some(collection):
    """$covarianceSamp expression returning null for some docs, number for others."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10, "y": 20, "factor": 2},
        {"_id": 2, "partition": "A", "x": 20, "y": 40, "factor": None},
        {"_id": 3, "partition": "A", "x": 30, "y": 60, "factor": 2},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=[{"$multiply": ["$x", "$factor"]}, "$y"],
    )
    # $multiply on x: [10*2=20, 20*null=null, 30*2=60]
    # Row 2 produces null x -> ignored. Pairs: (20,20) and (60,60)
    # mean_x=40, mean_y=40, covSamp = ((-20)(-20)+(20)(20))/1 = (400+400)/1 = 800.0
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "y": 20, "factor": 2, "result": 800.0},
        {"_id": 2, "partition": "A", "x": 20, "y": 40, "factor": None, "result": 800.0},
        {"_id": 3, "partition": "A", "x": 30, "y": 60, "factor": 2, "result": 800.0},
    ]
    assertSuccess(result, expected, msg="expression returning null for some — null results ignored")


# Property [Date Value as Expression]:
# Tests that Date values in expression field are non-numeric and ignored.


def test_covarianceSamp_date_value_as_expression_ignored(collection):
    """$covarianceSamp with Date value in one expression field — non-numeric, ignored."""
    docs = [
        {"_id": 1, "partition": "A", "x": datetime(2023, 1, 1, tzinfo=timezone.utc), "y": 10},
        {"_id": 2, "partition": "A", "x": 20, "y": 40},
        {"_id": 3, "partition": "A", "x": datetime(2023, 6, 1, tzinfo=timezone.utc), "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Docs 1 and 3 have Date in x -> non-numeric -> ignored
    # Only doc 2 is valid. Single pair -> covSamp = null (N-1=0)
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "y": 10,
            "result": None,
        },
        {"_id": 2, "partition": "A", "x": 20, "y": 40, "result": None},
        {
            "_id": 3,
            "partition": "A",
            "x": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "y": 30,
            "result": None,
        },
    ]
    assertSuccess(
        result,
        expected,
        msg="Date values in expression field are non-numeric — ignored, single pair returns null",
    )


# Property [Numeric Path Component]:
# Tests that numeric path components access array elements or object keys.


def test_covarianceSamp_numeric_path_component(collection):
    """$covarianceSamp with numeric path component accesses array element or object key."""
    docs = [
        {"_id": 1, "partition": "A", "arr": [{"x": 10, "y": 20}]},
        {"_id": 2, "partition": "A", "arr": [{"x": 30, "y": 40}]},
        {"_id": 3, "partition": "A", "arr": [{"x": 50, "y": 60}]},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$arr.0.x", "$arr.0.y"],
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # In $setWindowFields context, $arr.0.x does not resolve to array element —
    # the path returns non-numeric (array) values which are ignored, resulting in null.
    expected = [
        {"_id": 1, "result": None},
        {"_id": 2, "result": None},
        {"_id": 3, "result": None},
    ]
    assertSuccess(result, expected, msg="numeric path component in window context returns null")
