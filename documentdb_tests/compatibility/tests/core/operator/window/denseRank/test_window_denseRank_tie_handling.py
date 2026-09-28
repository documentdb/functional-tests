"""
Tests for $denseRank tie handling in window context.

$denseRank is a rank operator that assigns the same rank to documents with
equal sort values and does NOT skip rank positions after a tie. This is the
"dense" behavior: if two documents tie at rank 1, the next distinct sort value
gets rank 2 (not 3). This distinguishes $denseRank from $rank (which skips:
1, 1, 3) and from $documentNumber (which never shares: 1, 2, 3). These tests
cover no ties, all ties, and partial ties at the beginning, middle, and end
of a partition, as well as multiple tie groups and cross-partition isolation.
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess


def test_denseRank_no_ties(collection):
    """With all-distinct sort values, $denseRank assigns sequential 1, 2, 3, 4, 5."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 30},
        {"_id": 4, "partition": "A", "score": 40},
        {"_id": 5, "partition": "A", "score": 50},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
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
    assertSuccess(result, expected, msg="distinct sort values get sequential ranks")


def test_denseRank_all_ties(collection):
    """When every sort value ties, $denseRank assigns rank 1 to all documents."""
    docs = [
        {"_id": 1, "partition": "A", "score": 50},
        {"_id": 2, "partition": "A", "score": 50},
        {"_id": 3, "partition": "A", "score": 50},
        {"_id": 4, "partition": "A", "score": 50},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 50, "result": 1},
        {"_id": 2, "partition": "A", "score": 50, "result": 1},
        {"_id": 3, "partition": "A", "score": 50, "result": 1},
        {"_id": 4, "partition": "A", "score": 50, "result": 1},
    ]
    assertSuccess(result, expected, msg="all-tie partition gets rank 1 for every document")


def test_denseRank_partial_tie_at_beginning(collection):
    """A tie at the start shares rank 1, next distinct value gets rank 2 (dense)."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 10},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "result": 1},
        {"_id": 3, "partition": "A", "score": 20, "result": 2},
        {"_id": 4, "partition": "A", "score": 30, "result": 3},
    ]
    assertSuccess(result, expected, msg="tie at beginning yields 1,1,2,3 — no gap after tie")


def test_denseRank_partial_tie_in_middle(collection):
    """A tie in the middle shares the same rank, next value is rank+1 (dense)."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 20, "result": 2},
        {"_id": 3, "partition": "A", "score": 20, "result": 2},
        {"_id": 4, "partition": "A", "score": 30, "result": 3},
    ]
    assertSuccess(result, expected, msg="tie in middle yields 1,2,2,3 — no gap after tie")


def test_denseRank_partial_tie_at_end(collection):
    """A tie at the end shares the same rank — no gap before the tie."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 30},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 20, "result": 2},
        {"_id": 3, "partition": "A", "score": 30, "result": 3},
        {"_id": 4, "partition": "A", "score": 30, "result": 3},
    ]
    assertSuccess(result, expected, msg="tie at end yields 1,2,3,3 — tied docs share rank")


def test_denseRank_multiple_tie_groups(collection):
    """Multiple tie groups: each group shares a rank, no gaps between groups."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 10},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 20},
        {"_id": 5, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "result": 1},
        {"_id": 3, "partition": "A", "score": 20, "result": 2},
        {"_id": 4, "partition": "A", "score": 20, "result": 2},
        {"_id": 5, "partition": "A", "score": 30, "result": 3},
    ]
    assertSuccess(
        result, expected, msg="two tie groups yield 1,1,2,2,3 — dense ranking with no gaps"
    )


def test_denseRank_tie_across_partitions(collection):
    """Ties reset independently per partition — each partition ranks from 1."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 10},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "B", "score": 50},
        {"_id": 5, "partition": "B", "score": 50},
        {"_id": 6, "partition": "B", "score": 60},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "result": 1},
        {"_id": 3, "partition": "A", "score": 20, "result": 2},
        {"_id": 4, "partition": "B", "score": 50, "result": 1},
        {"_id": 5, "partition": "B", "score": 50, "result": 1},
        {"_id": 6, "partition": "B", "score": 60, "result": 2},
    ]
    assertSuccess(
        result, expected, msg="ties reset per partition — each partition starts at rank 1"
    )
