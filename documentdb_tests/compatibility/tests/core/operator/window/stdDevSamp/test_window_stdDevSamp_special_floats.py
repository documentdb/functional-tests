"""
Tests for $stdDevSamp with special float values (NaN, Infinity, -Infinity).

Covers: Infinity as numeric participant, -Infinity, NaN values,
sliding window behavior with special floats, and non-removable window
behavior (NaN propagation).

Key difference from $stdDevPop: single element in frame → null (N-1=0, undefined),
whereas $stdDevPop single element → NaN when value is Inf (due to Inf arithmetic)
or 0 for finite values. For frames with 2+ elements, NaN/Inf poisoning behavior
is identical to $stdDevPop.

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

# Property [Infinity Non-Removable Window]: Infinity in non-removable windows produces NaN


def test_stdDevSamp_positive_infinity_whole_partition(collection):
    """$stdDevSamp with Infinity in non-removable whole partition window produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="Infinity is numeric; non-removable window produces NaN")


def test_stdDevSamp_negative_infinity_whole_partition(collection):
    """$stdDevSamp with -Infinity in non-removable whole partition window produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="-Infinity is numeric; non-removable window produces NaN"
    )


def test_stdDevSamp_inf_and_neg_inf_in_same_frame(collection):
    """$stdDevSamp with both Infinity and -Infinity produces NaN (Inf - Inf = NaN in variance)."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY},
        {"_id": 3, "partition": "A", "value": 10},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 10, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="Inf + -Inf in frame → NaN in variance calculation")


def test_stdDevSamp_all_infinity_values(collection):
    """$stdDevSamp where all values are Infinity — identical Inf: mean=Inf, Inf-Inf=NaN."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="All identical Inf: mean=Inf, variance involves Inf-Inf=NaN"
    )


def test_stdDevSamp_infinity_cumulative_window(collection):
    """$stdDevSamp with Infinity in cumulative [unbounded, current] — row 1 is null (single
    element)."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "current"]}
    )
    # Row 1: frame=[Inf]        -> null (single element, N-1=0, undefined)
    # Row 2: frame=[Inf, 10]    -> NaN (Inf poisons)
    # Row 3: frame=[Inf, 10, 30] -> NaN (Inf poisons)
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result,
        expected,
        msg="Cumulative window: row 1 null (single element), rows 2-3 NaN (Inf poisons)",
    )


def test_stdDevSamp_single_infinity_value(collection):
    """$stdDevSamp with single Infinity value in whole partition.

    Returns null (single element, N-1=0).
    """
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": None},
    ]
    assertSuccess(
        result,
        expected,
        msg="Single Inf value: stdDevSamp with N=1 returns null (N-1=0, undefined)",
    )


# Property [NaN Non-Removable Window]: NaN in non-removable windows produces NaN


def test_stdDevSamp_nan_value_whole_partition(collection):
    """$stdDevSamp with NaN in non-removable window produces NaN (NaN is numeric, poisons)."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": FLOAT_NAN, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="NaN is numeric; non-removable window produces NaN")


# Property [Special Floats Sliding Window]: special floats in removable/sliding windows return null


def test_stdDevSamp_infinity_sliding_returns_null(collection):
    """$stdDevSamp sliding window returns null when Infinity is in the current frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 20},
        {"_id": 4, "partition": "A", "value": 30},
        {"_id": 5, "partition": "A", "value": 40},
    ]
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [-1, 0]})
    # Row 1: frame=[Inf]       -> null (single element, N-1=0)
    # Row 2: frame=[Inf, 10]   -> null (Inf in removable window)
    # Row 3: frame=[10, 20]    -> sqrt(50) = 7.0710678118654755
    # Row 4: frame=[20, 30]    -> sqrt(50) = 7.0710678118654755
    # Row 5: frame=[30, 40]    -> sqrt(50) = 7.0710678118654755
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_INFINITY, "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": None},
        {"_id": 3, "partition": "A", "value": 20, "result": 7.0710678118654755},
        {"_id": 4, "partition": "A", "value": 30, "result": 7.0710678118654755},
        {"_id": 5, "partition": "A", "value": 40, "result": 7.0710678118654755},
    ]
    assertSuccess(
        result,
        expected,
        msg="Sliding window: null for single element and when Inf in frame,"
        " recovers when Inf leaves",
    )


