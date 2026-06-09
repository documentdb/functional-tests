"""Tests for update command replacement document mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR, IMMUTABLE_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ReplaceTest(BaseTestCase):
    """Test case for replacement document behavior."""

    setup_docs: Any = None
    updates: Any = None
    expected_docs: Any = None


def run_replace(collection, test: ReplaceTest):
    """Insert docs and run update command."""
    if isinstance(test.setup_docs, list):
        collection.insert_many(test.setup_docs)
    else:
        collection.insert_one(test.setup_docs)
    execute_command(collection, {"update": collection.name, "updates": test.updates})
    return execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})


# Property [Replacement Semantics]: replacement document replaces all fields except _id,
# preserves _id from original, and empty replacement clears all non-_id fields.
TESTS: list[ReplaceTest] = [
    ReplaceTest(
        "replaces_all_fields",
        setup_docs={"_id": 1, "a": 1, "b": 2, "c": 3},
        updates=[{"q": {"_id": 1}, "u": {"x": 99, "y": 100}}],
        expected_docs=[{"_id": 1, "x": 99, "y": 100}],
        msg="update should replace all fields except _id with replacement doc.",
    ),
    ReplaceTest(
        "preserves_id",
        setup_docs={"_id": 1, "name": "old"},
        updates=[{"q": {"_id": 1}, "u": {"name": "new"}}],
        expected_docs=[{"_id": 1, "name": "new"}],
        msg="update should preserve _id from original document.",
    ),
    ReplaceTest(
        "empty_replacement_clears_fields",
        setup_docs={"_id": 1, "a": 1, "b": 2},
        updates=[{"q": {"_id": 1}, "u": {}}],
        expected_docs=[{"_id": 1}],
        msg="update with empty replacement should remove all fields except _id.",
    ),
    ReplaceTest(
        "matching_id_succeeds",
        setup_docs={"_id": 1, "a": 1},
        updates=[{"q": {"_id": 1}, "u": {"_id": 1, "b": 2}}],
        expected_docs=[{"_id": 1, "b": 2}],
        msg="update with _id matching original should succeed.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_update_replacement(collection, test: ReplaceTest):
    """Test replacement document produces correct final state."""
    result = run_replace(collection, test)
    assertSuccess(result, test.expected_docs, msg=test.msg)


@dataclass(frozen=True)
class ReplaceErrorTest(BaseTestCase):
    """Test case for replacement document error scenarios."""

    setup_docs: Any = None
    updates: Any = None


# Property [Replacement Errors]: replacement document rejects _id mismatch, operator
# keys mixed with plain fields, and multi:true with replacement.
ERROR_TESTS: list[ReplaceErrorTest] = [
    ReplaceErrorTest(
        "different_id_errors",
        setup_docs={"_id": 1, "a": 1},
        updates=[{"q": {"_id": 1}, "u": {"_id": 2, "b": 2}}],
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="update should reject replacement with _id different from matched doc.",
    ),
    ReplaceErrorTest(
        "multi_true_with_replacement_errors",
        setup_docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 1}],
        updates=[{"q": {"a": 1}, "u": {"b": 2}, "multi": True}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="update should reject multi:true with replacement document.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_update_replacement_errors(collection, test: ReplaceErrorTest):
    """Test replacement document error cases."""
    if isinstance(test.setup_docs, list):
        collection.insert_many(test.setup_docs)
    else:
        collection.insert_one(test.setup_docs)
    result = execute_command(collection, {"update": collection.name, "updates": test.updates})
    assertResult(result, error_code=test.error_code, msg=test.msg)


def test_update_replacement_always_counts_as_modified(collection):
    """Test replacement with identical content still reports nModified:1."""
    collection.insert_one({"_id": 1, "x": 5, "y": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"x": 5, "y": 10}}]},
    )
    assertSuccess(result, {"ok": 1.0, "n": 1, "nModified": 1}, raw_res=True)
