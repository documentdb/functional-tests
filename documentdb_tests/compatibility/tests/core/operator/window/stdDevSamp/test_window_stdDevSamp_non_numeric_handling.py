"""
Tests for $stdDevSamp null, missing, and non-numeric value handling.

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

# Property [Null and Missing]: null and missing field values are ignored


def test_stdDevSamp_null_values_ignored(collection):
    """$stdDevSamp ignores null values in the expression field."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": None},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # numerics [10, 30] → stdDevSamp = sqrt(((10-20)^2+(30-20)^2)/1) = sqrt(200) = 14.142
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "value": None, "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "value": 30, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="null values ignored, stdDevSamp of 10,30 = 14.142")


def test_stdDevSamp_missing_field_ignored(collection):
    """$stdDevSamp ignores documents where the expression field is missing."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A"},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "value": 30, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="missing field ignored, stdDevSamp of 10,30 = 14.142")


# Property [Non-Numeric Types Ignored]: string, boolean, array, object, date,
# ObjectId, Regex, Binary values are ignored


def test_stdDevSamp_string_values_ignored(collection):
    """$stdDevSamp ignores string values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": "hello"},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "value": "hello", "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "value": 30, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="string values ignored")


def test_stdDevSamp_boolean_values_ignored(collection):
    """$stdDevSamp ignores boolean values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": True},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "value": True, "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "value": 30, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="boolean values ignored")


def test_stdDevSamp_array_values_ignored(collection):
    """$stdDevSamp ignores array values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": [1, 2, 3]},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "value": [1, 2, 3], "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "value": 30, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="array values ignored")


def test_stdDevSamp_object_values_ignored(collection):
    """$stdDevSamp ignores object/document values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": {"nested": 99}},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "value": {"nested": 99}, "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "value": 30, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="object values ignored")


def test_stdDevSamp_objectid_and_regex_and_binary_ignored(collection):
    """$stdDevSamp ignores ObjectId, Regex, and Binary values."""
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
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only numeric: [10, 30] → stdDevSamp = sqrt(200/1) = 14.142
    expected = [
        {"_id": 1, "result": 14.142135623730951},
        {"_id": 2, "result": 14.142135623730951},
        {"_id": 3, "result": 14.142135623730951},
        {"_id": 4, "result": 14.142135623730951},
        {"_id": 5, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="ObjectId/Regex/Binary values ignored")


def test_stdDevSamp_timestamp_minkey_maxkey_ignored(collection):
    """$stdDevSamp ignores Timestamp, MinKey, and MaxKey values."""
    docs = [
        {"_id": 1, "partition": "A", "value": Timestamp(1234567890, 1)},
        {"_id": 2, "partition": "A", "value": MinKey()},
        {"_id": 3, "partition": "A", "value": MaxKey()},
        {"_id": 4, "partition": "A", "value": 10},
        {"_id": 5, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection,
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only numeric: [10, 30] -> stdDevSamp = sqrt(200/1) = 14.142
    expected = [
        {"_id": 1, "result": 14.142135623730951},
        {"_id": 2, "result": 14.142135623730951},
        {"_id": 3, "result": 14.142135623730951},
        {"_id": 4, "result": 14.142135623730951},
        {"_id": 5, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="Timestamp/MinKey/MaxKey values ignored")


# Property [All Non-Numeric Returns Null]: when all values are non-numeric, result is null


def test_stdDevSamp_all_non_numeric_returns_null(collection):
    """$stdDevSamp returns null when all values in frame are non-numeric."""
    docs = [
        {"_id": 1, "partition": "A", "value": "a"},
        {"_id": 2, "partition": "A", "value": None},
        {"_id": 3, "partition": "A"},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": "a", "result": None},
        {"_id": 2, "partition": "A", "value": None, "result": None},
        {"_id": 3, "partition": "A", "result": None},
    ]
    assertSuccess(result, expected, msg="all non-numeric in frame returns null")


def test_stdDevSamp_all_non_numeric_diverse_types(collection):
    """$stdDevSamp returns null when all values are diverse non-numeric types."""
    docs = [
        {"_id": 1, "partition": "A", "value": "text"},
        {"_id": 2, "partition": "A", "value": True},
        {"_id": 3, "partition": "A", "value": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        {"_id": 4, "partition": "A", "value": [1, 2]},
        {"_id": 5, "partition": "A", "value": {"a": 1}},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
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


def test_stdDevSamp_single_numeric_in_frame_returns_null(collection):
    """$stdDevSamp returns null when only one numeric value exists in frame (N-1=0)."""
    docs = [
        {"_id": 1, "partition": "A", "value": "text"},
        {"_id": 2, "partition": "A", "value": None},
        {"_id": 3, "partition": "A", "value": 42},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # Only one numeric (42) in the whole partition → stdDevSamp = null (N-1=0)
    expected = [
        {"_id": 1, "partition": "A", "value": "text", "result": None},
        {"_id": 2, "partition": "A", "value": None, "result": None},
        {"_id": 3, "partition": "A", "value": 42, "result": None},
    ]
    assertSuccess(result, expected, msg="single numeric value → stdDevSamp = null (N-1=0)")


# Property [Mixed Types in Frame]: non-numeric values filtered per-frame, numerics participate


def test_stdDevSamp_mixed_numeric_non_numeric_sliding(collection):
    """$stdDevSamp in sliding window with mix of numeric and non-numeric values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": "skip"},
        {"_id": 3, "partition": "A", "value": 20.0},
        {"_id": 4, "partition": "A", "value": None},
        {"_id": 5, "partition": "A", "value": 30.0},
    ]
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [-2, 2]})
    # Window [-2, 2] (5-doc centered):
    # Row 1: frame [10.0, "skip", 20.0] → numerics [10, 20] → stdDevSamp = 7.071
    # Row 2: frame [10.0, "skip", 20.0, None] → numerics [10, 20] → 7.071
    # Row 3: frame [10.0, "skip", 20.0, None, 30.0] → numerics [10, 20, 30] → 10.0
    # Row 4: frame ["skip", 20.0, None, 30.0] → numerics [20, 30] → 7.071
    # Row 5: frame [20.0, None, 30.0] → numerics [20, 30] → 7.071
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": 7.0710678118654755},
        {"_id": 2, "partition": "A", "value": "skip", "result": 7.0710678118654755},
        {"_id": 3, "partition": "A", "value": 20.0, "result": 10.0},
        {"_id": 4, "partition": "A", "value": None, "result": 7.0710678118654755},
        {"_id": 5, "partition": "A", "value": 30.0, "result": 7.0710678118654755},
    ]
    assertSuccess(result, expected, msg="mixed types in sliding window — non-numeric ignored")


