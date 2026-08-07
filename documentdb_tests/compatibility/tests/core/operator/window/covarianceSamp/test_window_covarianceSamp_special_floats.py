"""
Tests for $covarianceSamp with special float values (NaN, Infinity, -Infinity).

Covers: Infinity as numeric participant, -Infinity, NaN values,
sliding window behavior with special floats, and cumulative window behavior.

$covarianceSamp semantics for special floats (verified against server 8.2.4):
- NaN and Infinity are numeric values (not ignored like null/missing)
- Single value (N=1) always returns null for covarianceSamp (regardless of value type)
- In non-removable windows (whole partition): Inf produces Infinity, -Inf produces
  -Infinity, NaN produces NaN, Inf+(-Inf) cancels to 0.0, all-Inf produces null
- In cumulative windows (unbounded, current): single value = null, then propagates
- In sliding/removable windows: single-value frames return null, pairs with Inf
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


def test_covarianceSamp_positive_infinity_whole_partition(collection):
    """$covarianceSamp with Infinity in x, whole partition returns Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": FLOAT_INFINITY, "y": 4},
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
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": FLOAT_INFINITY, "y": 4, "result": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_INFINITY},
    ]
    assertSuccess(result, expected, msg="Infinity in x produces Infinity for whole partition")


def test_covarianceSamp_positive_infinity_in_y(collection):
    """$covarianceSamp with Infinity in second expression (y) produces Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
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
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_INFINITY, "result": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_INFINITY},
    ]
    assertSuccess(result, expected, msg="Infinity in y produces Infinity in whole partition")


def test_covarianceSamp_negative_infinity_in_y(collection):
    """$covarianceSamp with -Infinity in second expression (y) produces -Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_NEGATIVE_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
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


def test_covarianceSamp_opposing_infinity_same_pair(collection):
    """$covarianceSamp with +Inf and -Inf in the same (x, y) pair produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": FLOAT_NEGATIVE_INFINITY},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
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


def test_covarianceSamp_both_inf_signs_separate_rows(collection):
    """$covarianceSamp with +Inf and -Inf in separate rows, count_finite>=2, produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
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


def test_covarianceSamp_mixed_inf_types_across_rows(collection):
    """$covarianceSamp with opposing-sign pair + same-sign pair + finite: count_finite=1 -> null."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": FLOAT_INFINITY},
        {"_id": 2, "partition": "A", "x": 5, "y": FLOAT_NEGATIVE_INFINITY},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": FLOAT_INFINITY, "result": None},
        {"_id": 2, "partition": "A", "x": 5, "y": FLOAT_NEGATIVE_INFINITY, "result": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": None},
    ]
    assertSuccess(result, expected, msg="mixed inf types with count_finite=1 returns null for Samp")


def test_covarianceSamp_opposing_inf_signs_across_columns(collection):
    """$covarianceSamp with -Inf in x (one row) and +Inf in y (another row) produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": FLOAT_INFINITY},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
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


def test_covarianceSamp_negative_infinity_whole_partition(collection):
    """$covarianceSamp with -Infinity in x, whole partition returns -Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 4},
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


def test_covarianceSamp_inf_and_neg_inf_in_same_frame(collection):
    """$covarianceSamp with both Infinity and -Infinity in x returns null."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": 10, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": 10, "y": 30, "result": None},
    ]
    assertSuccess(
        result,
        expected,
        msg="Inf + -Inf in same frame: only 1 finite pair, covarianceSamp returns null",
    )


def test_covarianceSamp_all_infinity_values(collection):
    """$covarianceSamp where all x values are Infinity returns null (Inf-Inf=NaN internally)."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": FLOAT_INFINITY, "y": 20},
        {"_id": 3, "partition": "A", "x": FLOAT_INFINITY, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
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


def test_covarianceSamp_infinity_cumulative_window(collection):
    """$covarianceSamp cumulative [unbounded, current] with Infinity in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "current"]},
        expression=["$x", "$y"],
    )
    # Row 1: single Inf value -> null (N=1, covSamp undefined)
    # Row 2: frame=[(Inf,10),(2,20)] -> null (only 1 finite pair, covSamp needs N-1>=1 finite)
    # Row 3: frame=[(Inf,10),(2,20),(3,30)] -> Infinity (2 finite pairs + Inf propagates)
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": FLOAT_INFINITY},
    ]
    assertSuccess(
        result,
        expected,
        msg="Cumulative: single Inf=null, 2 values with Inf=null, 3 values=Infinity",
    )


def test_covarianceSamp_single_infinity_value(collection):
    """$covarianceSamp with single Infinity value in whole partition returns null."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
    ]
    assertSuccess(result, expected, msg="Single Inf value: covarianceSamp returns null")


# Property [NaN Non-Removable Window]: NaN in non-removable windows produces NaN


def test_covarianceSamp_nan_value_whole_partition(collection):
    """$covarianceSamp with NaN in non-removable window produces NaN (NaN is numeric, poisons)."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": FLOAT_NAN, "y": 4},
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
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": FLOAT_NAN, "y": 4, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="NaN is numeric; non-removable window produces NaN")


