"""
Tests for $covariancePop with special float values (NaN, Infinity, -Infinity).

Covers: Infinity as numeric participant, -Infinity, NaN values,
sliding window behavior with special floats, and cumulative window behavior.

$covariancePop semantics for special floats (verified against server 8.2.4):
- NaN and Infinity are numeric values (not ignored like null/missing)
- In non-removable windows (whole partition): Inf produces Infinity, -Inf produces
  -Infinity, NaN produces NaN, Inf+(-Inf) cancels to 0.0, all-Inf produces null
- In cumulative windows (unbounded, current): single Inf = null, then propagates
- In sliding/removable windows: Inf/NaN in frame yields specific behavior
  (not simply null) — Row with only special value returns null, pairs with Inf
  can return 0.0, clean frames compute normally
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

# Property [Infinity Non-Removable Window]: Infinity in non-removable whole partition windows


def test_covariancePop_positive_infinity_whole_partition(collection):
    """$covariancePop with Infinity in x, whole partition returns Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": FLOAT_INFINITY, "y": 4},
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
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": FLOAT_INFINITY, "y": 4, "result": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_INFINITY},
    ]
    assertSuccess(result, expected, msg="Infinity in x produces Infinity for whole partition")


def test_covariancePop_positive_infinity_in_y(collection):
    """$covariancePop with Infinity in second expression (y) produces Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
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
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_INFINITY, "result": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_INFINITY},
    ]
    assertSuccess(result, expected, msg="Infinity in y produces Infinity in whole partition")


def test_covariancePop_negative_infinity_in_y(collection):
    """$covariancePop with -Infinity in second expression (y) produces -Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_NEGATIVE_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
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
        {
            "_id": 1,
            "partition": "A",
            "x": 1,
            "y": FLOAT_NEGATIVE_INFINITY,
            "result": FLOAT_NEGATIVE_INFINITY,
        },
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": FLOAT_NEGATIVE_INFINITY},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_NEGATIVE_INFINITY},
    ]
    assertSuccess(result, expected, msg="-Infinity in y produces -Infinity in whole partition")


def test_covariancePop_opposing_infinity_same_pair(collection):
    """$covariancePop with +Inf and -Inf in the same (x, y) pair produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": FLOAT_NEGATIVE_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": FLOAT_INFINITY,
            "y": FLOAT_NEGATIVE_INFINITY,
            "result": FLOAT_NAN,
        },
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="opposing infinities in same pair produce NaN")


def test_covariancePop_both_inf_signs_separate_rows(collection):
    """$covariancePop with +Inf and -Inf in separate rows, count_finite>=2, produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": FLOAT_NAN},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="both inf signs in separate rows with count_finite>=2 produce NaN"
    )


def test_covariancePop_mixed_inf_types_across_rows(collection):
    """$covariancePop with opposing-sign pair + same-sign pair + finite: count_finite=1 -> 0."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": 5, "y": FLOAT_NEGATIVE_INFINITY},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": FLOAT_INFINITY, "result": 0.0},
        {"_id": 2, "partition": "A", "x": 5, "y": FLOAT_NEGATIVE_INFINITY, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="mixed inf types with count_finite=1 returns 0.0 for Pop")


def test_covariancePop_opposing_inf_signs_across_columns(collection):
    """$covariancePop with -Inf in x (one row) and +Inf in y (another row) produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": FLOAT_INFINITY},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 3, "y": FLOAT_INFINITY, "result": FLOAT_NAN},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="opposing inf signs across x and y columns produce NaN")


def test_covariancePop_negative_infinity_whole_partition(collection):
    """$covariancePop with -Infinity in x, whole partition returns -Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 4},
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
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": FLOAT_NEGATIVE_INFINITY},
        {
            "_id": 2,
            "partition": "A",
            "x": FLOAT_NEGATIVE_INFINITY,
            "y": 4,
            "result": FLOAT_NEGATIVE_INFINITY,
        },
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_NEGATIVE_INFINITY},
    ]
    assertSuccess(result, expected, msg="-Infinity in x produces -Infinity for whole partition")


def test_covariancePop_inf_and_neg_inf_in_same_frame(collection):
    """$covariancePop with both Infinity and -Infinity in x cancels to 0.0."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": 10, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": 0.0},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 10, "y": 30, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="Inf + -Inf in same frame cancels to 0.0")


def test_covariancePop_all_infinity_values(collection):
    """$covariancePop where all x values are Infinity returns null (Inf-Inf=NaN internally)."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": FLOAT_INFINITY, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": FLOAT_INFINITY, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": FLOAT_INFINITY, "y": 30, "result": None},
    ]
    assertSuccess(
        result, expected, msg="All Inf x values: Inf-Inf=NaN internally, server returns null"
    )


def test_covariancePop_infinity_cumulative_window(collection):
    """$covariancePop cumulative [unbounded, current] with Infinity in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "current"]},
        expression=["$x", "$y"],
    )
    # Row 1: single Inf value -> null
    # Row 2: frame=[(Inf,10),(2,20)] -> 0.0
    # Row 3: frame=[(Inf,10),(2,20),(3,30)] -> Infinity
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": FLOAT_INFINITY},
    ]
    assertSuccess(
        result, expected, msg="Cumulative: single Inf=null, 2 values=0.0, 3 values=Infinity"
    )


