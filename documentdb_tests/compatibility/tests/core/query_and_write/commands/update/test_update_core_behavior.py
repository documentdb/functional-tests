"""Tests for update command core behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import (
    assertProperties,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import NotExists
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import BSON_TYPE_SAMPLES, BsonType


@dataclass(frozen=True)
class UpdateCoreTest(BaseTestCase):
    """Test case for update command core behavior."""

    setup_docs: Any = None
    updates: Any = None
    expected_n: int = 0
    expected_n_modified: int = 0
    expected_docs: Any = None


def run_update_and_verify(collection, test: UpdateCoreTest):
    """Insert docs, run update command, return result."""
    if test.setup_docs:
        if isinstance(test.setup_docs, list):
            collection.insert_many(test.setup_docs)
        else:
            collection.insert_one(test.setup_docs)
    return execute_command(
        collection,
        {"update": collection.name, "updates": test.updates},
    )


# Property [Result Metadata]: update command reports correct n and nModified for
# match, no-match, no-op, single, and multi-document scenarios.
RESULT_TESTS: list[UpdateCoreTest] = [
    UpdateCoreTest(
        "single_match_modify",
        setup_docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        updates=[{"q": {"_id": 1}, "u": {"$set": {"x": 10}}}],
        expected_n=1,
        expected_n_modified=1,
        msg="update should report n=1, nModified=1 when one doc matched and changed.",
    ),
    UpdateCoreTest(
        "no_match",
        setup_docs={"_id": 1, "x": 1},
        updates=[{"q": {"_id": 999}, "u": {"$set": {"x": 10}}}],
        expected_n=0,
        expected_n_modified=0,
        msg="update should report n=0, nModified=0 when no documents match.",
    ),
    UpdateCoreTest(
        "empty_collection",
        setup_docs=None,
        updates=[{"q": {"x": 1}, "u": {"$set": {"x": 10}}}],
        expected_n=0,
        expected_n_modified=0,
        msg="update should report n=0, nModified=0 on empty collection.",
    ),
    UpdateCoreTest(
        "set_to_current_value_no_modify",
        setup_docs={"_id": 1, "x": 5},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"x": 5}}}],
        expected_n=1,
        expected_n_modified=0,
        msg="update should report nModified=0 when $set value equals current value.",
    ),
    UpdateCoreTest(
        "set_to_new_value",
        setup_docs={"_id": 1, "x": 5},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"x": 99}}}],
        expected_n=1,
        expected_n_modified=1,
        msg="update should report nModified=1 when $set changes value.",
    ),
    UpdateCoreTest(
        "multi_true_updates_all",
        setup_docs=[{"_id": 1, "s": "A"}, {"_id": 2, "s": "A"}, {"_id": 3, "s": "B"}],
        updates=[{"q": {"s": "A"}, "u": {"$set": {"s": "C"}}, "multi": True}],
        expected_n=2,
        expected_n_modified=2,
        msg="update with multi:true should modify all matching documents.",
    ),
    UpdateCoreTest(
        "multi_false_updates_one",
        setup_docs=[{"_id": 1, "s": "A"}, {"_id": 2, "s": "A"}, {"_id": 3, "s": "A"}],
        updates=[{"q": {"s": "A"}, "u": {"$set": {"s": "X"}}}],
        expected_n=1,
        expected_n_modified=1,
        # Which document is modified is non-deterministic without a sort; only the
        # count is asserted here intentionally.
        msg="update with multi:false should modify at most one document.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESULT_TESTS))
def test_update_core_results(collection, test: UpdateCoreTest):
    """Test update command reports correct result metadata."""
    result = run_update_and_verify(collection, test)
    assertSuccess(
        result,
        {"ok": 1.0, "n": test.expected_n, "nModified": test.expected_n_modified},
        raw_res=True,
        msg=test.msg,
    )


# Property [Document State]: update command produces correct final document state
# including field creation via dot notation, array values, and no-match leaving
# documents unchanged.
DOC_TESTS: list[UpdateCoreTest] = [
    UpdateCoreTest(
        "no_match_leaves_docs_unchanged",
        setup_docs={"_id": 1, "x": 1},
        updates=[{"q": {"_id": 999}, "u": {"$set": {"x": 99}}}],
        expected_docs=[{"_id": 1, "x": 1}],
        msg="update with no matching document should leave existing docs unchanged.",
    ),
    UpdateCoreTest(
        "creates_nested_via_dot_notation",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"a.b.c": 42}}}],
        expected_docs=[{"_id": 1, "a": {"b": {"c": 42}}}],
        msg="update should create nested subdocument fields via dot notation.",
    ),
    UpdateCoreTest(
        "sets_array_field",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"arr": [1, 2, 3]}}}],
        expected_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="update should set a field to an array value.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOC_TESTS))
def test_update_core_docs(collection, test: UpdateCoreTest):
    """Test update command produces correct document state."""
    run_update_and_verify(collection, test)
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected_docs, msg=test.msg)


def test_update_on_non_existent_collection(database_client):
    """Test update on non-existent collection returns n:0, nModified:0."""
    coll = database_client["nonexistent_coll"]
    result = execute_command(
        coll,
        {"update": coll.name, "updates": [{"q": {"x": 1}, "u": {"$set": {"x": 10}}}]},
    )
    assertSuccess(result, {"ok": 1.0, "n": 0, "nModified": 0}, raw_res=True)


# Property [Success Response Shape]: update command success response contains ok, n,
# nModified, and no writeErrors or writeConcernError fields.
def test_update_success_response_fields(collection):
    """Test update success response contains expected ok, n, nModified fields."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}]},
    )
    assertSuccessPartial(result, {"ok": 1.0, "n": 1, "nModified": 1})


def test_update_success_response_no_write_errors(collection):
    """Test update success response has no writeErrors field."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}]},
    )
    assertProperties(result, {"writeErrors": NotExists()}, raw_res=True)


def test_update_success_response_no_write_concern_error(collection):
    """Test update success response has no writeConcernError field."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}]},
    )
    assertProperties(result, {"writeConcernError": NotExists()}, raw_res=True)


# Property [BSON Type Pass-Through]: $set must store and round-trip every BSON type
# without coercion or data loss.
# PyMongo coerces Binary subtype 0 to plain bytes on read, so the expected value
# for bin_data must be raw bytes even though the stored value is Binary.
_BSON_TYPE_PASSTHROUGH_PARAMS = [
    pytest.param(
        bson_type,
        value,
        b"\x00\x01\x02" if bson_type == BsonType.BIN_DATA else value,
        id=bson_type.value,
    )
    for bson_type, value in BSON_TYPE_SAMPLES.items()
]


@pytest.mark.parametrize("bson_type,value,expected", _BSON_TYPE_PASSTHROUGH_PARAMS)
def test_update_set_bson_type_passthrough(
    collection, bson_type: BsonType, value: Any, expected: Any
):
    """Test $set preserves each BSON type exactly when read back via find."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"v": value}}}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "v": expected}],
        msg=f"$set should preserve {bson_type.value} without coercion.",
    )
