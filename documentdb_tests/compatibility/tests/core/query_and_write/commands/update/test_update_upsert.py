"""Tests for update command upsert behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class UpsertDocTest(BaseTestCase):
    """Test case for upsert document state verification."""

    setup_docs: Any = None
    updates: Any = None
    find_filter: Any = None
    expected_docs: Any = None


def run_upsert(collection, test: UpsertDocTest):
    """Insert optional setup docs, run update, return find result."""
    if test.setup_docs:
        collection.insert_one(test.setup_docs)
    execute_command(collection, {"update": collection.name, "updates": test.updates})
    return execute_command(collection, {"find": collection.name, "filter": test.find_filter})


# Property [Upsert Document Creation]: upsert extracts equality fields from query,
# ignores range operators, creates nested docs from dotted fields, and applies operators.
DOC_TESTS: list[UpsertDocTest] = [
    UpsertDocTest(
        "extracts_equality_fields",
        updates=[{"q": {"_id": 1, "a": 1, "b": 2}, "u": {"$set": {"c": 3}}, "upsert": True}],
        find_filter={"_id": 1},
        expected_docs=[{"_id": 1, "a": 1, "b": 2, "c": 3}],
        msg="upsert should extract equality fields from query into new doc.",
    ),
    UpsertDocTest(
        "range_query_not_extracted",
        updates=[{"q": {"_id": 1, "x": {"$gt": 5}}, "u": {"$set": {"y": 1}}, "upsert": True}],
        find_filter={"_id": 1},
        expected_docs=[{"_id": 1, "y": 1}],
        msg="upsert should not extract range ($gt) fields into new doc.",
    ),
    UpsertDocTest(
        "id_in_query_used",
        updates=[{"q": {"_id": 42}, "u": {"$set": {"x": 1}}, "upsert": True}],
        find_filter={"_id": 42},
        expected_docs=[{"_id": 42, "x": 1}],
        msg="upsert should use _id from query for new doc.",
    ),
    UpsertDocTest(
        "dotted_field_creates_nested",
        updates=[{"q": {"_id": 1, "a.b": 5}, "u": {"$set": {"c": 1}}, "upsert": True}],
        find_filter={"_id": 1},
        expected_docs=[{"_id": 1, "a": {"b": 5}, "c": 1}],
        msg="upsert should create nested doc from dotted field in query.",
    ),
    UpsertDocTest(
        "with_replacement",
        updates=[{"q": {"_id": 1}, "u": {"x": 10, "y": 20}, "upsert": True}],
        find_filter={"_id": 1},
        expected_docs=[{"_id": 1, "x": 10, "y": 20}],
        msg="upsert with replacement should create doc from replacement fields.",
    ),
    UpsertDocTest(
        "setOnInsert_applies_on_insert",
        updates=[{"q": {"_id": 1}, "u": {"$setOnInsert": {"a": 1, "b": 2}}, "upsert": True}],
        find_filter={"_id": 1},
        expected_docs=[{"_id": 1, "a": 1, "b": 2}],
        msg="$setOnInsert should set fields when upsert inserts a new doc.",
    ),
    UpsertDocTest(
        "setOnInsert_ignored_on_match",
        setup_docs={"_id": 1, "x": 10},
        updates=[{"q": {"_id": 1}, "u": {"$setOnInsert": {"a": 99}}, "upsert": True}],
        find_filter={"_id": 1},
        expected_docs=[{"_id": 1, "x": 10}],
        msg="$setOnInsert should not apply when document already exists.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOC_TESTS))
def test_update_upsert_docs(collection, test: UpsertDocTest):
    """Test upsert produces correct document state."""
    result = run_upsert(collection, test)
    assertSuccess(result, test.expected_docs, msg=test.msg)


# Property [Upsert Response]: upsert reports correct response metadata including
# n, nModified, and upserted array with index and _id.
def test_update_upsert_response_insert(collection):
    """Test upsert response when inserting new document."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 99}, "u": {"$set": {"x": 1}}, "upsert": True}],
        },
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "n": 1, "nModified": 0, "upserted": [{"index": 0, "_id": 99}]}
    )


def test_update_upsert_response_update(collection):
    """Test upsert response when matching existing document."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 99}}, "upsert": True}],
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 1, "nModified": 1}, raw_res=True)


def test_update_setOnInsert_without_upsert_noop(collection):
    """Test $setOnInsert without upsert:true does nothing on no match."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$setOnInsert": {"a": 1}}}],
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 0, "nModified": 0}, raw_res=True)