def test_stdDevSamp_neg_infinity_sliding_returns_null(collection):
    """$stdDevSamp sliding window returns null when -Infinity is in the current frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 20},
        {"_id": 4, "partition": "A", "value": 30},
    ]
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [-1, 0]})
    # Row 1: frame=[-Inf]       -> null (single element, N-1=0)
    # Row 2: frame=[-Inf, 10]   -> null (-Inf in removable window)
    # Row 3: frame=[10, 20]     -> sqrt(50) = 7.0710678118654755
    # Row 4: frame=[20, 30]     -> sqrt(50) = 7.0710678118654755
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_NEGATIVE_INFINITY, "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": None},
        {"_id": 3, "partition": "A", "value": 20, "result": 7.0710678118654755},
        {"_id": 4, "partition": "A", "value": 30, "result": 7.0710678118654755},
    ]
    assertSuccess(
        result,
        expected,
        msg="Sliding window: null for single element and when -Inf in frame,"
        " recovers when -Inf leaves",
    )


def test_stdDevSamp_nan_sliding_returns_null(collection):
    """$stdDevSamp sliding window returns null when NaN is in the current frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 20},
        {"_id": 4, "partition": "A", "value": 30},
    ]
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [-1, 0]})
    # Row 1: frame=[NaN]       -> null (single element, N-1=0)
    # Row 2: frame=[NaN, 10]   -> null (NaN in removable window)
    # Row 3: frame=[10, 20]    -> sqrt(50) = 7.0710678118654755
    # Row 4: frame=[20, 30]    -> sqrt(50) = 7.0710678118654755
    expected = [
        {"_id": 1, "partition": "A", "value": FLOAT_NAN, "result": None},
        {"_id": 2, "partition": "A", "value": 10, "result": None},
        {"_id": 3, "partition": "A", "value": 20, "result": 7.0710678118654755},
        {"_id": 4, "partition": "A", "value": 30, "result": 7.0710678118654755},
    ]
    assertSuccessNaN(
        result,
        expected,
        msg="Sliding window: null for single element and when NaN in frame,"
        " recovers when NaN leaves",
    )


def test_stdDevSamp_infinity_centered_sliding(collection):
    """$stdDevSamp centered sliding window [-1, 1] with Infinity in middle returns null."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY},
        {"_id": 4, "partition": "A", "value": 30},
        {"_id": 5, "partition": "A", "value": 40},
    ]
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [-1, 1]})
    # Row 1: frame=[10, 20]         -> sqrt(50) = 7.0710678118654755 (clean, edge clamp)
    # Row 2: frame=[10, 20, Inf]    -> null (Inf in removable window)
    # Row 3: frame=[20, Inf, 30]    -> null (Inf in removable window)
    # Row 4: frame=[Inf, 30, 40]    -> null (Inf in removable window)
    # Row 5: frame=[30, 40]         -> sqrt(50) = 7.0710678118654755 (clean, edge clamp)
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 7.0710678118654755},
        {"_id": 2, "partition": "A", "value": 20, "result": None},
        {"_id": 3, "partition": "A", "value": FLOAT_INFINITY, "result": None},
        {"_id": 4, "partition": "A", "value": 30, "result": None},
        {"_id": 5, "partition": "A", "value": 40, "result": 7.0710678118654755},
    ]
    assertSuccess(
        result,
        expected,
        msg="Centered sliding: null when Inf in frame, clean rows compute correctly",
    )
