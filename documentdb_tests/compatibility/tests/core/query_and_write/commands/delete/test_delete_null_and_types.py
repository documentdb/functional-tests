"""Delete command null handling and BSON type distinction tests.

Tests null/missing field matching semantics and BSON type distinction in queries.
"""

from __future__ import annotations

from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DATE_EPOCH

# Property [Null Semantics]: q:{field:null} matches both null values and missing fields.
NULL_MATCHING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_matches_null_and_missing",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}, {"_id": 3}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": None}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should match both null and missing fields",
    ),
    CommandTestCase(
        "type_null_matches_only_explicit",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}, {"_id": 3}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": {"$type": "null"}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match only explicit null with $type:null",
    ),
    CommandTestCase(
        "exists_false_matches_only_missing",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}, {"_id": 3}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": {"$exists": False}}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should match only missing field with $exists:false",
    ),
]

# Property [BSON Type Distinction]: queries distinguish between BSON types correctly.
TYPE_DISTINCTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "false_does_not_match_zero",
        docs=[{"_id": 1, "a": False}, {"_id": 2, "a": 0}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": False}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should not match int 0 when querying for false",
    ),
    CommandTestCase(
        "true_does_not_match_one",
        docs=[{"_id": 1, "a": True}, {"_id": 2, "a": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": True}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should not match int 1 when querying for true",
    ),
    CommandTestCase(
        "empty_string_does_not_match_null",
        docs=[{"_id": 1, "a": ""}, {"_id": 2, "a": None}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": ""}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete should not match null when querying for empty string",
    ),
    CommandTestCase(
        "zero_matches_all_numeric_zeros",
        docs=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": Int64(0)},
            {"_id": 3, "a": 0.0},
            {"_id": 4, "a": Decimal128("0")},
            {"_id": 5, "a": 1},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"a": 0}, "limit": 0}],
        },
        expected={"ok": 1.0, "n": 4},
        msg="delete should match all numeric zero representations",
    ),
]

DELETE_NULL_AND_TYPES_TESTS: list[CommandTestCase] = NULL_MATCHING_TESTS + TYPE_DISTINCTION_TESTS


@pytest.mark.parametrize("test", pytest_params(DELETE_NULL_AND_TYPES_TESTS))
def test_delete_null_and_types(database_client, collection, test):
    """Test delete command null matching and type distinction."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


_BSON_TYPE_DOCS: list[dict[str, Any]] = [
    {"_id": "double", "val": 3.14},
    {"_id": "string", "val": "hello"},
    {"_id": "object", "val": {"k": "v"}},
    {"_id": "array", "val": [1, 2, 3]},
    {"_id": "binary", "val": Binary(b"\x01\x02")},
    {"_id": "objectid", "val": ObjectId("000000000000000000000001")},
    {"_id": "bool", "val": True},
    {"_id": "date", "val": DATE_EPOCH},
    {"_id": "null", "val": None},
    {"_id": "regex", "val": Regex("^a", "i")},
    {"_id": "javascript", "val": Code("function(){}")},
    {"_id": "int", "val": 42},
    {"_id": "timestamp", "val": Timestamp(1, 1)},
    {"_id": "long", "val": Int64(123456)},
    {"_id": "decimal", "val": Decimal128("1.5")},
    {"_id": "minkey", "val": MinKey()},
    {"_id": "maxkey", "val": MaxKey()},
]

_BSON_TYPE_PARAMS = [pytest.param(doc["_id"], id=doc["_id"]) for doc in _BSON_TYPE_DOCS]


@pytest.mark.parametrize("type_id", _BSON_TYPE_PARAMS)
def test_delete_document_with_bson_type(collection, type_id):
    """Test delete can remove documents containing each BSON type."""
    collection.insert_many(_BSON_TYPE_DOCS)
    result = execute_command(
        collection,
        {"delete": collection.name, "deletes": [{"q": {"_id": type_id}, "limit": 1}]},
    )
    assertResult(
        result,
        expected={"ok": 1.0, "n": 1},
        msg=f"delete should remove document with {type_id} field",
        raw_res=True,
    )