def test_covariancePop_single_infinity_value(collection):
    """$covariancePop with single Infinity value in whole partition returns null."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
    ]
    assertSuccess(result, expected, msg="Single Inf value: covariancePop returns null")


# Property [NaN Non-Removable Window]: NaN in non-removable windows produces NaN


def test_covariancePop_nan_value_whole_partition(collection):
    """$covariancePop with NaN in non-removable window produces NaN (NaN is numeric, poisons)."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": FLOAT_NAN, "y": 4},
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
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": FLOAT_NAN, "y": 4, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="NaN is numeric; non-removable window produces NaN")


def test_covariancePop_nan_in_y_whole_partition(collection):
    """$covariancePop with NaN in second expression (y) produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": FLOAT_NAN},
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
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": 2, "y": FLOAT_NAN, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="NaN in y expression poisons non-removable window to NaN"
    )


# Property [Special Floats Sliding Window]: special floats in removable/sliding windows


def test_covariancePop_infinity_sliding(collection):
    """$covariancePop sliding window [-1,0] with Infinity in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
        {"_id": 5, "partition": "A", "x": 5, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(Inf,10)]           -> null (single Inf pair)
    # Row 2: frame=[(Inf,10),(2,20)]    -> 0.0
    # Row 3: frame=[(2,20),(3,30)]      -> covPop = 2.5
    # Row 4: frame=[(3,30),(4,40)]      -> covPop = 2.5
    # Row 5: frame=[(4,40),(5,50)]      -> covPop = 2.5
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 2.5},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 2.5},
        {"_id": 5, "partition": "A", "x": 5, "y": 50, "result": 2.5},
    ]
    assertSuccess(
        result, expected, msg="Sliding window: null for single Inf, 0.0 for Inf pair, then recovers"
    )


def test_covariancePop_neg_infinity_sliding(collection):
    """$covariancePop sliding window [-1,0] with -Infinity in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(-Inf,10)]           -> null (single -Inf pair)
    # Row 2: frame=[(-Inf,10),(2,20)]    -> 0.0
    # Row 3: frame=[(2,20),(3,30)]       -> covPop = 2.5
    # Row 4: frame=[(3,30),(4,40)]       -> covPop = 2.5
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 2.5},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 2.5},
    ]
    assertSuccess(
        result,
        expected,
        msg="Sliding window: null for single -Inf, 0.0 for -Inf pair, then recovers",
    )


def test_covariancePop_nan_sliding(collection):
    """$covariancePop sliding window [-1,0] with NaN in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_NAN, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(NaN,10)]           -> null (single NaN pair)
    # Row 2: frame=[(NaN,10),(2,20)]    -> 0.0
    # Row 3: frame=[(2,20),(3,30)]      -> covPop = 2.5
    # Row 4: frame=[(3,30),(4,40)]      -> covPop = 2.5
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_NAN, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 2.5},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 2.5},
    ]
    assertSuccessNaN(
        result, expected, msg="Sliding window: null for single NaN, 0.0 for NaN pair, then recovers"
    )


def test_covariancePop_infinity_centered_sliding(collection):
    """$covariancePop centered sliding window [-1, 1] with Infinity in middle."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": FLOAT_INFINITY, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
        {"_id": 5, "partition": "A", "x": 5, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-1, 1]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(1,10),(2,20)] -> covPop = 2.5
    # Row 2: frame=[(1,10),(2,20),(Inf,30)] -> Infinity (Inf propagates in 3-elem frame)
    # Row 3: frame=[(2,20),(Inf,30),(4,40)] -> Infinity
    # Row 4: frame=[(Inf,30),(4,40),(5,50)] -> Infinity
    # Row 5: frame=[(4,40),(5,50)] -> covPop = 2.5 (with possible FP rounding)
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10, "result": 2.5},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "x": FLOAT_INFINITY, "y": 30, "result": FLOAT_INFINITY},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": FLOAT_INFINITY},
        {"_id": 5, "partition": "A", "x": 5, "y": 50, "result": 2.5000000000000107},
    ]
    assertSuccess(
        result,
        expected,
        msg="Centered sliding: Inf propagates in 3-elem frames, clean 2-elem frames = 2.5",
    )


def test_covariancePop_nan_in_y_sliding(collection):
    """$covariancePop sliding window [-1,0] with NaN in y of first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(1,NaN)]           -> null (single pair with NaN)
    # Row 2: frame=[(1,NaN),(2,20)]    -> 0.0
    # Row 3: frame=[(2,20),(3,30)]     -> covPop = 2.5
    # Row 4: frame=[(3,30),(4,40)]     -> covPop = 2.5
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_NAN, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 2.5},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 2.5},
    ]
    assertSuccessNaN(
        result,
        expected,
        msg="Sliding window: null for single NaN-y, 0.0 for NaN-y pair, then recovers",
    )
