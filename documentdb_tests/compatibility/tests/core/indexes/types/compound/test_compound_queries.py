"""Tests for compound index query behavior.

Validates prefix queries, sort matching, projections, hints,
nested/embedded fields, multikey, and null/missing field handling.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

_PREFIX_DOCS = (
    {"_id": 1, "a": 1, "b": 10, "c": 100},
    {"_id": 2, "a": 1, "b": 20, "c": 200},
    {"_id": 3, "a": 2, "b": 10, "c": 300},
    {"_id": 4, "a": 2, "b": 20, "c": 400},
    {"_id": 5, "a": 3, "b": 30, "c": 500},
)

PREFIX_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="prefix_first_field",
        indexes=({"key": {"a": 1, "b": -1, "c": 1}, "name": "abc"},),
        doc=_PREFIX_DOCS,
        filter={"a": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1, "b": 10, "c": 100}, {"_id": 2, "a": 1, "b": 20, "c": 200}],
        msg="Query on prefix field a should work",
    ),
    IndexQueryTestCase(
        id="prefix_first_two_fields",
        indexes=({"key": {"a": 1, "b": -1, "c": 1}, "name": "abc"},),
        doc=_PREFIX_DOCS,
        filter={"a": 1, "b": 10},
        expected=[{"_id": 1, "a": 1, "b": 10, "c": 100}],
        msg="Query on prefix fields a,b should work",
    ),
    IndexQueryTestCase(
        id="prefix_all_fields",
        indexes=({"key": {"a": 1, "b": -1, "c": 1}, "name": "abc"},),
        doc=_PREFIX_DOCS,
        filter={"a": 2, "b": 20, "c": 400},
        expected=[{"_id": 4, "a": 2, "b": 20, "c": 400}],
        msg="Query on all fields should work",
    ),
    IndexQueryTestCase(
        id="prefix_skip_first_field",
        indexes=({"key": {"a": 1, "b": -1, "c": 1}, "name": "abc"},),
        doc=_PREFIX_DOCS,
        filter={"b": 10},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1, "b": 10, "c": 100}, {"_id": 3, "a": 2, "b": 10, "c": 300}],
        msg="Query on non-prefix field still returns correct results",
    ),
    IndexQueryTestCase(
        id="prefix_range_on_first_field",
        indexes=({"key": {"a": 1, "b": -1, "c": 1}, "name": "abc"},),
        doc=_PREFIX_DOCS,
        filter={"a": {"$gt": 1}, "b": 10},
        sort={"_id": 1},
        expected=[{"_id": 3, "a": 2, "b": 10, "c": 300}],
        msg="Range on prefix field with equality on next field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PREFIX_QUERY_TESTS))
def test_compound_prefix_query(collection, test):
    """Test compound index prefix query behavior."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter}
    if test.sort:
        cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


_SORT_DOCS = (
    {"_id": 1, "a": 1, "b": 10},
    {"_id": 2, "a": 1, "b": 20},
    {"_id": 3, "a": 2, "b": 5},
)

SORT_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="sort_exact_match",
        indexes=({"key": {"a": 1, "b": -1}, "name": "a_1_b_neg1"},),
        doc=_SORT_DOCS,
        filter={},
        sort={"a": 1, "b": -1},
        expected=[
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 3, "a": 2, "b": 5},
        ],
        msg="Sort matching index exactly",
    ),
    IndexQueryTestCase(
        id="sort_reverse_match",
        indexes=({"key": {"a": 1, "b": -1}, "name": "a_1_b_neg1"},),
        doc=_SORT_DOCS,
        filter={},
        sort={"a": -1, "b": 1},
        expected=[
            {"_id": 3, "a": 2, "b": 5},
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 1, "b": 20},
        ],
        msg="Sort matching index in reverse",
    ),
    IndexQueryTestCase(
        id="sort_not_satisfiable_by_index",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        doc=_SORT_DOCS,
        filter={},
        sort={"a": 1, "b": -1},
        expected=[
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 3, "a": 2, "b": 5},
        ],
        msg="Sort not satisfiable by index still returns correct results",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SORT_TESTS))
