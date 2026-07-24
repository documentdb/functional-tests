"""
Tests for $stdDevPop with special float values (NaN, Infinity, -Infinity).

Covers: Infinity as numeric participant, -Infinity, NaN values,
sliding window behavior with special floats, and non-removable window
behavior (NaN propagation).

DocumentDB behavior (consistent IEEE 754): NaN/Inf are numeric and propagate NaN
uniformly — same result regardless of window type (removable or non-removable).

The reference server has inconsistent behavior:
- Non-removable windows (unbounded, cumulative): NaN/Inf → result is NaN
- Removable/sliding windows: NaN/Inf in frame → result is null (not NaN)
- $group: NaN → result is null
This is three different answers for the same semantic question. DocumentDB's
uniform NaN propagation is the more correct IEEE 754 interpretation.
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Infinity Non-Removable Window]: Infinity in non-removable windows
# (whole partition, cumulative) produces NaN


def test_stdDevPop_positive_infinity_whole_partition(collection):
    """$stdDevPop with Infinity in non-removable whole partition window produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="Infinity is numeric; non-removable window produces NaN")


def test_stdDevPop_negative_infinity_whole_partition(collection):
    """$stdDevPop with -Infinity in non-removable whole partition window produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="-Infinity is numeric; non-removable window produces NaN"
    )


def test_stdDevPop_inf_and_neg_inf_in_same_frame(collection):
    """$stdDevPop with both Infinity and -Infinity produces NaN (Inf - Inf = NaN in variance)."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY},
        {"_id": 3, "partition": "A", "value": 10},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 10, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="Inf + -Inf in frame → NaN in variance calculation")


def test_stdDevPop_all_infinity_values(collection):
    """$stdDevPop where all values are Infinity — identical Inf: mean=Inf, Inf-Inf=NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="All identical Inf: mean=Inf, variance involves Inf-Inf=NaN"
    )


def test_stdDevPop_infinity_cumulative_window(collection):
    """$stdDevPop with Infinity in cumulative [unbounded, current] produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "current"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="Cumulative window is non-removable; Inf produces NaN throughout"
    )


def test_stdDevPop_single_infinity_value(collection):
    """$stdDevPop with single Infinity value in whole partition produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="Single Inf value: stdDevPop involves Inf arithmetic → NaN"
    )


# Property [NaN Non-Removable Window]: NaN in non-removable windows produces NaN


def test_stdDevPop_nan_value_whole_partition(collection):
    """$stdDevPop with NaN in non-removable window produces NaN (NaN is numeric, poisons)."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevPop", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_NAN, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="NaN is numeric; non-removable window produces NaN")


# Property [Special Floats Sliding Window]: special floats in removable/sliding windows return null


def test_stdDevPop_infinity_sliding_returns_null(collection):
    """$stdDevPop sliding window returns null when Infinity is in the current frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 20},
        {"_id": 4, "partition": "A", "value": 30},
        {"_id": 5, "partition": "A", "value": 40},
    ]
    result = run_window_operator(collection, "$stdDevPop", docs, {"documents": [-1, 0]})
    # Row 1: frame=[Inf]       -> null (Inf in removable window)
    # Row 2: frame=[Inf, 10]   -> null (Inf in removable window)
    # Row 3: frame=[10, 20]    -> clean -> 5.0
    # Row 4: frame=[20, 30]    -> clean -> 5.0
    # Row 5: frame=[30, 40]    -> clean -> 5.0
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": None},
        {"_id": 3, "partition": "A", "value": 20, "result": 5.0},
        {"_id": 4, "partition": "A", "value": 30, "result": 5.0},
        {"_id": 5, "partition": "A", "value": 40, "result": 5.0},
    ]
    assertSuccess(
        result, expected, msg="Sliding window: null when Inf in frame, recovers when Inf leaves"
    )


def test_stdDevPop_neg_infinity_sliding_returns_null(collection):
    """$stdDevPop sliding window returns null when -Infinity is in the current frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 20},
        {"_id": 4, "partition": "A", "value": 30},
    ]
    result = run_window_operator(collection, "$stdDevPop", docs, {"documents": [-1, 0]})
    # Row 1: frame=[-Inf]       -> null (Inf in removable window)
    # Row 2: frame=[-Inf, 10]   -> null (Inf in removable window)
    # Row 3: frame=[10, 20]     -> 5.0
    # Row 4: frame=[20, 30]     -> 5.0
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY, "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": None},
        {"_id": 3, "partition": "A", "value": 20, "result": 5.0},
        {"_id": 4, "partition": "A", "value": 30, "result": 5.0},
    ]
    assertSuccess(
        result, expected, msg="Sliding window: null when -Inf in frame, recovers when -Inf leaves"
    )


def test_stdDevPop_nan_sliding_returns_null(collection):
    """$stdDevPop sliding window returns null when NaN is in the current frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 20},
        {"_id": 4, "partition": "A", "value": 30},
    ]
    result = run_window_operator(collection, "$stdDevPop", docs, {"documents": [-1, 0]})
    # Row 1: frame=[NaN]       -> null (NaN in removable window)
    # Row 2: frame=[NaN, 10]   -> null (NaN in removable window)
    # Row 3: frame=[10, 20]    -> 5.0
    # Row 4: frame=[20, 30]    -> 5.0
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_NAN, "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": None},
        {"_id": 3, "partition": "A", "value": 20, "result": 5.0},
        {"_id": 4, "partition": "A", "value": 30, "result": 5.0},
    ]
    assertSuccessNaN(
        result, expected, msg="Sliding window: null when NaN in frame, recovers when NaN leaves"
    )


def test_stdDevPop_infinity_centered_sliding(collection):
    """$stdDevPop centered sliding window [-1, 1] with Infinity in middle returns null."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 4, "partition": "A", "value": 30},
        {"_id": 5, "partition": "A", "value": 40},
    ]
    result = run_window_operator(collection, "$stdDevPop", docs, {"documents": [-1, 1]})
    # Row 1: frame=[10, 20]         -> 5.0 (clean, edge clamp)
    # Row 2: frame=[10, 20, Inf]    -> null (Inf in removable window)
    # Row 3: frame=[20, Inf, 30]    -> null (Inf in removable window)
    # Row 4: frame=[Inf, 30, 40]    -> null (Inf in removable window)
    # Row 5: frame=[30, 40]         -> 5.0 (clean, edge clamp)
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 5.0},
        {"_id": 2, "partition": "A", "value": 20, "result": None},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY, "result": None},
        {"_id": 4, "partition": "A", "value": 30, "result": None},
        {"_id": 5, "partition": "A", "value": 40, "result": 5.0},
    ]
    assertSuccess(
        result,
        expected,
        msg="Centered sliding: null when Inf in frame, clean rows compute correctly",
    )
