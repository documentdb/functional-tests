"""
Tests for $documentNumber order dependence and partition semantics.

$documentNumber is order-dependent: positions are assigned in sortBy order, so
reversing the sort direction or sorting on a different field produces different
numbers for the same documents. Positions restart at 1 in every partition. Each
document in the partition gets assigned a unique document number.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

SORTED_PROJECTION = [{"$sort": {"_id": 1}}, {"$project": {"_id": 1, "docNumber": 1}}]

BASIC_DOCS = [
    {"_id": 1, "partition": "A", "value": 10},
    {"_id": 2, "partition": "A", "value": 20},
    {"_id": 3, "partition": "A", "value": 30},
    {"_id": 4, "partition": "A", "value": 40},
    {"_id": 5, "partition": "A", "value": 50},
]


def run_document_number(collection, docs, sort_by, partition_by="$partition", extra_stages=None):
    """Insert docs and run $documentNumber, optionally omitting partitionBy."""
    if docs:
        collection.insert_many([dict(d) for d in docs])

    stage = {"sortBy": sort_by, "output": {"docNumber": {"$documentNumber": {}}}}
    if partition_by is not None:
        stage["partitionBy"] = partition_by

    pipeline = [{"$setWindowFields": stage}]
    pipeline.extend(SORTED_PROJECTION if extra_stages is None else extra_stages)

    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )


# Property [Order Dependence]: changing sortBy changes the assigned positions.


def test_documentNumber_ascending_sort(collection):
    """Ascending sort assigns positions in ascending order of the sort field."""
    result = run_document_number(collection, BASIC_DOCS, {"_id": 1})
    expected = [
        {"_id": 1, "docNumber": 1},
        {"_id": 2, "docNumber": 2},
        {"_id": 3, "docNumber": 3},
        {"_id": 4, "docNumber": 4},
        {"_id": 5, "docNumber": 5},
    ]
    assertSuccess(result, expected, msg="ascending sort numbers documents 1..5 in _id order")


def test_documentNumber_descending_sort(collection):
    """Descending sort reverses the assigned positions — order-dependent operator."""
    result = run_document_number(collection, BASIC_DOCS, {"_id": -1})
    expected = [
        {"_id": 1, "docNumber": 5},
        {"_id": 2, "docNumber": 4},
        {"_id": 3, "docNumber": 3},
        {"_id": 4, "docNumber": 2},
        {"_id": 5, "docNumber": 1},
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
    result = run_document_number(collection, docs, {"value": 1})
    expected = [
        {"_id": 1, "docNumber": 3},
        {"_id": 2, "docNumber": 1},
        {"_id": 3, "docNumber": 2},
    ]
    assertSuccess(result, expected, msg="positions follow the value sort order, not _id order")


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
    result = run_document_number(collection, docs, {"_id": 1})
    expected = [
        {"_id": 1, "docNumber": 1},
        {"_id": 2, "docNumber": 2},
        {"_id": 3, "docNumber": 1},
        {"_id": 4, "docNumber": 2},
        {"_id": 5, "docNumber": 3},
    ]
    assertSuccess(result, expected, msg="numbering restarts at 1 in each partition")


def test_documentNumber_without_partitionBy(collection):
    """Omitting partitionBy treats the whole collection as a single partition."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "B", "value": 20},
        {"_id": 3, "partition": "C", "value": 30},
    ]
    result = run_document_number(collection, docs, {"_id": 1}, partition_by=None)
    expected = [
        {"_id": 1, "docNumber": 1},
        {"_id": 2, "docNumber": 2},
        {"_id": 3, "docNumber": 3},
    ]
    assertSuccess(
        result, expected, msg="omitted partitionBy numbers the whole collection continuously"
    )


# Property [Empty and Single-Document Input]: smallest partition sizes number correctly.


def test_documentNumber_single_document_partition(collection):
    """A single-document partition gets position 1."""
    result = run_document_number(
        collection, [{"_id": 1, "partition": "A", "value": 10}], {"_id": 1}
    )
    assertSuccess(result, [{"_id": 1, "docNumber": 1}], msg="single-document partition gets 1")


def test_documentNumber_empty_collection(collection):
    """$documentNumber on an empty collection returns no documents without error."""
    result = run_document_number(collection, [], {"_id": 1})
    assertSuccess(result, [], msg="empty collection produces no documents")
