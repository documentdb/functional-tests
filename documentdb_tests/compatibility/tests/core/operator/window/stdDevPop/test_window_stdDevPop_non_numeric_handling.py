"""
Tests for $stdDevPop null, missing, and non-numeric value handling.

Covers: null values, missing fields, strings, booleans, arrays, objects,
ObjectId, Regex, Binary, Timestamp, MinKey, MaxKey, mixed numeric and
non-numeric in same frame, and all non-numeric returns null.
"""

from datetime import datetime, timezone

from bson import Binary, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Null and Missing]: null and missing field values are ignored in stdDev computation


def test_stdDevPop_null_values_ignored(collection):
    """$stdDevPop ignores null values in the expression field."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": None},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": None, "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="null values ignored, stdDevPop of 10,30 = 10")


def test_stdDevPop_missing_field_ignored(collection):
    """$stdDevPop ignores documents where the expression field is missing."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A"},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="missing field ignored, stdDevPop of 10,30 = 10")


def test_stdDevPop_nulls_among_numerics_in_frame(collection):
    """$stdDevPop ignores nulls in frame and computes on remaining numerics."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": None},
        {"_id": 3, "partition": "A", "value": 30.0},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # Whole partition: numerics [10, 30] -> stdDevPop = 10.0 (null ignored)
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": 10.0},
        {"_id": 2, "partition": "A", "value": None, "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30.0, "result": 10.0},
    ]
    assertSuccess(
        result, expected, msg="null values ignored, stdDevPop computed on remaining numerics"
    )


# Property [Non-Numeric Types Ignored]: string, boolean, array, object, date,
# ObjectId, Regex, Binary values are ignored


def test_stdDevPop_string_values_ignored(collection):
    """$stdDevPop ignores string values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": "hello"},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": "hello", "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="string values ignored")


def test_stdDevPop_boolean_values_ignored(collection):
    """$stdDevPop ignores boolean values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": True},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": True, "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="boolean values ignored")


def test_stdDevPop_array_values_ignored(collection):
    """$stdDevPop ignores array values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": [1, 2, 3]},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": [1, 2, 3], "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="array values ignored")


