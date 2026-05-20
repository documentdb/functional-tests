"""Tests for sparse index behavior with other commands — count hint and edge cases."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

QUERY_DOCS = (
    {"_id": 1, "a": 1},
    {"_id": 2, "a": 2},
    {"_id": 3},
    {"_id": 4, "a": None},
)

SPARSE_COUNT_HINT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="hint_returns_fewer_results",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        doc=QUERY_DOCS,
        expected={"n": 3, "ok": 1.0},
        command_options={"query": {}, "hint": {"a": 1}},
        msg="Hint with sparse index on empty query returns fewer results than total",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_COUNT_HINT_TESTS))
def test_sparse_count_hint(collection, test):
    """Test sparse index count behavior when hint forces sparse index usage."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    if test.doc:
        collection.insert_many(list(test.doc))
    cmd = {"count": collection.name}
    if "query" in test.command_options:
        cmd["query"] = test.command_options["query"]
    if "hint" in test.command_options:
        cmd["hint"] = test.command_options["hint"]
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, raw_res=True)


SPARSE_EDGE_COUNT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="on_id_field_has_no_effect",
        indexes=({"key": {"_id": 1}, "name": "idx_id_sparse", "sparse": True},),
        doc=({"_id": 1}, {"_id": 2}, {"_id": 3}),
        expected={"n": 3, "ok": 1.0},
        command_options={"query": {}, "hint": {"_id": 1}},
        msg="Sparse index on _id field — _id always exists, so sparse has no effect",
    ),
    IndexTestCase(
        id="mixed_type_array",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        doc=({"_id": 1, "a": [1, "two", None, True]}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"query": {}, "hint": {"a": 1}},
        msg="Sparse index on field that contains arrays of mixed types",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_EDGE_COUNT_TESTS))
def test_sparse_edge_case(collection, test):
    """Test sparse index edge cases."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    if test.doc:
        collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"count": collection.name, **test.command_options},
    )
    assertSuccess(result, test.expected, raw_res=True)
