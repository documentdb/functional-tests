"""
Tests for $covariancePop null, missing, and non-numeric value handling.

Covers: null values, missing fields, strings, booleans, arrays, objects,
ObjectId, Regex, Binary, Timestamp, MinKey, MaxKey, mixed numeric and
non-numeric in same frame, and all non-numeric returns null.

$covariancePop semantics: when either expression in ["$x", "$y"] evaluates to
a non-numeric, null, or missing value for a document, that entire row (pair)
is ignored in the covariance computation.
"""

from datetime import datetime, timezone

from bson import Binary, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

# Property [Null and Missing]: null and missing field values cause the row to be ignored


def test_covariancePop_null_in_x_ignored(collection):
    """$covariancePop ignores rows where x expression is null."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": None, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has null x -> ignored. Pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covPop = ((-1)(-2)+(1)(2))/2 = 4/2 = 2.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": None, "y": 4, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="null x values ignored, covPop of (1,2),(3,6) = 2.0")


def test_covariancePop_null_in_y_ignored(collection):
    """$covariancePop ignores rows where y expression is null."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has null y -> ignored. Pairs: (1,2) and (3,6)
    # mean_x=2, mean_y=4, covPop = 2.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": 2, "y": None, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="null y values ignored")


def test_covariancePop_missing_x_field_ignored(collection):
    """$covariancePop ignores documents where the x field is missing."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "y": 4},  # x missing
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has missing x -> ignored. Pairs: (1,2) and (3,6) -> covPop = 2.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "y": 4, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="missing x field ignored")


def test_covariancePop_missing_y_field_ignored(collection):
    """$covariancePop ignores documents where the y field is missing."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2},  # y missing
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Row 2 has missing y -> ignored. Pairs: (1,2) and (3,6) -> covPop = 2.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": 2, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="missing y field ignored")


def test_covariancePop_both_null_ignored(collection):
    """$covariancePop ignores rows where both x and y are null."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": None, "y": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": None, "y": None, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="both null values -> row ignored")


# Property [Non-Numeric Types Ignored]: string, boolean, array, object, date,
# ObjectId, Regex, Binary values are ignored


def test_covariancePop_string_in_x_ignored(collection):
    """$covariancePop ignores rows where x is a string."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": "hello", "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": "hello", "y": 4, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="string x values ignored")


def test_covariancePop_string_in_y_ignored(collection):
    """$covariancePop ignores rows where y is a string."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": "world"},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": 2, "y": "world", "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="string y values ignored")


def test_covariancePop_boolean_values_ignored(collection):
    """$covariancePop ignores rows where x or y is boolean."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": True, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": False},
        {"_id": 4, "partition": "A", "x": 4, "y": 8},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Rows 2 and 3 ignored. Valid pairs: (1,2) and (4,8)
    # mean_x=2.5, mean_y=5, covPop = ((-1.5)(-3)+(1.5)(3))/2 = (4.5+4.5)/2 = 4.5
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.5},
        {"_id": 2, "partition": "A", "x": True, "y": 4, "result": 4.5},
        {"_id": 3, "partition": "A", "x": 3, "y": False, "result": 4.5},
        {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 4.5},
    ]
    assertSuccess(result, expected, msg="boolean values ignored in both positions")


def test_covariancePop_array_values_ignored(collection):
    """$covariancePop ignores rows where x or y is an array."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": [1, 2, 3], "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": [1, 2, 3], "y": 4, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="array values ignored")


def test_covariancePop_object_values_ignored(collection):
    """$covariancePop ignores rows where x or y is an object/document."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": {"nested": 99}, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 2.0},
        {"_id": 2, "partition": "A", "x": {"nested": 99}, "y": 4, "result": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="object values ignored")