def test_stdDevPop_object_values_ignored(collection):
    """$stdDevPop ignores object/document values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": {"nested": 99}},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": {"nested": 99}, "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="object values ignored")


def test_stdDevPop_objectid_and_regex_and_binary_ignored(collection):
    """$stdDevPop ignores ObjectId, Regex, and Binary values."""
    oid = ObjectId("507f1f77bcf86cd799439011")
    docs = [
        {"_id": 1, "partition": "A", "value": oid},
        {"_id": 2, "partition": "A", "value": Regex("^test", "i")},
        {"_id": 3, "partition": "A", "value": Binary(b"\x01\x02\x03")},
        {"_id": 4, "partition": "A", "value": 10},
        {"_id": 5, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection,
        "$stdDevPop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only numeric: [10, 30] -> stdDevPop = 10.0
    expected = [
        {"_id": 1, "result": 10.0},
        {"_id": 2, "result": 10.0},
        {"_id": 3, "result": 10.0},
        {"_id": 4, "result": 10.0},
        {"_id": 5, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="ObjectId/Regex/Binary values ignored")


def test_stdDevPop_timestamp_minkey_maxkey_ignored(collection):
    """$stdDevPop ignores Timestamp, MinKey, and MaxKey values."""
    docs = [
        {"_id": 1, "partition": "A", "value": Timestamp(1234567890, 1)},
        {"_id": 2, "partition": "A", "value": MinKey()},
        {"_id": 3, "partition": "A", "value": MaxKey()},
        {"_id": 4, "partition": "A", "value": 10},
        {"_id": 5, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection,
        "$stdDevPop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only numeric: [10, 30] -> stdDevPop = 10.0
    expected = [
        {"_id": 1, "result": 10.0},
        {"_id": 2, "result": 10.0},
        {"_id": 3, "result": 10.0},
        {"_id": 4, "result": 10.0},
        {"_id": 5, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="Timestamp/MinKey/MaxKey values ignored")


# Property [All Non-Numeric Returns Null]: when all values are non-numeric, result is null


def test_stdDevPop_all_non_numeric_returns_null(collection):
    """$stdDevPop returns null when all values in frame are non-numeric."""
    docs = [
        {"_id": 1, "partition": "A", "value": "a"},
        {"_id": 2, "partition": "A", "value": None},
        {"_id": 3, "partition": "A"},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": "a", "result": None},
        {"_id": 2, "partition": "A", "value": None, "result": None},
        {"_id": 3, "partition": "A", "result": None},
    ]
    assertSuccess(result, expected, msg="all non-numeric in frame returns null")


def test_stdDevPop_all_non_numeric_diverse_types(collection):
    """$stdDevPop returns null when all values are diverse non-numeric types."""
    docs = [
        {"_id": 1, "partition": "A", "value": "text"},
        {"_id": 2, "partition": "A", "value": True},
        {"_id": 3, "partition": "A", "value": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        {"_id": 4, "partition": "A", "value": [1, 2]},
        {"_id": 5, "partition": "A", "value": {"a": 1}},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # No numeric values -> null
    expected = [
        {"_id": 1, "partition": "A", "value": "text", "result": None},
        {"_id": 2, "partition": "A", "value": True, "result": None},
        {
            "_id": 3,
            "partition": "A",
            "value": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "result": None,
        },
        {"_id": 4, "partition": "A", "value": [1, 2], "result": None},
        {"_id": 5, "partition": "A", "value": {"a": 1}, "result": None},
    ]
    assertSuccess(result, expected, msg="all diverse non-numeric types return null")


# Property [Mixed Types in Frame]: non-numeric values filtered per-frame, numerics participate


def test_stdDevPop_mixed_numeric_non_numeric_sliding(collection):
    """$stdDevPop in sliding window with mix of numeric and non-numeric values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": "skip"},
        {"_id": 3, "partition": "A", "value": 20.0},
        {"_id": 4, "partition": "A", "value": None},
        {"_id": 5, "partition": "A", "value": 30.0},
    ]
    result = run_window_operator(collection, "$stdDevPop", docs, {"documents": [-2, 2]})
    # Window [-2, 2] (5-doc centered):
    # Row 1: frame [10.0, "skip", 20.0] -> numerics [10, 20] -> stdDevPop = 5.0
    # Row 2: frame [10.0, "skip", 20.0, None] -> numerics [10, 20] -> 5.0
    # Row 3: frame [10.0, "skip", 20.0, None, 30.0] -> numerics [10, 20, 30] -> 8.165
    # Row 4: frame ["skip", 20.0, None, 30.0] -> numerics [20, 30] -> 5.0
    # Row 5: frame [20.0, None, 30.0] -> numerics [20, 30] -> 5.0
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": 5.0},
        {"_id": 2, "partition": "A", "value": "skip", "result": 5.0},
        {"_id": 3, "partition": "A", "value": 20.0, "result": 8.16496580927726},
        {"_id": 4, "partition": "A", "value": None, "result": 5.0},
        {"_id": 5, "partition": "A", "value": 30.0, "result": 5.0},
    ]
    assertSuccess(result, expected, msg="mixed types in sliding window — non-numeric ignored")


