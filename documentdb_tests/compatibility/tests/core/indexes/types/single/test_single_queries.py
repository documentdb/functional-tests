"""Tests for single field index query behavior.

Validates equality queries on various field types, null/missing field indexing,
sort order, descending index queries, and hint usage.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


FIELD_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="field_top_level_query",
        indexes=({"key": {"score": 1}, "name": "score_1"},),
        doc=({"_id": 1, "score": 10}, {"_id": 2, "score": 20}, {"_id": 3, "score": 30}),
        filter={"score": 20},
        expected=[{"_id": 2, "score": 20}],
        msg="Should find document by indexed field",
    ),
    IndexQueryTestCase(
        id="field_embedded_query",
        indexes=({"key": {"address.city": 1}, "name": "address.city_1"},),
        doc=(
            {"_id": 1, "address": {"city": "NYC", "zip": "10001"}},
            {"_id": 2, "address": {"city": "LA", "zip": "90001"}},
        ),
        filter={"address.city": "NYC"},
        expected=[{"_id": 1, "address": {"city": "NYC", "zip": "10001"}}],
        msg="Should find by embedded field",
    ),
    IndexQueryTestCase(
        id="field_embedded_document_query",
        indexes=({"key": {"address": 1}, "name": "address_1"},),
        doc=(
            {"_id": 1, "address": {"city": "NYC", "zip": "10001"}},
            {"_id": 2, "address": {"city": "LA", "zip": "90001"}},
        ),
        filter={"address": {"city": "NYC", "zip": "10001"}},
        expected=[{"_id": 1, "address": {"city": "NYC", "zip": "10001"}}],
        msg="Should match entire embedded document",
    ),
    IndexQueryTestCase(
        id="field_embedded_document_order_matters",
        indexes=({"key": {"address": 1}, "name": "address_1"},),
        doc=({"_id": 1, "address": {"city": "NYC", "zip": "10001"}},),
        filter={"address": {"zip": "10001", "city": "NYC"}},
        expected=[],
        msg="Different field order should not match embedded document",
    ),
    IndexQueryTestCase(
        id="null_value_indexed",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": None}, {"_id": 2, "a": 5}),
        filter={"a": None},
        expected=[{"_id": 1, "a": None}],
        msg="Should find document with null value",
    ),
    IndexQueryTestCase(
        id="missing_field_as_null",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "b": 10}, {"_id": 2, "a": 5}),
        filter={"a": None},
        expected=[{"_id": 1, "b": 10}],
        msg="Missing field treated as null in query",
    ),
    IndexQueryTestCase(
        id="in_query",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}),
        filter={"a": {"$in": [1, 3]}},
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="$in query should find matching documents",
    ),
    IndexQueryTestCase(
        id="ne_query",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}),
        filter={"a": {"$ne": 2}},
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="$ne query should exclude matching documents",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_QUERY_TESTS))
def test_single_field_query(collection, test):
    """Test single field index queries on various field types."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": test.indexes[0]["name"]}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


SORT_ORDER_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="sort_ascending_index_ascending",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": 3}, {"_id": 2, "a": 1}, {"_id": 3, "a": 2}),
        sort={"a": 1},
        expected=[{"_id": 2, "a": 1}, {"_id": 3, "a": 2}, {"_id": 1, "a": 3}],
        msg="Ascending index supports ascending sort",
    ),
    IndexQueryTestCase(
        id="sort_ascending_index_descending",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": 3}, {"_id": 2, "a": 1}, {"_id": 3, "a": 2}),
        sort={"a": -1},
        expected=[{"_id": 1, "a": 3}, {"_id": 3, "a": 2}, {"_id": 2, "a": 1}],
        msg="Ascending index supports descending sort via reverse scan",
    ),
    IndexQueryTestCase(
        id="sort_filter_and_sort",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": 5}, {"_id": 2, "a": 3}, {"_id": 3, "a": 7}, {"_id": 4, "a": 1}),
        filter={"a": {"$gt": 2}},
        sort={"a": 1},
        expected=[{"_id": 2, "a": 3}, {"_id": 1, "a": 5}, {"_id": 3, "a": 7}],
        msg="Index supports both filter and sort on same field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SORT_ORDER_TESTS))
def test_single_sort_order(collection, test):
    """Test single field index sort order behavior."""
    collection.insert_many(list(test.doc))
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    cmd = {"find": collection.name, "hint": test.indexes[0]["name"]}
    if test.filter:
        cmd["filter"] = test.filter
    cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


DESCENDING_INDEX_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="descending_equality",
        indexes=({"key": {"a": -1}, "name": "a_neg1"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 10}),
        filter={"a": 5},
        expected=[{"_id": 2, "a": 5}],
        msg="Descending index should support equality query",
    ),
    IndexQueryTestCase(
        id="descending_range_gt",
        indexes=({"key": {"a": -1}, "name": "a_neg1"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 10}),
        filter={"a": {"$gt": 3}},
        expected=[{"_id": 2, "a": 5}, {"_id": 3, "a": 10}],
        msg="Descending index should support $gt range query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DESCENDING_INDEX_TESTS))
def test_single_descending_index(collection, test):
    """Test descending single field index query behavior."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": test.indexes[0]["name"]}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


HINT_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="hint_by_name",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": 10}, {"_id": 2, "a": 20}),
        filter={"a": 10},
        hint="a_1",
        expected=[{"_id": 1, "a": 10}],
        msg="Hint by index name should return correct results",
    ),
    IndexQueryTestCase(
        id="hint_by_key",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        doc=({"_id": 1, "a": 10}, {"_id": 2, "a": 20}),
        filter={"a": 10},
        hint={"a": 1},
        expected=[{"_id": 1, "a": 10}],
        msg="Hint by key pattern should return correct results",
    ),
]


@pytest.mark.parametrize("test", pytest_params(HINT_TESTS))
def test_single_hint_usage(collection, test):
    """Test single field index with hint."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter, "hint": test.hint},
    )
    assertSuccess(result, test.expected, msg=test.msg)
