"""Tests for $bit update operator result metadata and upsert behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class BitResultTest(BaseTestCase):
    """Test case for $bit result metadata."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None
    expected_n: int = 0
    expected_n_modified: int = 0


@dataclass(frozen=True)
class BitUpsertTest(BaseTestCase):
    """Test case for $bit upsert behavior."""

    query: Any = None
    update: Any = None
    expected_doc: Any = None


# Property [Result Metadata]: $bit reports correct n and nModified values for match,
# no-match, no-op (identity), and empty operand scenarios.
RESULT_TESTS: list[BitResultTest] = [
    BitResultTest(
        "match_and_modify",
        setup_docs=[{"_id": 1, "v": 15}],
        query={"_id": 1},
        update={"$bit": {"v": {"and": 7}}},
        expected_n=1,
        expected_n_modified=1,
        msg="$bit should report nModified=1 when value changes.",
    ),
    BitResultTest(
        "match_no_modify_identity",
        setup_docs=[{"_id": 1, "v": 15}],
        query={"_id": 1},
        update={"$bit": {"v": {"and": -1}}},
        expected_n=1,
        expected_n_modified=0,
        msg="$bit should report nModified=0 when AND -1 is identity (no change).",
    ),
    BitResultTest(
        "no_match",
        setup_docs=[{"_id": 1, "v": 5}],
        query={"_id": 99},
        update={"$bit": {"v": {"or": 1}}},
        expected_n=0,
        expected_n_modified=0,
        msg="$bit should report n=0 when no document matches.",
    ),
    BitResultTest(
        "empty_bit_noop",
        setup_docs=[{"_id": 1, "v": 10}],
        query={"_id": 1},
        update={"$bit": {}},
        expected_n=1,
        expected_n_modified=0,
        msg="$bit should report nModified=0 for empty $bit object.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESULT_TESTS))
def test_bit_result_metadata(collection, test: BitResultTest):
    """Test $bit update result metadata."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": test.expected_n, "nModified": test.expected_n_modified, "ok": 1.0},
        msg=test.msg,
    )


# Property [Upsert Initialization]: $bit creates a new document with the field
# initialized from 0 when upsert is true and no document matches.
UPSERT_TESTS: list[BitUpsertTest] = [
    BitUpsertTest(
        "upsert_and_creates_zero",
        query={"_id": 99},
        update={"$bit": {"v": {"and": 10}}},
        expected_doc={"_id": 99, "v": 0},
        msg="$bit should create document with field=0 on upsert with AND.",
    ),
    BitUpsertTest(
        "upsert_or_creates_value",
        query={"_id": 99},
        update={"$bit": {"v": {"or": 10}}},
        expected_doc={"_id": 99, "v": 10},
        msg="$bit should create document with field=operand on upsert with OR.",
    ),
    BitUpsertTest(
        "upsert_xor_creates_value",
        query={"_id": 99},
        update={"$bit": {"v": {"xor": 10}}},
        expected_doc={"_id": 99, "v": 10},
        msg="$bit should create document with field=operand on upsert with XOR.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPSERT_TESTS))
def test_bit_upsert(collection, test: BitUpsertTest):
    """Test $bit upsert creates document with field initialized from 0."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected_doc["_id"]}}
    )
    assertSuccess(result, [test.expected_doc], msg=test.msg)
