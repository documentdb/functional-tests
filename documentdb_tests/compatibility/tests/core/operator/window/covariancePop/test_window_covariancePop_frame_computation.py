"""
Tests for $covariancePop computation under documents-mode window frame shapes.

Verifies the operator computes correct results given the 4 defined frame shapes:
whole-partition, cumulative, reverse-cumulative, and sliding.

$covariancePop semantics:
- Takes array of exactly 2 expressions: ["$x", "$y"]
- Population covariance = sum((xi - mean_x)(yi - mean_y)) / N
- Single value (N=1) -> covariancePop = 0 (divides by N, not N-1)
- Empty window -> null

Note: Stage-level frame boundary tests (under stages/setWindowFields/) verify
that the correct documents are selected into the frame (centered, trailing,
leading, non-overlapping, edge cases). These per-operator tests verify the
operator produces correct values given those documents.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    COVAR_DOCS,
    WindowTestCase,
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# COVAR_DOCS: x = [1,2,3,4,5], y = [2,4,6,8,10] (y = 2x)
# mean_x = 3, mean_y = 6
# covPop = sum((xi-3)(yi-6))/5 = (8+2+0+2+8)/5 = 20/5 = 4.0


COVARIANCEPOP_DOCUMENTS_FRAME_TESTS: list[WindowTestCase] = [
    # Property [Whole Partition]: unbounded-unbounded frame covers entire partition
    # covPop(x, y) for all 5 docs = 4.0 (calculated above)
    WindowTestCase(
        "whole_partition",
        docs=COVAR_DOCS,
        window={"documents": ["unbounded", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
            {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 4.0},
            {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
            {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 4.0},
            {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 4.0},
        ],
        msg="whole partition covariancePop should be 4.0",
    ),
    # Property [Cumulative Frame]: expanding frame from start to current
    # Row 1 (n=1): [(1,2)] -> covPop = 0 (single value, divides by N=1)
    # Row 2 (n=2): [(1,2),(2,4)] -> mean_x=1.5, mean_y=3
    #   covPop = ((-0.5)(-1)+(0.5)(1))/2 = (0.5+0.5)/2 = 0.5
    # Row 3 (n=3): [(1,2),(2,4),(3,6)] -> mean_x=2, mean_y=4
    #   covPop = ((-1)(-2)+(0)(0)+(1)(2))/3 = (2+0+2)/3 = 4/3 = 1.3333...
    # Row 4 (n=4): [(1,2),(2,4),(3,6),(4,8)] -> mean_x=2.5, mean_y=5
    #   covPop = ((-1.5)(-3)+(-0.5)(-1)+(0.5)(1)+(1.5)(3))/4 = (4.5+0.5+0.5+4.5)/4 = 10/4 = 2.5
    # Row 5 (n=5): all docs -> covPop = 4.0
    WindowTestCase(
        "cumulative",
        docs=COVAR_DOCS,
        window={"documents": ["unbounded", "current"]},
        expected=[
            {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 0.0},
            {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 0.5},
            {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 1.3333333333333333},
            {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 2.5},
            {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 4.0},
        ],
        msg="cumulative covariancePop should grow",
    ),
    # Property [Reverse Cumulative Frame]: shrinking frame from current to end
    # Row 1 (n=5): all docs -> covPop = 4.0
    # Row 2 (n=4): [(2,4),(3,6),(4,8),(5,10)] -> mean_x=3.5, mean_y=7
    #   covPop = ((-1.5)(-3)+(-0.5)(-1)+(0.5)(1)+(1.5)(3))/4 = (4.5+0.5+0.5+4.5)/4 = 2.5
    # Row 3 (n=3): [(3,6),(4,8),(5,10)] -> mean_x=4, mean_y=8
    #   covPop = ((-1)(-2)+(0)(0)+(1)(2))/3 = 4/3 = 1.3333...
    # Row 4 (n=2): [(4,8),(5,10)] -> mean_x=4.5, mean_y=9
    #   covPop = ((-0.5)(-1)+(0.5)(1))/2 = 1/2 = 0.5
    # Row 5 (n=1): [(5,10)] -> covPop = 0
    WindowTestCase(
        "reverse_cumulative",
        docs=COVAR_DOCS,
        window={"documents": ["current", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
            {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 2.5},
            {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 1.3333333333333333},
            {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 0.5},
            {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 0.0},
        ],
        msg="reverse-cumulative covariancePop should shrink",
    ),
    # Property [Sliding Frame]: fixed-size window that moves with current row
    # Window [-1, 1] = 3-doc centered (clamped at edges)
    # Row 1: [(1,2),(2,4)] (edge clamp) -> mean_x=1.5, mean_y=3
    #   covPop = ((-0.5)(-1)+(0.5)(1))/2 = 0.5
    # Row 2: [(1,2),(2,4),(3,6)] -> mean_x=2, mean_y=4
    #   covPop = ((-1)(-2)+(0)(0)+(1)(2))/3 = 4/3 = 1.3333...
    # Row 3: [(2,4),(3,6),(4,8)] -> mean_x=3, mean_y=6
    #   covPop = ((-1)(-2)+(0)(0)+(1)(2))/3 = 4/3 = 1.3333...
    # Row 4: [(3,6),(4,8),(5,10)] -> mean_x=4, mean_y=8
    #   covPop = ((-1)(-2)+(0)(0)+(1)(2))/3 = 4/3 = 1.3333...
    # Row 5: [(4,8),(5,10)] (edge clamp) -> mean_x=4.5, mean_y=9
    #   covPop = ((-0.5)(-1)+(0.5)(1))/2 = 0.5
    WindowTestCase(
        "sliding_centered",
        docs=COVAR_DOCS,
        window={"documents": [-1, 1]},
        expected=[
            {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 0.5},
            {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 1.3333333333333333},
            {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 1.3333333333333333},
            {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 1.3333333333333333},
            {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 0.5},
        ],
        msg="centered sliding window [-1,1]",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COVARIANCEPOP_DOCUMENTS_FRAME_TESTS))
def test_covariancePop_documents_frames(collection, test):
    """$covariancePop with various documents-mode window frames."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        test.docs,
        test.window,
        sort_by=test.sort_by,
        expression=["$x", "$y"],
    )
    assertSuccess(result, test.expected, msg=test.msg)


