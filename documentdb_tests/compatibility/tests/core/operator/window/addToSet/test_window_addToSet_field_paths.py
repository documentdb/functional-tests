"""
Tests for $addToSet with nested field paths and array traversal.

Covers dotted paths, missing intermediate paths, null-valued vs missing fields,
top-level arrays collected whole, array-of-objects traversal, and numeric path
components. $addToSet collects the resolved value of any type; a missing field
contributes nothing while an explicit null is collected. Results compared with
ignore_order_in=["result"].
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

WHOLE = {"documents": ["unbounded", "unbounded"]}


# Property [Dotted Field Path]: $addToSet resolves nested values via a dotted path.


def test_addToSet_dotted_field_path(collection):
    """$addToSet with a dotted field path collects nested document values."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"value": 10}}},
        {"_id": 2, "partition": "A", "data": {"metrics": {"value": 20}}},
        {"_id": 3, "partition": "A", "data": {"metrics": {"value": 30}}},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$data.metrics.value"
    )
    expected = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"value": 10}}, "result": [10, 20, 30]},
        {"_id": 2, "partition": "A", "data": {"metrics": {"value": 20}}, "result": [10, 20, 30]},
        {"_id": 3, "partition": "A", "data": {"metrics": {"value": 30}}, "result": [10, 20, 30]},
    ]
    assertSuccess(
        result, expected, msg="dotted field path collects nested values", ignore_order_in=["result"]
    )


# Property [Missing Intermediate Path]: a missing intermediate path contributes nothing.


def test_addToSet_missing_intermediate_path(collection):
    """$addToSet with a missing intermediate path contributes nothing for that doc."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"value": 10}}},
        {"_id": 2, "partition": "A", "data": {"other": 99}},
        {"_id": 3, "partition": "A", "data": {"metrics": {"value": 30}}},
    ]
    result = run_window_operator(
        collection, "$addToSet", docs, WHOLE, expression="$data.metrics.value"
    )
    # Doc 2 has no data.metrics.value -> contributes nothing. Set is {10, 30}.
    expected = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"value": 10}}, "result": [10, 30]},
        {"_id": 2, "partition": "A", "data": {"other": 99}, "result": [10, 30]},
        {"_id": 3, "partition": "A", "data": {"metrics": {"value": 30}}, "result": [10, 30]},
    ]
    assertSuccess(
        result,
        expected,
        msg="missing intermediate path contributes nothing",
        ignore_order_in=["result"],
    )


# Property [Null-Valued vs Missing]: an explicit null is collected; a missing field is not.


def test_addToSet_null_valued_field_collected_missing_skipped(collection):
    """$addToSet collects an explicit null but skips a missing field."""
    docs = [
        {"_id": 1, "partition": "A", "v": None},
        {"_id": 2, "partition": "A", "v": 10},
        {"_id": 3, "partition": "A"},
    ]
    result = run_window_operator(collection, "$addToSet", docs, WHOLE, expression="$v")
    # Explicit null collected once; doc 3 (missing v) contributes nothing. Set is {null, 10}.
    expected = [
        {"_id": 1, "partition": "A", "v": None, "result": [None, 10]},
        {"_id": 2, "partition": "A", "v": 10, "result": [None, 10]},
        {"_id": 3, "partition": "A", "result": [None, 10]},
    ]
    assertSuccess(
        result,
        expected,
        msg="explicit null collected, missing field skipped",
        ignore_order_in=["result"],
    )


# Property [Top-Level Array Field]: an array value is collected whole as one element.


def test_addToSet_top_level_array_collected_whole(collection):
    """$addToSet collects a top-level array value as a single element; equal arrays dedup."""
    docs = [
        {"_id": 1, "partition": "A", "v": [10, 20]},
        {"_id": 2, "partition": "A", "v": [10, 20]},
        {"_id": 3, "partition": "A", "v": 50},
    ]
    result = run_window_operator(collection, "$addToSet", docs, WHOLE, expression="$v")
    # The two [10, 20] arrays collapse; 50 is distinct. Set is {[10, 20], 50}.
    expected = [
        {"_id": 1, "partition": "A", "v": [10, 20], "result": [[10, 20], 50]},
        {"_id": 2, "partition": "A", "v": [10, 20], "result": [[10, 20], 50]},
        {"_id": 3, "partition": "A", "v": 50, "result": [[10, 20], 50]},
    ]
    assertSuccess(
        result,
        expected,
        msg="top-level array collected whole and deduped",
        ignore_order_in=["result"],
    )


# Property [Array-of-Objects Intermediate Path]: a path through an array of objects returns
# the array of matched values, collected as one element.


def test_addToSet_intermediate_array_path(collection):
    """$addToSet with a path through an array of objects collects the matched-values array."""
    docs = [
        {"_id": 1, "partition": "A", "arr": [{"field": 10}, {"field": 20}]},
        {"_id": 2, "partition": "A", "arr": [{"field": 30}, {"field": 40}]},
    ]
    result = run_window_operator(collection, "$addToSet", docs, WHOLE, expression="$arr.field")
    # "$arr.field" resolves to [10, 20] and [30, 40] respectively, each collected as one element.
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "arr": [{"field": 10}, {"field": 20}],
            "result": [[10, 20], [30, 40]],
        },
        {
            "_id": 2,
            "partition": "A",
            "arr": [{"field": 30}, {"field": 40}],
            "result": [[10, 20], [30, 40]],
        },
    ]
    assertSuccess(
        result,
        expected,
        msg="array-of-objects path collects matched-values array",
        ignore_order_in=["result"],
    )


# Property [Numeric Path Component]: a numeric path component in window context.


def test_addToSet_numeric_path_component(collection):
    """$addToSet with a numeric path component collects the (empty) resolved value."""
    docs = [
        {"_id": 1, "partition": "A", "arr": [{"field": 10}, {"field": 20}]},
        {"_id": 2, "partition": "A", "arr": [{"field": 30}, {"field": 40}]},
    ]
    result = run_window_operator(collection, "$addToSet", docs, WHOLE, expression="$arr.0.field")
    # "$arr.0.field" yields an empty array here, collected as one element and deduped across rows.
    expected = [
        {"_id": 1, "partition": "A", "arr": [{"field": 10}, {"field": 20}], "result": [[]]},
        {"_id": 2, "partition": "A", "arr": [{"field": 30}, {"field": 40}], "result": [[]]},
    ]
    assertSuccess(
        result,
        expected,
        msg="numeric path component collects empty resolved value",
        ignore_order_in=["result"],
    )
