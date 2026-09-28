"""
Tests for $denseRank order dependence and partition semantics.

$denseRank is order-dependent: ranks are assigned in sortBy order, so
reversing the sort direction or sorting on a different field produces different
ranks for the same documents. Ranking restarts at 1 in every partition.
Documents with the same sort value share the same rank, and the next distinct
value gets the immediately following rank (no gaps).
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    BASIC_DOCS,
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

# Property [Order Dependence]: changing sortBy changes the assigned ranks.


def test_denseRank_ascending_sort(collection):
    """Ascending sort assigns ranks in ascending order of the sort field."""
    result = run_window_operator(
        collection,
        "$denseRank",
        BASIC_DOCS,
        sort_by={"_id": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 1},
        {"_id": 2, "partition": "A", "value": 20, "result": 2},
        {"_id": 3, "partition": "A", "value": 30, "result": 3},
        {"_id": 4, "partition": "A", "value": 40, "result": 4},
        {"_id": 5, "partition": "A", "value": 50, "result": 5},
    ]
    assertSuccess(result, expected, msg="ascending sort ranks documents 1..5 in _id order")


def test_denseRank_descending_sort(collection):
    """Descending sort reverses the assigned ranks — order-dependent operator."""
    result = run_window_operator(
        collection,
        "$denseRank",
        BASIC_DOCS,
        sort_by={"_id": -1},
        expression={},
    )
    expected = [
        {"_id": 5, "partition": "A", "value": 50, "result": 1},
        {"_id": 4, "partition": "A", "value": 40, "result": 2},
        {"_id": 3, "partition": "A", "value": 30, "result": 3},
        {"_id": 2, "partition": "A", "value": 20, "result": 4},
        {"_id": 1, "partition": "A", "value": 10, "result": 5},
    ]
    assertSuccess(
        result,
        expected,
        msg="descending sort reverses ranks — different result than ascending",
    )


def test_denseRank_sort_on_different_field(collection):
    """Sorting on a different field assigns ranks by that field's order."""
    docs = [
        {"_id": 1, "partition": "A", "value": 50},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"value": 1},
        expression={},
    )
    expected = [
        {"_id": 2, "partition": "A", "value": 10, "result": 1},
        {"_id": 3, "partition": "A", "value": 30, "result": 2},
        {"_id": 1, "partition": "A", "value": 50, "result": 3},
    ]
    assertSuccess(result, expected, msg="output follows the value sort order; ranks 1..3 by value")


# Property [Partition Isolation]: ranking restarts at 1 in each partition.


def test_denseRank_restarts_per_partition(collection):
    """Each partition is ranked independently starting from 1."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "B", "value": 30},
        {"_id": 4, "partition": "B", "value": 40},
        {"_id": 5, "partition": "B", "value": 50},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"_id": 1},
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 1},
        {"_id": 2, "partition": "A", "value": 20, "result": 2},
        {"_id": 3, "partition": "B", "value": 30, "result": 1},
        {"_id": 4, "partition": "B", "value": 40, "result": 2},
        {"_id": 5, "partition": "B", "value": 50, "result": 3},
    ]
    assertSuccess(result, expected, msg="ranking restarts at 1 in each partition")


def test_denseRank_without_partitionBy(collection):
    """Omitting partitionBy treats the whole collection as a single partition."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "B", "value": 20},
        {"_id": 3, "partition": "C", "value": 30},
    ]
    result = run_window_operator(
        collection,
        "$denseRank",
        docs,
        sort_by={"_id": 1},
        partition_by=None,
        expression={},
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 1},
        {"_id": 2, "partition": "B", "value": 20, "result": 2},
        {"_id": 3, "partition": "C", "value": 30, "result": 3},
    ]
    assertSuccess(
        result, expected, msg="omitted partitionBy ranks the whole collection continuously"
    )


# Property [Empty and Single-Document Input]: smallest partition sizes rank correctly.


def test_denseRank_single_document_partition(collection):
    """A single-document partition gets rank 1."""
    result = run_window_operator(
        collection,
        "$denseRank",
        [{"_id": 1, "partition": "A", "value": 10}],
        sort_by={"_id": 1},
        expression={},
    )
    assertSuccess(
        result,
        [{"_id": 1, "partition": "A", "value": 10, "result": 1}],
        msg="single-document partition gets rank 1",
    )


def test_denseRank_empty_collection(collection):
    """$denseRank on an empty collection returns no documents without error."""
    result = run_window_operator(
        collection,
        "$denseRank",
        [],
        sort_by={"_id": 1},
        expression={},
    )
    assertSuccess(result, [], msg="empty collection produces no documents")
