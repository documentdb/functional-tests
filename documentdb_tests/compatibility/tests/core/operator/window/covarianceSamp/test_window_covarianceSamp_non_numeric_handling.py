"""
Tests for $covarianceSamp null, missing, and non-numeric value handling.

Covers: null values, missing fields, strings, booleans, arrays, objects,
ObjectId, Regex, Binary, Timestamp, MinKey, MaxKey, mixed numeric and
non-numeric in same frame, and all non-numeric returns null.

$covarianceSamp semantics: when either expression in ["$x", "$y"] evaluates to
a non-numeric, null, or missing value for a document, that entire row (pair)
is ignored in the covariance computation. Additionally, when only one valid
numeric pair exists in the frame, $covarianceSamp returns null (N-1=0).
"""

from datetime import datetime, timezone

from bson import Binary, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

# Property [Null and Missing]: null and missing field values cause the row to be ignored


def test_covarianceSamp_null_in_x_ignored(collection):
    """$covarianceSamp ignores rows where x expression is null."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": None, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has null x -> ignored. Pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covSamp = ((-1)(-2)+(1)(2))/1 = 4/1 = 4.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": None, "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="null x values ignored, covSamp of (1,2),(3,6) = 4.0")


def test_covarianceSamp_null_in_y_ignored(collection):
    """$covarianceSamp ignores rows where y expression is null."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has null y -> ignored. Pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covSamp = 4.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": 2, "y": None, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="null y values ignored")


def test_covarianceSamp_missing_x_field_ignored(collection):
    """$covarianceSamp ignores documents where the x field is missing."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "y": 4},  # x missing
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has missing x -> ignored. Pairs: (1,2) and (3,6) -> covSamp = 4.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="missing x field ignored")


def test_covarianceSamp_missing_y_field_ignored(collection):
    """$covarianceSamp ignores documents where the y field is missing."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2},  # y missing
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has missing y -> ignored. Pairs: (1,2) and (3,6) -> covSamp = 4.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": 2, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="missing y field ignored")


def test_covarianceSamp_both_null_ignored(collection):
    """$covarianceSamp ignores rows where both x and y are null."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": None, "y": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": None, "y": None, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="both null values -> row ignored")


# Property [Non-Numeric Types Ignored]: string, boolean, array, object, date,
# ObjectId, Regex, Binary values are ignored


def test_covarianceSamp_string_in_x_ignored(collection):
    """$covarianceSamp ignores rows where x is a string."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": "hello", "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": "hello", "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="string x values ignored")


def test_covarianceSamp_string_in_y_ignored(collection):
    """$covarianceSamp ignores rows where y is a string."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": "world"},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": 2, "y": "world", "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="string y values ignored")


def test_covarianceSamp_boolean_values_ignored(collection):
    """$covarianceSamp ignores rows where x or y is boolean."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": True, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": False},
        {"_id": 4, "partition": "A", "x": 4, "y": 8},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Rows 2 and 3 ignored. Valid pairs: (1,2) and (4,8)
    # mean_x=2.5, mean_y=5, covSamp = ((-1.5)(-3)+(1.5)(3))/1 = (4.5+4.5)/1 = 9.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 9.0},
        {"_id": 2, "partition": "A", "x": True, "y": 4, "result": 9.0},
        {"_id": 3, "partition": "A", "x": 3, "y": False, "result": 9.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 9.0},
    ]
    assertSuccess(result, expected, msg="boolean values ignored in both positions")


def test_covarianceSamp_array_values_ignored(collection):
    """$covarianceSamp ignores rows where x or y is an array."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": [1, 2, 3], "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": [1, 2, 3], "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="array values ignored")


def test_covarianceSamp_object_values_ignored(collection):
    """$covarianceSamp ignores rows where x or y is an object/document."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": {"nested": 99}, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": {"nested": 99}, "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="object values ignored")