def test_covarianceSamp_nan_in_y_whole_partition(collection):
    """$covarianceSamp with NaN in second expression (y) produces NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": FLOAT_NAN},
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
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": 2, "y": FLOAT_NAN, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="NaN in y expression poisons non-removable window to NaN"
    )


# Property [Special Floats Sliding Window]: special floats in removable/sliding windows


def test_covarianceSamp_infinity_sliding(collection):
    """$covarianceSamp sliding window [-1,0] with Infinity in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
        {"_id": 5, "partition": "A", "x": 5, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(Inf,10)]           -> null (single value, covSamp undefined)
    # Row 2: frame=[(Inf,10),(2,20)]    -> null (only 1 finite pair, covSamp needs >= 2 finite)
    # Row 3: frame=[(2,20),(3,30)]      -> covSamp = 5.0
    # Row 4: frame=[(3,30),(4,40)]      -> covSamp = 5.0
    # Row 5: frame=[(4,40),(5,50)]      -> covSamp = 5.0
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 5.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 5.0},
        {"_id": 5, "partition": "A", "x": 5, "y": 50, "result": 5.0},
    ]
    assertSuccess(
        result,
        expected,
        msg="Sliding window: null for single Inf, null for Inf pair, then recovers",
    )


def test_covarianceSamp_neg_infinity_sliding(collection):
    """$covarianceSamp sliding window [-1,0] with -Infinity in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(-Inf,10)]           -> null (single value, covSamp undefined)
    # Row 2: frame=[(-Inf,10),(2,20)]    -> null (only 1 finite pair, covSamp needs >= 2 finite)
    # Row 3: frame=[(2,20),(3,30)]       -> covSamp = 5.0
    # Row 4: frame=[(3,30),(4,40)]       -> covSamp = 5.0
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_NEGATIVE_INFINITY, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 5.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 5.0},
    ]
    assertSuccess(
        result,
        expected,
        msg="Sliding window: null for single -Inf, null for -Inf pair, then recovers",
    )


def test_covarianceSamp_nan_sliding(collection):
    """$covarianceSamp sliding window [-1,0] with NaN in first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": FLOAT_NAN, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(NaN,10)]           -> null (single value, covSamp undefined)
    # Row 2: frame=[(NaN,10),(2,20)]    -> null (only 1 finite pair, covSamp needs >= 2 finite)
    # Row 3: frame=[(2,20),(3,30)]      -> covSamp = 5.0
    # Row 4: frame=[(3,30),(4,40)]      -> covSamp = 5.0
    expected = [
        {"_id": 1, "partition": "A", "x": FLOAT_NAN, "y": 10, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 5.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 5.0},
    ]
    assertSuccessNaN(
        result,
        expected,
        msg="Sliding window: null for single NaN, null for NaN pair, then recovers",
    )


def test_covarianceSamp_infinity_centered_sliding(collection):
    """$covarianceSamp centered sliding window [-1, 1] with Infinity in middle."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": FLOAT_INFINITY, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
        {"_id": 5, "partition": "A", "x": 5, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": [-1, 1]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(1,10),(2,20)] (n=2) -> covSamp = 5.0
    # Row 2: frame=[(1,10),(2,20),(Inf,30)] (n=3) -> Infinity (Inf propagates in 3-elem frame)
    # Row 3: frame=[(2,20),(Inf,30),(4,40)] (n=3) -> Infinity
    # Row 4: frame=[(Inf,30),(4,40),(5,50)] (n=3) -> Infinity
    # Row 5: frame=[(4,40),(5,50)] (n=2) -> covSamp = 5.0 (with possible FP rounding)
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10, "result": 5.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": FLOAT_INFINITY},
        {"_id": 3, "partition": "A", "x": FLOAT_INFINITY, "y": 30, "result": FLOAT_INFINITY},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": FLOAT_INFINITY},
        {"_id": 5, "partition": "A", "x": 5, "y": 50, "result": 5.000000000000021},
    ]
    assertSuccess(
        result,
        expected,
        msg="Centered sliding: Inf propagates in 3-elem frames, clean 2-elem frames = 5.0",
    )


def test_covarianceSamp_nan_in_y_sliding(collection):
    """$covarianceSamp sliding window [-1,0] with NaN in y of first row."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
    ]
    result = run_window_operator(
        collection,
        "$covarianceSamp",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Row 1: frame=[(1,NaN)]           -> null (single pair, covSamp undefined)
    # Row 2: frame=[(1,NaN),(2,20)]    -> null (only 1 finite pair, covSamp needs >= 2 finite)
    # Row 3: frame=[(2,20),(3,30)]     -> covSamp = 5.0
    # Row 4: frame=[(3,30),(4,40)]     -> covSamp = 5.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": FLOAT_NAN, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 5.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 5.0},
    ]
    assertSuccessNaN(
        result,
        expected,
        msg="Sliding window: null for single NaN-y, null for NaN-y pair, then recovers",
    )
