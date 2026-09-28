"""
Tests for $documentNumber tie handling in window context.

$documentNumber is a rank operator: it assigns a unique sequential position
(1, 2, 3, ...) to every document in a partition in sortBy order, regardless of
whether the sortBy values tie. This is the distinguishing behavior from $rank
(which skips positions after a tie: 1, 1, 3) and $denseRank (which does not:
1, 1, 2). These tests cover no ties, all ties, and partial ties at the
beginning, middle, and end of a partition.
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess


def test_documentNumber_no_ties(collection):
    """With all-distinct sort values, $documentNumber assigns 1, 2, 3, 4, 5."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 30},
        {"_id": 4, "partition": "A", "score": 40},
        {"_id": 5, "partition": "A", "score": 50},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 20, "result": 2},
        {"_id": 3, "partition": "A", "score": 30, "result": 3},
        {"_id": 4, "partition": "A", "score": 40, "result": 4},
        {"_id": 5, "partition": "A", "score": 50, "result": 5},
    ]
    assertSuccess(result, expected, msg="distinct sort values get sequential positions")


def test_documentNumber_all_ties(collection):
    """When every sort value ties, $documentNumber still assigns unique 1..N."""
    docs = [
        {"_id": 1, "partition": "A", "score": 50},
        {"_id": 2, "partition": "A", "score": 50},
        {"_id": 3, "partition": "A", "score": 50},
        {"_id": 4, "partition": "A", "score": 50},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 50, "result": 1},
        {"_id": 2, "partition": "A", "score": 50, "result": 2},
        {"_id": 3, "partition": "A", "score": 50, "result": 3},
        {"_id": 4, "partition": "A", "score": 50, "result": 4},
    ]
    assertSuccess(result, expected, msg="all-tie partition still gets unique positions")


def test_documentNumber_partial_tie_at_beginning(collection):
    """A tie at the start of the partition does not repeat positions (1, 2, 3, 4)."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 10},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "result": 2},
        {"_id": 3, "partition": "A", "score": 20, "result": 3},
        {"_id": 4, "partition": "A", "score": 30, "result": 4},
    ]
    assertSuccess(result, expected, msg="tie at beginning yields unique positions")


def test_documentNumber_partial_tie_in_middle(collection):
    """A tie in the middle of the partition does not repeat positions (1, 2, 3, 4)."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 20, "result": 2},
        {"_id": 3, "partition": "A", "score": 20, "result": 3},
        {"_id": 4, "partition": "A", "score": 30, "result": 4},
    ]
    assertSuccess(result, expected, msg="tie in middle yields unique positions")


def test_documentNumber_partial_tie_at_end(collection):
    """A tie at the end of the partition does not repeat positions (1, 2, 3, 4)."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 30},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 20, "result": 2},
        {"_id": 3, "partition": "A", "score": 30, "result": 3},
        {"_id": 4, "partition": "A", "score": 30, "result": 4},
    ]
    assertSuccess(result, expected, msg="tie at end yields unique positions")