def test_stdDevPop_mixed_types_in_documents(collection):
    """$stdDevPop over documents with diverse value types — only numerics participate."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": "hello"},
        {"_id": 3, "partition": "A", "value": True},
        {"_id": 4, "partition": "A", "value": datetime(2023, 6, 1, tzinfo=timezone.utc)},
        {"_id": 5, "partition": "A", "value": 30},
        {"_id": 6, "partition": "A", "value": None},
        {"_id": 7, "partition": "A", "value": [1, 2, 3]},
        {"_id": 8, "partition": "A", "value": {"nested": 99}},
        {"_id": 9, "partition": "A", "value": 50},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevPop": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "result": 1}},
            ],
            "cursor": {},
        },
    )
    # Only numeric: [10, 30, 50] -> mean=30, variance=(400+0+400)/3=266.67, stddev=16.33
    expected = [
        {"_id": 1, "result": 16.32993161855452},
        {"_id": 2, "result": 16.32993161855452},
        {"_id": 3, "result": 16.32993161855452},
        {"_id": 4, "result": 16.32993161855452},
        {"_id": 5, "result": 16.32993161855452},
        {"_id": 6, "result": 16.32993161855452},
        {"_id": 7, "result": 16.32993161855452},
        {"_id": 8, "result": 16.32993161855452},
        {"_id": 9, "result": 16.32993161855452},
    ]
    assertSuccess(result, expected, msg="diverse non-numeric types ignored in whole partition")


def test_stdDevPop_mixed_types_sliding_window(collection):
    """$stdDevPop sliding window over documents with diverse types — per-frame filtering."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": 20.0},
        {"_id": 3, "partition": "A", "value": "skip"},
        {"_id": 4, "partition": "A", "value": True},
        {"_id": 5, "partition": "A", "value": 30.0},
        {"_id": 6, "partition": "A", "value": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        {"_id": 7, "partition": "A", "value": 40.0},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevPop": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Whole partition: numerics [10, 20, 30, 40] -> stdDevPop = 11.180339887498949
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": 11.180339887498949},
        {"_id": 2, "partition": "A", "value": 20.0, "result": 11.180339887498949},
        {"_id": 3, "partition": "A", "value": "skip", "result": 11.180339887498949},
        {"_id": 4, "partition": "A", "value": True, "result": 11.180339887498949},
        {"_id": 5, "partition": "A", "value": 30.0, "result": 11.180339887498949},
        {
            "_id": 6,
            "partition": "A",
            "value": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "result": 11.180339887498949,
        },
        {"_id": 7, "partition": "A", "value": 40.0, "result": 11.180339887498949},
    ]
    assertSuccess(result, expected, msg="sliding window filters non-numeric types per frame")


def test_stdDevPop_numeric_among_diverse_types_cumulative(collection):
    """$stdDevPop cumulative window with numerics scattered among diverse types."""
    docs = [
        {"_id": 1, "partition": "A", "value": "text"},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": datetime(2023, 6, 1, tzinfo=timezone.utc)},
        {"_id": 4, "partition": "A", "value": 20},
        {"_id": 5, "partition": "A", "value": True},
        {"_id": 6, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "current"]}
    )
    # Cumulative, only numerics count:
    # Row 1: no numeric -> null
    # Row 2: [10] -> 0
    # Row 3: [10] -> 0 (datetime ignored)
    # Row 4: [10, 20] -> 5.0
    # Row 5: [10, 20] -> 5.0 (True ignored)
    # Row 6: [10, 20, 30] -> 8.165
    expected = [
        {"_id": 1, "partition": "A", "value": "text", "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": 0.0},
        {
            "_id": 3,
            "partition": "A",
            "value": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "result": 0.0,
        },
        {"_id": 4, "partition": "A", "value": 20, "result": 5.0},
        {"_id": 5, "partition": "A", "value": True, "result": 5.0},
        {"_id": 6, "partition": "A", "value": 30, "result": 8.16496580927726},
    ]
    assertSuccess(result, expected, msg="cumulative window with numerics among diverse types")


def test_stdDevPop_numerics_among_non_numeric_sliding(collection):
    """$stdDevPop sliding frame filters non-numerics and computes on remaining values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": "a"},
        {"_id": 3, "partition": "A", "value": 30.0},
        {"_id": 4, "partition": "A", "value": "b"},
        {"_id": 5, "partition": "A", "value": 50.0},
    ]
    result = run_window_operator(collection, "$stdDevPop", docs, {"documents": [-2, 2]})
    # Window [-2, 2] (5-doc centered):
    # Row 1: [10.0, "a", 30.0] -> numerics [10, 30] -> stdDevPop = 10.0
    # Row 2: [10.0, "a", 30.0, "b"] -> numerics [10, 30] -> 10.0
    # Row 3: [10.0, "a", 30.0, "b", 50.0] -> numerics [10, 30, 50] -> 16.3299...
    # Row 4: ["a", 30.0, "b", 50.0] -> numerics [30, 50] -> 10.0
    # Row 5: [30.0, "b", 50.0] -> numerics [30, 50] -> 10.0
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": 10.0},
        {"_id": 2, "partition": "A", "value": "a", "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30.0, "result": 16.32993161855452},
        {"_id": 4, "partition": "A", "value": "b", "result": 10.0},
        {"_id": 5, "partition": "A", "value": 50.0, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="non-numeric values filtered in sliding frame")
