"""
Tests for $documentNumber order dependence and partition semantics.

$documentNumber is order-dependent: positions are assigned in sortBy order, so
reversing the sort direction or sorting on a different field produces different
numbers for the same documents. Positions restart at 1 in every partition. Each
document in the partition gets assigned a unique document number.
"""

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    BASIC_DOCS,
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

# Property [Order Dependence]: changing sortBy changes the assigned positions.


def test_documentNumber_ascending_sort(collection):
    """Ascending sort assigns positions in ascending order of the sort field."""
    result = run_window_operator(
        collection,
        "$documentNumber",
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
    assertSuccess(result, expected, msg="ascending sort numbers documents 1..5 in _id order")


def test_documentNumber_descending_sort(collection):
    """Descending sort reverses the assigned positions — order-dependent operator."""
    result = run_window_operator(
        collection,
        "$documentNumber",
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
        msg="descending sort reverses positions — different result than ascending",
    )


def test_documentNumber_sort_on_different_field(collection):
    """Sorting on a different field assigns positions by that field's order."""
    docs = [
        {"_id": 1, "partition": "A", "value": 50},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
        docs,
        sort_by={"value": 1},
        expression={},
    )
    expected = [
        {"_id": 2, "partition": "A", "value": 10, "result": 1},
        {"_id": 3, "partition": "A", "value": 30, "result": 2},
        {"_id": 1, "partition": "A", "value": 50, "result": 3},
    ]
    assertSuccess(result, expected, msg="output follows the value sort order; positions 1..3 by value")


# Property [Partition Isolation]: numbering restarts at 1 in each partition.


def test_documentNumber_restarts_per_partition(collection):
    """Each partition is numbered independently starting from 1."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "B", "value": 30},
        {"_id": 4, "partition": "B", "value": 40},
        {"_id": 5, "partition": "B", "value": 50},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
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
    assertSuccess(result, expected, msg="numbering restarts at 1 in each partition")


def test_documentNumber_without_partitionBy(collection):
    """Omitting partitionBy treats the whole collection as a single partition."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "B", "value": 20},
        {"_id": 3, "partition": "C", "value": 30},
    ]
    result = run_window_operator(
        collection,
        "$documentNumber",
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
        result, expected, msg="omitted partitionBy numbers the whole collection continuously"
    )


# Property [Empty and Single-Document Input]: smallest partition sizes number correctly.


def test_documentNumber_single_document_partition(collection):
    """A single-document partition gets position 1."""
    result = run_window_operator(
        collection,
        "$documentNumber",
        [{"_id": 1, "partition": "A", "value": 10}],
        sort_by={"_id": 1},
        expression={},
    )
    assertSuccess(
        result,
        [{"_id": 1, "partition": "A", "value": 10, "result": 1}],
        msg="single-document partition gets 1",
    )


def test_documentNumber_empty_collection(collection):
    """$documentNumber on an empty collection returns no documents without error."""
    result = run_window_operator(
        collection,
        "$documentNumber",
        [],
        sort_by={"_id": 1},
        expression={},
    )
    assertSuccess(result, [], msg="empty collection produces no documents")