def test_covarianceSamp_objectid_and_regex_and_binary_ignored(collection):
    """$covarianceSamp ignores ObjectId, Regex, and Binary values."""
    oid = ObjectId("507f1f77bcf86cd799439011")
    docs = [
        {"_id": 1, "partition": "A", "x": oid, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": Regex("^test", "i")},
        {"_id": 3, "partition": "A", "x": Binary(b"\x01\x02\x03"), "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 8},
        {"_id": 5, "partition": "A", "x": 6, "y": 12},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only rows 4 and 5 valid: (4,8) and (6,12)
    # mean_x=5, mean_y=10, covSamp = ((-1)(-2)+(1)(2))/1 = 4/1 = 4.0
    expected = [
        {"_id": 1, "result": 4.0},
        {"_id": 2, "result": 4.0},
        {"_id": 3, "result": 4.0},
        {"_id": 4, "result": 4.0},
        {"_id": 5, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="ObjectId/Regex/Binary values ignored")


def test_covarianceSamp_timestamp_minkey_maxkey_ignored(collection):
    """$covarianceSamp ignores Timestamp, MinKey, and MaxKey values."""
    docs = [
        {"_id": 1, "partition": "A", "x": Timestamp(1234567890, 1), "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": MinKey()},
        {"_id": 3, "partition": "A", "x": MaxKey(), "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 8},
        {"_id": 5, "partition": "A", "x": 6, "y": 12},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only rows 4 and 5 valid: (4,8) and (6,12) -> covSamp = 4.0
    expected = [
        {"_id": 1, "result": 4.0},
        {"_id": 2, "result": 4.0},
        {"_id": 3, "result": 4.0},
        {"_id": 4, "result": 4.0},
        {"_id": 5, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="Timestamp/MinKey/MaxKey values ignored")


# Property [All Non-Numeric Returns Null]: when all values are non-numeric, result is null


def test_covarianceSamp_all_non_numeric_returns_null(collection):
    """$covarianceSamp returns null when all values in frame are non-numeric."""
    docs = [
        {"_id": 1, "partition": "A", "x": "a", "y": 2},
        {"_id": 2, "partition": "A", "x": None, "y": 4},
        {"_id": 3, "partition": "A", "y": 6},  # x missing
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": "a", "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": None, "y": 4, "result": None},
        {"_id": 3, "partition": "A", "y": 6, "result": None},
    ]
    assertSuccess(result, expected, msg="all non-numeric x values in frame returns null")


def test_covarianceSamp_all_non_numeric_diverse_types(collection):
    """$covarianceSamp returns null when all values are diverse non-numeric types."""
    docs = [
        {"_id": 1, "partition": "A", "x": "text", "y": 10},
        {"_id": 2, "partition": "A", "x": True, "y": 20},
        {"_id": 3, "partition": "A", "x": datetime(2023, 1, 1, tzinfo=timezone.utc), "y": 30},
        {"_id": 4, "partition": "A", "x": [1, 2], "y": 40},
        {"_id": 5, "partition": "A", "x": {"a": 1}, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # No valid numeric x values -> null
    expected = [
        {"_id": 1, "partition": "A", "x": "text", "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": True, "y": 20, "result": None},
        {
            "_id": 3,
            "partition": "A",
            "x": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "y": 30,
            "result": None,
        },
        {"_id": 4, "partition": "A", "x": [1, 2], "y": 40, "result": None},
        {"_id": 5, "partition": "A", "x": {"a": 1}, "y": 50, "result": None},
    ]
    assertSuccess(result, expected, msg="all diverse non-numeric types return null")


# Property [Single Valid Pair Returns Null]: when only one numeric pair exists, covSamp = null


def test_covarianceSamp_single_valid_pair_returns_null(collection):
    """$covarianceSamp returns null when only one valid numeric pair exists (N-1=0)."""
    docs = [
        {"_id": 1, "partition": "A", "x": "a", "y": 2},
        {"_id": 2, "partition": "A", "x": 5, "y": 10},
        {"_id": 3, "partition": "A", "x": None, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Only 1 valid numeric pair (5,10) -> N=1 -> covSamp = null
    expected = [
        {"_id": 1, "partition": "A", "x": "a", "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 5, "y": 10, "result": None},
        {"_id": 3, "partition": "A", "x": None, "y": 6, "result": None},
    ]
    assertSuccess(result, expected, msg="single valid numeric pair -> covSamp = null (N-1=0)")


# Property [Mixed Types in Frame]: non-numeric values filtered per-frame, numerics participate


def test_covarianceSamp_mixed_numeric_non_numeric_sliding(collection):
    """$covarianceSamp in sliding window with mix of numeric and non-numeric values."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10},
        {"_id": 2, "partition": "A", "x": "skip", "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": None, "y": 40},
        {"_id": 5, "partition": "A", "x": 5, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": [-2, 2]},
        expression=["$x", "$y"],
    )
    # Window [-2, 2] (5-doc centered):
    # Row 1: frame docs 1-3, valid pairs: (1,10),(3,30) -> mean_x=2,mean_y=20
    #   covSamp = ((-1)(-10)+(1)(10))/1 = 20/1 = 20.0
    # Row 2: frame docs 1-4, valid pairs: (1,10),(3,30) -> covSamp = 20.0
    # Row 3: frame docs 1-5, valid pairs: (1,10),(3,30),(5,50) -> mean_x=3,mean_y=30
    #   covSamp = ((-2)(-20)+(0)(0)+(2)(20))/2 = (40+0+40)/2 = 80/2 = 40.0
    # Row 4: frame docs 2-5, valid pairs: (3,30),(5,50) -> mean_x=4,mean_y=40
    #   covSamp = ((-1)(-10)+(1)(10))/1 = 20.0
    # Row 5: frame docs 3-5, valid pairs: (3,30),(5,50) -> covSamp = 20.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10, "result": 20.0},
        {"_id": 2, "partition": "A", "x": "skip", "y": 20, "result": 20.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 40.0},
        {"_id": 4, "partition": "A", "x": None, "y": 40, "result": 20.0},
        {"_id": 5, "partition": "A", "x": 5, "y": 50, "result": 20.0},
    ]
    assertSuccess(result, expected, msg="mixed types in sliding window — non-numeric ignored")


def test_covarianceSamp_numeric_among_diverse_types_cumulative(collection):
    """$covarianceSamp cumulative window with numerics scattered among diverse types."""
    docs = [
        {"_id": 1, "partition": "A", "x": "text", "y": 2},
        {"_id": 2, "partition": "A", "x": 1, "y": 2},
        {"_id": 3, "partition": "A", "x": datetime(2023, 6, 1, tzinfo=timezone.utc), "y": 4},
        {"_id": 4, "partition": "A", "x": 3, "y": 6},
        {"_id": 5, "partition": "A", "x": True, "y": 8},
        {"_id": 6, "partition": "A", "x": 5, "y": 10},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "current"]},
        expression=["$x", "$y"],
    )
    # Cumulative, only numeric x and numeric y pairs count:
    # Row 1: no valid pair -> null
    # Row 2: [(1,2)] -> single pair -> null (N-1=0)
    # Row 3: [(1,2)] -> datetime x ignored, still single pair -> null
    # Row 4: [(1,2),(3,6)] -> mean_x=2, mean_y=4, covSamp = ((-1)(-2)+(1)(2))/1 = 4.0
    # Row 5: [(1,2),(3,6)] -> True ignored, still 2 pairs -> 4.0
    # Row 6: [(1,2),(3,6),(5,10)] -> mean_x=3, mean_y=6
    #   covSamp = ((-2)(-4)+(0)(0)+(2)(4))/2 = 16/2 = 8.0
    expected = [
        {"_id": 1, "partition": "A", "x": "text", "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 1, "y": 2, "result": None},
        {
            "_id": 3,
            "partition": "A",
            "x": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "y": 4,
            "result": None,
        },
        {"_id": 4, "partition": "A", "x": 3, "y": 6, "result": 4.0},
        {"_id": 5, "partition": "A", "x": True, "y": 8, "result": 4.0},
        {"_id": 6, "partition": "A", "x": 5, "y": 10, "result": 8.0},
    ]
    assertSuccess(result, expected, msg="cumulative window with numerics among diverse types")
