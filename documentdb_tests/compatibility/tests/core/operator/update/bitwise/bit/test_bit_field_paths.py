"""Tests for $bit update operator field paths, missing fields, and multiple fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class BitFieldPathTest(BaseTestCase):
    """Test case for $bit field path behavior."""

    setup_doc: Any = None
    update: Any = None
    expected_doc: Any = None


# Property [Field Paths]: $bit supports dot notation for nested fields, creates missing
# intermediate documents, initializes missing fields from 0, and operates on multiple
# fields independently in a single update.
TESTS: list[BitFieldPathTest] = [
    # Missing field initialization (field defaults to 0).
    BitFieldPathTest(
        "missing_field_and",
        setup_doc={"_id": 1},
        update={"$bit": {"v": {"and": 10}}},
        expected_doc={"_id": 1, "v": 0},
        msg="$bit should initialize missing field to 0 then compute 0 & 10 = 0.",
    ),
    BitFieldPathTest(
        "missing_field_or",
        setup_doc={"_id": 1},
        update={"$bit": {"v": {"or": 10}}},
        expected_doc={"_id": 1, "v": 10},
        msg="$bit should initialize missing field to 0 then compute 0 | 10 = 10.",
    ),
    BitFieldPathTest(
        "missing_field_xor",
        setup_doc={"_id": 1},
        update={"$bit": {"v": {"xor": 10}}},
        expected_doc={"_id": 1, "v": 10},
        msg="$bit should initialize missing field to 0 then compute 0 ^ 10 = 10.",
    ),
    BitFieldPathTest(
        "missing_field_int64_operand",
        setup_doc={"_id": 1},
        update={"$bit": {"v": {"or": Int64(255)}}},
        expected_doc={"_id": 1, "v": Int64(255)},
        msg="$bit should create Int64 result when missing field gets Int64 operand.",
    ),
    # Dot notation on nested fields.
    BitFieldPathTest(
        "nested_dot_notation",
        setup_doc={"_id": 1, "a": {"b": 15}},
        update={"$bit": {"a.b": {"and": 7}}},
        expected_doc={"_id": 1, "a": {"b": 7}},
        msg="$bit should update nested field via dot notation.",
    ),
    BitFieldPathTest(
        "missing_nested_creates_path",
        setup_doc={"_id": 1},
        update={"$bit": {"a.b": {"or": 5}}},
        expected_doc={"_id": 1, "a": {"b": 5}},
        msg="$bit should create intermediate nested documents for missing path.",
    ),
    # Array element by numeric index.
    BitFieldPathTest(
        "array_index",
        setup_doc={"_id": 1, "arr": [10, 20, 30]},
        update={"$bit": {"arr.0": {"xor": 5}}},
        expected_doc={"_id": 1, "arr": [15, 20, 30]},
        msg="$bit should update array element by numeric index.",
    ),
    # Multiple fields in single $bit.
    BitFieldPathTest(
        "multiple_fields",
        setup_doc={"_id": 1, "a": 15, "b": 0, "c": 5},
        update={"$bit": {"a": {"and": 7}, "b": {"or": 8}, "c": {"xor": 3}}},
        expected_doc={"_id": 1, "a": 7, "b": 8, "c": 6},
        msg="$bit should update multiple fields independently in one operation.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_bit_field_paths(collection, test: BitFieldPathTest):
    """Test $bit field path resolution, creation, and multi-field support."""
    collection.insert_one(test.setup_doc)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": test.update}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}},
    )
    assertSuccess(result, [test.expected_doc], msg=test.msg)
