"""Tests for distinct command result ordering and response format."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex
from bson.timestamp import Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import TargetDatabase

# Property [Result Ordering]: distinct results are returned in BSON type
# comparison order.
DISTINCT_RESULT_ORDERING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ordering_cross_type",
        docs=[
            {"_id": 1, "x": MaxKey()},
            {"_id": 2, "x": "hello"},
            {"_id": 3, "x": None},
            {"_id": 4, "x": 42},
            {"_id": 5, "x": {"a": 1}},
            {"_id": 6, "x": Binary(b"data", 0)},
            {"_id": 7, "x": ObjectId("000000000000000000000001")},
            {"_id": 8, "x": True},
            {"_id": 9, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 10, "x": Timestamp(100, 1)},
            {"_id": 11, "x": Regex("abc", "")},
            {"_id": 12, "x": MinKey()},
            {"_id": 13, "x": Code("function()", {"scope": 1})},
            {"_id": 14, "x": Code("function()")},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [
                MinKey(),
                None,
                42,
                "hello",
                {"a": 1},
                b"data",
                ObjectId("000000000000000000000001"),
                True,
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                Timestamp(100, 1),
                Regex("abc", ""),
                Code("function()"),
                Code("function()", {"scope": 1}),
                MaxKey(),
            ],
            "ok": 1.0,
        },
        msg=(
            "distinct should return results in BSON type comparison order:"
            " MinKey < null < numbers < string < object < binary"
            " < ObjectId < bool < datetime < Timestamp < Regex"
            " < Code < CodeWithScope < MaxKey"
        ),
    ),
    CommandTestCase(
        "ordering_within_numbers",
        docs=[
            {"_id": 1, "x": 100},
            {"_id": 2, "x": -5},
            {"_id": 3, "x": 0},
            {"_id": 4, "x": 42},
            {"_id": 5, "x": -100},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [-100, -5, 0, 42, 100], "ok": 1.0},
        msg="distinct should order numbers by numeric value within the number type",
    ),
    CommandTestCase(
        "ordering_within_strings",
        docs=[
            {"_id": 1, "x": "banana"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "cherry"},
            {"_id": 4, "x": "Apple"},
            {"_id": 5, "x": ""},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": ["", "Apple", "apple", "banana", "cherry"],
            "ok": 1.0,
        },
        msg="distinct should order strings by binary comparison within the string type",
    ),
    CommandTestCase(
        "ordering_within_booleans",
        docs=[{"_id": 1, "x": True}, {"_id": 2, "x": False}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [False, True], "ok": 1.0},
        msg="distinct should order booleans with False before True",
    ),
    CommandTestCase(
        "ordering_within_datetimes",
        docs=[
            {"_id": 1, "x": datetime(2024, 6, 1, tzinfo=timezone.utc)},
            {"_id": 2, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 3, "x": datetime(2024, 12, 1, tzinfo=timezone.utc)},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 6, 1, tzinfo=timezone.utc),
                datetime(2024, 12, 1, tzinfo=timezone.utc),
            ],
            "ok": 1.0,
        },
        msg="distinct should order datetimes chronologically within the datetime type",
    ),
]

# Property [Return Type and Response Format]: the response document contains the
# distinct values and succeeds even for non-existent collections.
DISTINCT_RESPONSE_FORMAT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response_format_basic",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should return a response with values array and ok field",
    ),
    CommandTestCase(
        "response_format_nonexistent_database",
        target_collection=TargetDatabase(suffix="nonexistent"),
        docs=None,
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty values array for a non-existent database",
    ),
    CommandTestCase(
        "response_format_empty_collection",
        docs=[],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty values array for an empty collection",
    ),
]

DISTINCT_RESULT_FORMAT_TESTS: list[CommandTestCase] = (
    DISTINCT_RESULT_ORDERING_TESTS + DISTINCT_RESPONSE_FORMAT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_RESULT_FORMAT_TESTS))
def test_distinct_result_ordering(
    database_client: Any, collection: Any, test: CommandTestCase
) -> None:
    """Test distinct result ordering cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