def test_compound_sort(collection, test):
    """Test compound index sort order matching."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter, "sort": test.sort}
    )
    assertSuccess(result, test.expected, msg=test.msg)


NESTED_FIELD_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="embedded_fields",
        indexes=({"key": {"a.x": 1, "a.y": 1}, "name": "ax_ay"},),
        doc=({"_id": 1, "a": {"x": 1, "y": 10}}, {"_id": 2, "a": {"x": 2, "y": 20}}),
        filter={"a.x": 1, "a.y": 10},
        expected=[{"_id": 1, "a": {"x": 1, "y": 10}}],
        msg="Compound on embedded fields works",
    ),
    IndexQueryTestCase(
        id="mixed_top_and_embedded",
        indexes=({"key": {"a": 1, "b.c": 1}, "name": "a_bc"},),
        doc=({"_id": 1, "a": 1, "b": {"c": 10}}, {"_id": 2, "a": 2, "b": {"c": 20}}),
        filter={"a": 1, "b.c": 10},
        expected=[{"_id": 1, "a": 1, "b": {"c": 10}}],
        msg="Mixed top-level and embedded works",
    ),
    IndexQueryTestCase(
        id="multikey_one_array_field",
        indexes=({"key": {"tags": 1, "category": 1}, "name": "tags_cat"},),
        doc=({"_id": 1, "tags": [1, 2], "category": "a"},),
        filter={"tags": 2, "category": "a"},
        expected=[{"_id": 1, "tags": [1, 2], "category": "a"}],
        msg="Multikey compound query works",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_FIELD_QUERY_TESTS))
def test_compound_nested_field_query(collection, test):
    """Test compound index nested field and multikey queries."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


NULL_MISSING_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="null_first_field",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        doc=({"_id": 1, "a": None, "b": 5},),
        filter={"a": None, "b": 5},
        expected=[{"_id": 1, "a": None, "b": 5}],
        msg="Null in first field is indexed",
    ),
    IndexQueryTestCase(
        id="null_second_field",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        doc=({"_id": 1, "a": 5, "b": None},),
        filter={"a": 5, "b": None},
        expected=[{"_id": 1, "a": 5, "b": None}],
        msg="Null in second field is indexed",
    ),
    IndexQueryTestCase(
        id="missing_first_field",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        doc=({"_id": 1, "b": 5},),
        filter={"a": None},
        expected=[{"_id": 1, "b": 5}],
        msg="Missing first field treated as null",
    ),
    IndexQueryTestCase(
        id="missing_second_field",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        doc=({"_id": 1, "a": 5},),
        filter={"a": 5, "b": None},
        expected=[{"_id": 1, "a": 5}],
        msg="Missing second field treated as null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_MISSING_QUERY_TESTS))
def test_compound_null_missing_query(collection, test):
    """Test compound index null/missing field query behavior."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_compound_partial_sort_with_equality(collection):
    """Test query with equality on prefix allows sort on next field."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1, "c": 1}, "name": "abc"}],
        },
    )
    collection.insert_many(
        [
            {"_id": 1, "a": 5, "b": 3, "c": 10},
            {"_id": 2, "a": 5, "b": 1, "c": 20},
            {"_id": 3, "a": 5, "b": 2, "c": 30},
            {"_id": 4, "a": 9, "b": 1, "c": 40},
        ]
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": 5}, "sort": {"b": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 2, "a": 5, "b": 1, "c": 20},
            {"_id": 3, "a": 5, "b": 2, "c": 30},
            {"_id": 1, "a": 5, "b": 3, "c": 10},
        ],
        msg="Equality on a allows sort on b",
    )


def test_compound_multi_field_sort_after_equality(collection):
    """Test equality on prefix allows multi-field sort on remaining fields."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1, "c": 1}, "name": "abc"}],
        },
    )
    collection.insert_many(
        [
            {"_id": 1, "a": 5, "b": 2, "c": 30},
            {"_id": 2, "a": 5, "b": 1, "c": 20},
            {"_id": 3, "a": 5, "b": 1, "c": 10},
            {"_id": 4, "a": 9, "b": 1, "c": 5},
        ]
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": 5}, "sort": {"b": 1, "c": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 3, "a": 5, "b": 1, "c": 10},
            {"_id": 2, "a": 5, "b": 1, "c": 20},
            {"_id": 1, "a": 5, "b": 2, "c": 30},
        ],
        msg="Equality on a allows sort on b,c",
    )
