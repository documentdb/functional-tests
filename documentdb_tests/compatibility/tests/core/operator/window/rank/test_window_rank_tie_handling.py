"""
Tests for $rank tie handling in window context.

$rank is a rank operator that assigns positions where tied documents (same sort
value) share the same rank, and the next distinct value skips positions. For
example, two documents tied at rank 1 produce ranks 1, 1, 3 — position 2 is
skipped. This is the distinguishing behavior from $documentNumber (which always
assigns unique sequential positions: 1, 2, 3) and $denseRank (which shares
rank but does not skip: 1, 1, 2). These tests cover no ties, all ties, and
partial ties at the beginning, middle, and end of a partition, as well as
multiple tie groups and cross-partition independence.
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess


def test_rank_no_ties(collection):
    """With all-distinct sort values, $rank assigns sequential 1, 2, 3, 4, 5."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 30},
        {"_id": 4, "partition": "A", "score": 40},
        {"_id": 5, "partition": "A", "score": 50},
    ]
    result = run_window_operator(
        collection,
        "$rank",
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
    assertSuccess(result, expected, msg="distinct sort values get sequential ranks 1..5")


def test_rank_all_ties(collection):
    """When every sort value ties, $rank assigns rank 1 to all documents."""
    docs = [
        {"_id": 1, "partition": "A", "score": 50},
        {"_id": 2, "partition": "A", "score": 50},
        {"_id": 3, "partition": "A", "score": 50},
        {"_id": 4, "partition": "A", "score": 50},
    ]
    result = run_window_operator(
        collection,
        "$rank",
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
    assertSuccess(result, expected, msg="all-tie partition assigns rank 1 to every document")


def test_rank_partial_tie_at_beginning(collection):
    """A tie at the start shares rank 1 and skips rank 2 → 1, 1, 3, 4."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 10},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$rank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "result": 1},
        {"_id": 3, "partition": "A", "score": 20, "result": 3},
        {"_id": 4, "partition": "A", "score": 30, "result": 4},
    ]
    assertSuccess(result, expected, msg="tie at beginning yields 1, 1, 3, 4 — rank 2 skipped")


def test_rank_partial_tie_in_middle(collection):
    """A tie in the middle shares rank 2 and skips rank 3 → 1, 2, 2, 4."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$rank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 20, "result": 2},
        {"_id": 3, "partition": "A", "score": 20, "result": 2},
        {"_id": 4, "partition": "A", "score": 30, "result": 4},
    ]
    assertSuccess(result, expected, msg="tie in middle yields 1, 2, 2, 4 — rank 3 skipped")


def test_rank_partial_tie_at_end(collection):
    """A tie at the end shares rank 3 → 1, 2, 3, 3."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 20},
        {"_id": 3, "partition": "A", "score": 30},
        {"_id": 4, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$rank",
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
    assertSuccess(result, expected, msg="tie at end yields 1, 2, 3, 3 — no skip needed at tail")


def test_rank_multiple_tie_groups(collection):
    """Two separate tie groups → 1, 1, 3, 3, 5 — each group skips the next."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 10},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "A", "score": 20},
        {"_id": 5, "partition": "A", "score": 30},
    ]
    result = run_window_operator(
        collection,
        "$rank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "result": 1},
        {"_id": 3, "partition": "A", "score": 20, "result": 3},
        {"_id": 4, "partition": "A", "score": 20, "result": 3},
        {"_id": 5, "partition": "A", "score": 30, "result": 5},
    ]
    assertSuccess(
        result,
        expected,
        msg="two tie groups yield 1, 1, 3, 3, 5 — positions 2 and 4 skipped",
    )


def test_rank_tie_across_partitions(collection):
    """Ties in separate partitions are ranked independently — each restarts at 1."""
    docs = [
        {"_id": 1, "partition": "A", "score": 10},
        {"_id": 2, "partition": "A", "score": 10},
        {"_id": 3, "partition": "A", "score": 20},
        {"_id": 4, "partition": "B", "score": 10},
        {"_id": 5, "partition": "B", "score": 10},
        {"_id": 6, "partition": "B", "score": 20},
    ]
    result = run_window_operator(
        collection,
        "$rank",
        docs,
        sort_by={"score": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "score": 10, "result": 1},
        {"_id": 2, "partition": "A", "score": 10, "result": 1},
        {"_id": 3, "partition": "A", "score": 20, "result": 3},
        {"_id": 4, "partition": "B", "score": 10, "result": 1},
        {"_id": 5, "partition": "B", "score": 10, "result": 1},
        {"_id": 6, "partition": "B", "score": 20, "result": 3},
    ]
    assertSuccess(
        result,
        expected,
        msg="tie handling resets independently per partition — both partitions get 1, 1, 3",
    )
