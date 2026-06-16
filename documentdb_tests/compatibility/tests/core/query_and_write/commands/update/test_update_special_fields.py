"""Tests for update command special field handling and BSON type preservation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
    IMMUTABLE_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class SpecialFieldTest(BaseTestCase):
    """Test case for special field and BSON preservation behavior."""

    setup_docs: Any = None
    updates: Any = None
    expected_docs: Any = None


def run_and_find(collection, test: SpecialFieldTest):
    """Insert doc, run update, return find result."""
    collection.insert_one(test.setup_docs)
    execute_command(collection, {"update": collection.name, "updates": test.updates})
    return execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})


# Property [BSON Type Preservation]: $set preserves the exact BSON type of the value
# stored, including int, Int64, double, Decimal128, datetime, null, and bool.
TYPE_TESTS: list[SpecialFieldTest] = [
    SpecialFieldTest(
        "preserves_int",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"v": 42}}}],
        expected_docs=[{"_id": 1, "v": 42}],
        msg="$set should preserve integer type.",
    ),
    SpecialFieldTest(
        "preserves_int64",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"v": Int64(123_456_789_012_345)}}}],
        expected_docs=[{"_id": 1, "v": Int64(123_456_789_012_345)}],
        msg="$set should preserve Int64 type.",
    ),
    SpecialFieldTest(
        "preserves_double",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"v": 3.14}}}],
        expected_docs=[{"_id": 1, "v": 3.14}],
        msg="$set should preserve double type.",
    ),
    SpecialFieldTest(
        "preserves_decimal128",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"v": Decimal128("123.456")}}}],
        expected_docs=[{"_id": 1, "v": Decimal128("123.456")}],
        msg="$set should preserve Decimal128 type.",
    ),
    SpecialFieldTest(
        "preserves_date",
        setup_docs={"_id": 1},
        updates=[
            {
                "q": {"_id": 1},
                "u": {"$set": {"v": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}},
            }
        ],
        expected_docs=[{"_id": 1, "v": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}],
        msg="$set should preserve datetime type.",
    ),
    SpecialFieldTest(
        "preserves_null",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"v": None}}}],
        expected_docs=[{"_id": 1, "v": None}],
        msg="$set should preserve null value.",
    ),
    SpecialFieldTest(
        "preserves_bool",
        setup_docs={"_id": 1},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"v": True}}}],
        expected_docs=[{"_id": 1, "v": True}],
        msg="$set should preserve boolean type.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TYPE_TESTS))
def test_update_bson_preservation(collection, test: SpecialFieldTest):
    """Test $set preserves BSON types correctly."""
    result = run_and_find(collection, test)
    assertSuccess(result, test.expected_docs, msg=test.msg)


# Property [Dollar/Dot Field Rules]: top-level dollar-prefixed fields are rejected,
# nested dollar-prefixed fields succeed, and array index beyond length pads with null.
FIELD_TESTS: list[SpecialFieldTest] = [
    SpecialFieldTest(
        "nested_dollar_prefix_succeeds",
        setup_docs={"_id": 1, "a": {}},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"a.$b": 1}}}],
        expected_docs=[{"_id": 1, "a": {"$b": 1}}],
        msg="$set on nested dollar-prefixed field should succeed.",
    ),
    SpecialFieldTest(
        "array_index_pads_nulls",
        setup_docs={"_id": 1, "arr": [0, 1]},
        updates=[{"q": {"_id": 1}, "u": {"$set": {"arr.5": 99}}}],
        expected_docs=[{"_id": 1, "arr": [0, 1, None, None, None, 99]}],
        msg="$set on array index beyond length should pad with null.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_TESTS))
def test_update_field_rules(collection, test: SpecialFieldTest):
    """Test dollar/dot field and array index behavior."""
    result = run_and_find(collection, test)
    assertSuccess(result, test.expected_docs, msg=test.msg)


def test_update_cannot_modify_id(collection):
    """Test $set on _id field errors."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"_id": 2}}}]},
    )
    assertFailureCode(result, IMMUTABLE_FIELD_ERROR)


def test_update_top_level_dollar_prefix_errors(collection):
    """Test $set on top-level dollar-prefixed field errors."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"$bad": 1}}}]},
    )
    assertFailureCode(result, DOLLAR_PREFIXED_FIELD_NAME_ERROR)