def test_stdDevSamp_mixed_types_in_documents(collection):
    """$stdDevSamp over documents with diverse value types — only numerics participate."""
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
    result = run_window_operator(
        collection,
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only numeric: [10, 30, 50] → mean=30, var_samp=(400+0+400)/2=400, stdDevSamp=20.0
    expected = [
        {"_id": 1, "result": 20.0},
        {"_id": 2, "result": 20.0},
        {"_id": 3, "result": 20.0},
        {"_id": 4, "result": 20.0},
        {"_id": 5, "result": 20.0},
        {"_id": 6, "result": 20.0},
        {"_id": 7, "result": 20.0},
        {"_id": 8, "result": 20.0},
        {"_id": 9, "result": 20.0},
    ]
    assertSuccess(result, expected, msg="diverse non-numeric types ignored in whole partition")


def test_stdDevSamp_mixed_types_sliding_window(collection):
    """$stdDevSamp sliding window over documents with diverse types — per-frame filtering."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": 20.0},
        {"_id": 3, "partition": "A", "value": "skip"},
        {"_id": 4, "partition": "A", "value": True},
        {"_id": 5, "partition": "A", "value": 30.0},
        {"_id": 6, "partition": "A", "value": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        {"_id": 7, "partition": "A", "value": 40.0},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # Whole partition: numerics [10, 20, 30, 40] → mean=25
    # var_samp = (225+25+25+225)/3 = 500/3 = 166.67, stdDevSamp = 12.9099...
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": 12.909944487358056},
        {"_id": 2, "partition": "A", "value": 20.0, "result": 12.909944487358056},
        {"_id": 3, "partition": "A", "value": "skip", "result": 12.909944487358056},
        {"_id": 4, "partition": "A", "value": True, "result": 12.909944487358056},
        {"_id": 5, "partition": "A", "value": 30.0, "result": 12.909944487358056},
        {
            "_id": 6,
            "partition": "A",
            "value": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "result": 12.909944487358056,
        },
        {"_id": 7, "partition": "A", "value": 40.0, "result": 12.909944487358056},
    ]
    assertSuccess(result, expected, msg="whole partition filters non-numeric types")


def test_stdDevSamp_numeric_among_diverse_types_cumulative(collection):
    """$stdDevSamp cumulative window with numerics scattered among diverse types."""
    docs = [
        {"_id": 1, "partition": "A", "value": "text"},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": datetime(2023, 6, 1, tzinfo=timezone.utc)},
        {"_id": 4, "partition": "A", "value": 20},
        {"_id": 5, "partition": "A", "value": True},
        {"_id": 6, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "current"]}
    )
    # Cumulative, only numerics count:
    # Row 1: no numeric → null
    # Row 2: [10] → null (N=1, N-1=0)
    # Row 3: [10] → null (datetime ignored, still one numeric)
    # Row 4: [10, 20] → stdDevSamp = 7.071
    # Row 5: [10, 20] → 7.071 (True ignored)
    # Row 6: [10, 20, 30] → 10.0
    expected = [
        {"_id": 1, "partition": "A", "value": "text", "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": None},
        {
            "_id": 3,
            "partition": "A",
            "value": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "result": None,
        },
        {"_id": 4, "partition": "A", "value": 20, "result": 7.0710678118654755},
        {"_id": 5, "partition": "A", "value": True, "result": 7.0710678118654755},
        {"_id": 6, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="cumulative window with numerics among diverse types")


def test_stdDevSamp_numerics_among_non_numeric_sliding(collection):
    """$stdDevSamp sliding frame filters non-numerics and computes on remaining values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": "a"},
        {"_id": 3, "partition": "A", "value": 30.0},
        {"_id": 4, "partition": "A", "value": "b"},
        {"_id": 5, "partition": "A", "value": 50.0},
    ]
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [-2, 2]})
    # Window [-2, 2] (5-doc centered):
    # Row 1: numerics [10, 30] → stdDevSamp = sqrt(200/1) = 14.142
    # Row 2: numerics [10, 30] → 14.142
    # Row 3: numerics [10, 30, 50] → sqrt(800/2) = 20.0
    # Row 4: numerics [30, 50] → sqrt(200/1) = 14.142
    # Row 5: numerics [30, 50] → 14.142
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "value": "a", "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "value": 30.0, "result": 20.0},
        {"_id": 4, "partition": "A", "value": "b", "result": 14.142135623730951},
        {"_id": 5, "partition": "A", "value": 50.0, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="non-numeric values filtered in sliding frame")
