"""
Tests for $covariancePop order independence in window context.

Verifies that $covariancePop produces the same result regardless of sortBy direction,
confirming it is an order-independent operator. Population covariance is a
symmetric statistic over the frame — it depends only on which documents are in
the frame, not on their processing order.
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    COVAR_DOCS,
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

UNBOUNDED_WINDOW = {"documents": ["unbounded", "unbounded"]}

# Property [Order Independence]: $covariancePop produces same result regardless of sort direction


def test_covariancePop_whole_partition_ascending_sort(collection):
    """$covariancePop whole partition with ascending sort."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=COVAR_DOCS,
        expression=["$x", "$y"],
        window=UNBOUNDED_WINDOW,
        sort_by={"_id": 1},
    )
    # covPop of (x,y) where y=2x: covPop = 4.0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 4.0},
        {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 4.0},
    ]
    assertSuccess(result, expected, msg="ascending sort produces correct covariancePop")


def test_covariancePop_whole_partition_descending_sort(collection):
    """$covariancePop whole partition with descending sort produces same result as ascending."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=COVAR_DOCS,
        expression=["$x", "$y"],
        window=UNBOUNDED_WINDOW,
        sort_by={"_id": -1},
        extra_stages=[{"$sort": {"_id": 1}}],
    )
    # Same result regardless of sort direction — order-independent operator
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 4.0},
        {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 4.0},
    ]
    assertSuccess(
        result, expected, msg="descending sort produces same covariancePop — order independent"
    )


def test_covariancePop_sort_by_value_vs_sort_by_id(collection):
    """$covariancePop whole partition: sort by value field vs sort by _id gives same result."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=COVAR_DOCS,
        expression=["$x", "$y"],
        window=UNBOUNDED_WINDOW,
        sort_by={"x": -1},
        extra_stages=[{"$sort": {"_id": 1}}],
    )
    # Sorting by x descending should not affect whole-partition covariancePop
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 4.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 4.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 4.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 8, "result": 4.0},
        {"_id": 5, "partition": "A", "x": 5, "y": 10, "result": 4.0},
    ]
    assertSuccess(
        result,
        expected,
        msg="sort by value field produces same result as sort by _id — order independent",
    )


NEGATIVE_COVAR_DOCS = [
    {"_id": 1, "partition": "A", "x": 1, "y": 10},
    {"_id": 2, "partition": "A", "x": 2, "y": 8},
    {"_id": 3, "partition": "A", "x": 3, "y": 6},
    {"_id": 4, "partition": "A", "x": 4, "y": 4},
    {"_id": 5, "partition": "A", "x": 5, "y": 2},
]

# x=[1,2,3,4,5] mean=3, y=[10,8,6,4,2] mean=6
# covPop = ((-2)(4)+(-1)(2)+(0)(0)+(1)(-2)+(2)(-4))/5 = (-8-2+0-2-8)/5 = -20/5 = -4.0
NEGATIVE_COVAR_EXPECTED = [
    {"_id": 1, "partition": "A", "x": 1, "y": 10, "result": -4.0},
    {"_id": 2, "partition": "A", "x": 2, "y": 8, "result": -4.0},
    {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": -4.0},
    {"_id": 4, "partition": "A", "x": 4, "y": 4, "result": -4.0},
    {"_id": 5, "partition": "A", "x": 5, "y": 2, "result": -4.0},
]


def test_covariancePop_negative_correlation_ascending_sort(collection):
    """$covariancePop with negative correlation gives correct result with ascending sort."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=NEGATIVE_COVAR_DOCS,
        expression=["$x", "$y"],
        window=UNBOUNDED_WINDOW,
        sort_by={"_id": 1},
    )
    assertSuccess(
        result, NEGATIVE_COVAR_EXPECTED, msg="negative correlation ascending sort gives -4.0"
    )


def test_covariancePop_negative_correlation_descending_sort(collection):
    """$covariancePop with negative correlation gives same result with descending sort."""
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs=NEGATIVE_COVAR_DOCS,
        expression=["$x", "$y"],
        window=UNBOUNDED_WINDOW,
        sort_by={"_id": -1},
        extra_stages=[{"$sort": {"_id": 1}}],
    )
    assertSuccess(
        result, NEGATIVE_COVAR_EXPECTED, msg="negative correlation descending sort gives same -4.0"
    )