def test_covariancePop_objectid_and_regex_and_binary_ignored(collection):
    """$covariancePop ignores ObjectId, Regex, and Binary values."""
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
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only rows 4 and 5 valid: (4,8) and (6,12)
    # mean_x=5, mean_y=10, covPop = ((-1)(-2)+(1)(2))/2 = 4/2 = 2.0
    expected = [
        {"_id": 1, "result": 2.0},
        {"_id": 2, "result": 2.0},
        {"_id": 3, "result": 2.0},
        {"_id": 4, "result": 2.0},
        {"_id": 5, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="ObjectId/Regex/Binary values ignored")


def test_covariancePop_timestamp_minkey_maxkey_ignored(collection):
    """$covariancePop ignores Timestamp, MinKey, and MaxKey values."""
    docs = [
        {"_id": 1, "partition": "A", "x": Timestamp(1234567890, 1), "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": MinKey()},
        {"_id": 3, "partition": "A", "x": MaxKey(), "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 8},
        {"_id": 5, "partition": "A", "x": 6, "y": 12},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
        extra_stages=[{"$project": {"_id": 1, "result": 1}}],
    )
    # Only rows 4 and 5 valid: (4,8) and (6,12) -> covPop = 2.0
    expected = [
        {"_id": 1, "result": 2.0},
        {"_id": 2, "result": 2.0},
        {"_id": 3, "result": 2.0},
        {"_id": 4, "result": 2.0},
        {"_id": 5, "result": 2.0},
    ]
    assertSuccess(result, expected, msg="Timestamp/MinKey/MaxKey values ignored")


# Property [All Non-Numeric Returns Null]: when all values are non-numeric, result is null


def test_covariancePop_all_non_numeric_returns_null(collection):
    """$covariancePop returns null when all values in frame are non-numeric."""
    docs = [
        {"_id": 1, "partition": "A", "x": "a", "y": 2},
        {"_id": 2, "partition": "A", "x": None, "y": 4},
        {"_id": 3, "partition": "A", "y": 6},  # x missing
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
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


def test_covariancePop_all_non_numeric_diverse_types(collection):
    """$covariancePop returns null when all values are diverse non-numeric types."""
    docs = [
        {"_id": 1, "partition": "A", "x": "text", "y": 10},
        {"_id": 2, "partition": "A", "x": True, "y": 20},
        {"_id": 3, "partition": "A", "x": datetime(2023, 1, 1, tzinfo=timezone.utc), "y": 30},
        {"_id": 4, "partition": "A", "x": [1, 2], "y": 40},
        {"_id": 5, "partition": "A", "x": {"a": 1}, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
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


# Property [Mixed Types in Frame]: non-numeric values filtered per-frame, numerics participate


def test_covariancePop_mixed_numeric_non_numeric_sliding(collection):
    """$covariancePop in sliding window with mix of numeric and non-numeric values."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10},
        {"_id": 2, "partition": "A", "x": "skip", "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": None, "y": 40},
        {"_id": 5, "partition": "A", "x": 5, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-2, 2]},
        expression=["$x", "$y"],
    )
    # Window [-2, 2] (5-doc centered):
    # Row 1: frame docs 1-3, valid pairs: (1,10),(3,30) -> mean_x=2,mean_y=20
    #   covPop = ((-1)(-10)+(1)(10))/2 = 20/2 = 10.0
    # Row 2: frame docs 1-4, valid pairs: (1,10),(3,30) -> covPop = 10.0
    # Row 3: frame docs 1-5, valid pairs: (1,10),(3,30),(5,50) -> mean_x=3,mean_y=30
    #   covPop = ((-2)(-20)+(0)(0)+(2)(20))/3 = (40+0+40)/3 = 80/3 = 26.6667
    # Row 4: frame docs 2-5, valid pairs: (3,30),(5,50) -> mean_x=4,mean_y=40
    #   covPop = ((-1)(-10)+(1)(10))/2 = 10.0
    # Row 5: frame docs 3-5, valid pairs: (3,30),(5,50) -> covPop = 10.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "x": "skip", "y": 20, "result": 10.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 26.666666666666668},
        {"_id": 4, "partition": "A", "x": None, "y": 40, "result": 10.0},
        {"_id": 5, "partition": "A", "x": 5, "y": 50, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="mixed types in sliding window — non-numeric ignored")


def test_covariancePop_numeric_among_diverse_types_cumulative(collection):
    """$covariancePop cumulative window with numerics scattered among diverse types."""
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
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "current"]},
        expression=["$x", "$y"],
    )
    # Cumulative, only numeric x and numeric y pairs count:
    # Row 1: no valid pair -> null
    # Row 2: [(1,2)] -> single pair -> 0
    # Row 3: [(1,2)] -> datetime x ignored, still single pair -> 0
    # Row 4: [(1,2),(3,6)] -> mean_x=2, mean_y=4, covPop = ((-1)(-2)+(1)(2))/2 = 2.0
    # Row 5: [(1,2),(3,6)] -> True ignored, still 2 pairs -> 2.0
    # Row 6: [(1,2),(3,6),(5,10)] -> mean_x=3, mean_y=6
    #   covPop = ((-2)(-4)+(0)(0)+(2)(4))/3 = 16/3 = 5.3333...
    expected = [
        {"_id": 1, "partition": "A", "x": "text", "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 1, "y": 2, "result": 0.0},
        {
            "_id": 3,
            "partition": "A",
            "x": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "y": 4,
            "result": 0.0,
        },
        {"_id": 4, "partition": "A", "x": 3, "y": 6, "result": 2.0},
        {"_id": 5, "partition": "A", "x": True, "y": 8, "result": 2.0},
        {"_id": 6, "partition": "A", "x": 5, "y": 10, "result": 5.333333333333333},
    ]
    assertSuccess(result, expected, msg="cumulative window with numerics among diverse types")
