"""$bit update operator across command paths (findAndModify and bulk write).

Existing $bit coverage drives the operator exclusively through the ``update``
command. This file covers the other command paths that route $bit through
distinct gateway code: the ``findAndModify`` command (with ``new`` pre/post
image selection and ``upsert``) and a batched bulk write. The bitwise result
and the response metadata must match the ``update`` command path.

Oracle: MongoDB 7.0 (functional-tests CI baseline). The engine under test
matches native behavior on every case; no engine divergences are tracked for
this surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from pymongo import UpdateOne

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.update


@dataclass(frozen=True)
class BitFindAndModifyTest(BaseTestCase):
    """A $bit findAndModify case."""

    setup_doc: Any = None
    command_extra: dict = field(default_factory=dict)
    bit_op: Any = None
    # Expected `value` image returned by findAndModify (pre- or post-image).
    expected_value: Any = None
    # Expected resulting document after the operation (read back via find).
    expected_doc: Any = None


FIND_AND_MODIFY_TESTS: list[BitFindAndModifyTest] = [
    BitFindAndModifyTest(
        "and_returns_post_image",
        setup_doc={"_id": 1, "v": 13},
        bit_op={"and": 10},
        command_extra={"new": True},
        expected_value={"_id": 1, "v": 8},
        expected_doc={"_id": 1, "v": 8},
        msg="findAndModify $bit AND returns the post-image when new=true.",
    ),
    BitFindAndModifyTest(
        "or_returns_post_image",
        setup_doc={"_id": 1, "v": 13},
        bit_op={"or": 2},
        command_extra={"new": True},
        expected_value={"_id": 1, "v": 15},
        expected_doc={"_id": 1, "v": 15},
        msg="findAndModify $bit OR returns the post-image when new=true.",
    ),
    BitFindAndModifyTest(
        "xor_returns_post_image",
        setup_doc={"_id": 1, "v": 13},
        bit_op={"xor": 6},
        command_extra={"new": True},
        expected_value={"_id": 1, "v": 11},
        expected_doc={"_id": 1, "v": 11},
        msg="findAndModify $bit XOR returns the post-image when new=true.",
    ),
    BitFindAndModifyTest(
        "and_returns_pre_image_when_new_false",
        setup_doc={"_id": 1, "v": 13},
        bit_op={"and": 10},
        command_extra={"new": False},
        expected_value={"_id": 1, "v": 13},
        expected_doc={"_id": 1, "v": 8},
        msg="findAndModify $bit returns the pre-image when new=false but still applies.",
    ),
]


def run_find_and_modify(collection, test: BitFindAndModifyTest):
    """Insert the seed doc, run $bit via findAndModify, return (response, found doc)."""
    collection.insert_one(dict(test.setup_doc))
    command = {
        "findAndModify": collection.name,
        "query": {"_id": test.setup_doc["_id"]},
        "update": {"$bit": {"v": test.bit_op}},
    }
    command.update(test.command_extra)
    response = execute_command(collection, command)
    found = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": test.setup_doc["_id"]}, "sort": {"_id": 1}},
    )
    return response, found


@pytest.mark.parametrize("test", pytest_params(FIND_AND_MODIFY_TESTS))
def test_bit_find_and_modify(collection, test: BitFindAndModifyTest):
    """$bit applied through findAndModify returns the documented image."""
    response, _ = run_find_and_modify(collection, test)
    assertSuccessPartial(response, {"value": test.expected_value}, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(FIND_AND_MODIFY_TESTS))
def test_bit_find_and_modify_persisted(collection, test: BitFindAndModifyTest):
    """$bit applied through findAndModify persists the bitwise result."""
    _, found = run_find_and_modify(collection, test)
    assertResult(found, expected=[test.expected_doc], msg=test.msg)


def test_bit_find_and_modify_upsert(collection):
    """findAndModify $bit with upsert initializes the field from 0 and returns it."""
    response = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 99},
            "update": {"$bit": {"v": {"or": 5}}},
            "upsert": True,
            "new": True,
        },
    )
    assertSuccessPartial(
        response,
        {"value": {"_id": 99, "v": 5}},
        msg="findAndModify $bit upsert initializes v from 0 then applies OR 5.",
    )


def test_bit_bulk_write_update_one(collection):
    """$bit applied through a batched bulk write produces the bitwise result."""
    collection.insert_one({"_id": 1, "v": 13})
    collection.bulk_write([UpdateOne({"_id": 1}, {"$bit": {"v": {"and": 10}}})])
    found = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertResult(
        found,
        expected=[{"_id": 1, "v": 8}],
        msg="A bulk-write $bit AND computes 1101 & 1010 = 1000.",
    )