def test_covariancePop_negative_correlation(collection):
    """$covariancePop with negative correlation (y decreases as x increases)."""
    # x = [1, 2, 3], y = [6, 4, 2] -> y = -2x + 8
    # mean_x=2, mean_y=4
    # covPop = ((-1)(2)+(0)(0)+(1)(-2))/3 = (-2+0-2)/3 = -4/3 = -1.3333...
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 6},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 2},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 6, "result": -1.3333333333333333},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": -1.3333333333333333},
        {"_id": 3, "partition": "A", "x": 3, "y": 2, "result": -1.3333333333333333},
    ]
    assertSuccess(result, expected, msg="negative correlation produces negative covariancePop")


def test_covariancePop_zero_covariance(collection):
    """$covariancePop returns 0 when variables are uncorrelated."""
    # x = [1, 2, 3], y = [5, 5, 5] -> y is constant
    # mean_x=2, mean_y=5
    # covPop = ((-1)(0)+(0)(0)+(1)(0))/3 = 0
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 5},
        {"_id": 2, "partition": "A", "x": 2, "y": 5},
        {"_id": 3, "partition": "A", "x": 3, "y": 5},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 5, "result": 0.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 5, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 5, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="constant y produces zero covariance")


def test_covariancePop_identical_x_and_y(collection):
    """$covariancePop where x == y reduces to population variance."""
    # When x==y: covPop(x,x) = varPop(x)
    # x = [10, 20, 30] -> mean=20, varPop = (100+0+100)/3 = 200/3 = 66.6667
    docs = [
        {"_id": 1, "partition": "A", "x": 10, "y": 10},
        {"_id": 2, "partition": "A", "x": 20, "y": 20},
        {"_id": 3, "partition": "A", "x": 30, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # covPop(x,x) = varPop(x) = 200/3
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "y": 10, "result": 66.66666666666667},
        {"_id": 2, "partition": "A", "x": 20, "y": 20, "result": 66.66666666666667},
        {"_id": 3, "partition": "A", "x": 30, "y": 30, "result": 66.66666666666667},
    ]
    assertSuccess(result, expected, msg="covPop(x,x) equals varPop(x)")


def test_covariancePop_trailing_sliding_window(collection):
    """$covariancePop with trailing sliding window [-1, 0]."""
    # Window [-1, 0] = look-back 1 row + current
    # Row 1: [(1,2)] (only current, edge) -> n=1 -> covPop = 0
    # Row 2: [(1,2),(2,4)] -> covPop = 0.5 (same as cumulative row 2)
    # Row 3: [(2,4),(3,6)] -> mean_x=2.5, mean_y=5
    #   covPop = ((-0.5)(-1)+(0.5)(1))/2 = 0.5
    # Row 4: [(3,6),(4,8)] -> mean_x=3.5, mean_y=7
    #   covPop = ((-0.5)(-1)+(0.5)(1))/2 = 0.5
    # Row 5: [(4,8),(5,10)] -> mean_x=4.5, mean_y=9
    #   covPop = ((-0.5)(-1)+(0.5)(1))/2 = 0.5
    docs = COVAR_DOCS
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 0.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 0.5},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 0.5},
        {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 0.5},
        {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 0.5},
    ]
    assertSuccess(result, expected, msg="trailing sliding window [-1, 0]")


def test_covariancePop_empty_window_returns_null(collection):
    """$covariancePop returns null when the window frame contains zero documents."""
    # Window [5, 10] on a 3-doc partition: for all rows, no documents fall in the frame
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [5, 10]},
        expression=["$x", "$y"],
    )
    # Frame [5, 10] means offset +5 to +10 from current row — no such rows exist
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": None},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": None},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": None},
    ]
    assertSuccess(result, expected, msg="empty window frame returns null")
