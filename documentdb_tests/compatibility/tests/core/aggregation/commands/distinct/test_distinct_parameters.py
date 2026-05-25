"""Tests for distinct command parameter acceptance behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex
from bson.timestamp import Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import NAMESPACE_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len, Ne
from documentdb_tests.framework.target_collection import ViewCollection
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    INT32_MAX,
)

# Property [Query Parameter Behavior]: the query parameter filters which documents
# contribute to distinct values; an empty document matches all.
DISTINCT_QUERY_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_filters_documents",
        docs=[
            {"_id": 1, "x": "a", "status": "active"},
            {"_id": 2, "x": "b", "status": "inactive"},
            {"_id": 3, "x": "c", "status": "active"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"status": "active"},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should filter documents by the query parameter",
    ),
    CommandTestCase(
        "query_empty_doc_matches_all",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "b"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should treat empty document query as matching all documents",
    ),
]

# Property [Query No Match]: when the query matches no documents on an existing
# collection, distinct returns an empty values array.
DISTINCT_QUERY_NO_MATCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_no_matching_documents",
        docs=[
            {"_id": 1, "x": "a", "y": 1},
            {"_id": 2, "x": "b", "y": 2},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"y": 99},
        },
        expected={"values": [], "ok": 1.0},
        msg="distinct should return empty values when query matches no documents",
    ),
]

# Property [Comment Parameter Behavior]: all BSON types are accepted as the
# comment value without error, and the comment does not affect command results.
DISTINCT_COMMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx, v=val: {
            "distinct": ctx.collection,
            "key": "x",
            "comment": v,
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg=f"distinct should accept {tid} as comment without affecting results",
    )
    for tid, val in [
        ("string", "a string comment"),
        ("int32", 42),
        ("int64", Int64(123456789)),
        ("double", 3.14),
        ("decimal128", Decimal128("9.99")),
        ("bool", True),
        ("array", [1, "two", 3]),
        ("object", {"reason": "testing"}),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(100, 1)),
        ("binary", Binary(b"data", 0)),
        ("regex", Regex("pattern", "i")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"s": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [ReadConcern Success]: readConcern accepts "local", "available", and
# "majority" levels, as well as an empty object or provenance-only without a level.
DISTINCT_READCONCERN_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_{tid}",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx, v=val: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": v,
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg=f"distinct should accept readConcern {tid}",
    )
    for tid, val in [
        ("local", {"level": "local"}),
        ("available", {"level": "available"}),
        ("majority", {"level": "majority"}),
        ("empty_object", {}),
        ("provenance_only", {"provenance": "clientSupplied"}),
    ]
]

# Property [maxTimeMS Acceptance]: maxTimeMS accepts 0, positive integers up to
# INT32_MAX, whole-number floats, Decimal128 integers, and -0.0.
DISTINCT_MAXTIMEMS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_{tid}",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx, v=val: {
            "distinct": ctx.collection,
            "key": "x",
            "maxTimeMS": v,
        },
        expected={"values": ["a"], "ok": 1.0},
        msg=f"distinct should accept {tid} as maxTimeMS",
    )
    for tid, val in [
        ("zero", 0),
        ("positive_int", 1000),
        ("int32_max", INT32_MAX),
        ("int64_int32_max", Int64(INT32_MAX)),
        ("whole_number_float", 500.0),
        ("decimal128_integer", Decimal128("100")),
        ("negative_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_neg_zero_exponent", Decimal128("-0E+10")),
    ]
]

# Property [Timestamp Zero Replacement]: Timestamp(0, 0) is replaced by the server
# on insert; the stored values participate in deduplication, not the literal (0, 0).
DISTINCT_TIMESTAMP_ZERO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dedup_timestamp_zero_replaced",
        docs=[{"_id": 1, "x": Timestamp(0, 0)}, {"_id": 2, "x": Timestamp(0, 0)}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": Len(2),
            "values.0": Ne(Timestamp(0, 0)),
            "values.1": Ne(Timestamp(0, 0)),
            "ok": Eq(1.0),
        },
        msg=(
            "distinct should return server-assigned timestamps for Timestamp(0, 0),"
            " not deduplicate them as identical"
        ),
    ),
]

# Property [Collection Name Acceptance]: non-existent collection names with special
# characters, Unicode, number-like strings, and long names succeed with empty results.
DISTINCT_COLLECTION_NAME_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collname_nonexistent",
        docs=None,
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should succeed with empty results for a non-existent collection",
    ),
    CommandTestCase(
        "collname_space",
        docs=None,
        command=lambda ctx: {"distinct": f"{ctx.collection} space", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept space characters in collection names",
    ),
    CommandTestCase(
        "collname_punctuation",
        docs=None,
        command=lambda ctx: {"distinct": f"{ctx.collection}!@#%^&*()", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept punctuation characters in collection names",
    ),
    CommandTestCase(
        "collname_control_chars",
        docs=None,
        command=lambda ctx: {"distinct": f"{ctx.collection}\x01\x02\x03", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept control characters in collection names",
    ),
    CommandTestCase(
        "collname_zero_width_space",
        # U+200B zero-width space.
        docs=None,
        command=lambda ctx: {"distinct": f"{ctx.collection}\u200b", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept zero-width space in collection names",
    ),
    CommandTestCase(
        "collname_emoji",
        docs=None,
        command=lambda ctx: {"distinct": f"{ctx.collection}\U0001f389", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept emoji characters in collection names",
    ),
    CommandTestCase(
        "collname_tab",
        docs=None,
        command=lambda ctx: {"distinct": f"{ctx.collection}\t", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept tab characters in collection names",
    ),
    CommandTestCase(
        "collname_newline",
        docs=None,
        command=lambda ctx: {"distinct": f"{ctx.collection}\n", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept newline characters in collection names",
    ),
    CommandTestCase(
        "collname_number_zero",
        docs=None,
        command=lambda ctx: {"distinct": "0", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg='distinct should accept "0" as collection name without coercion',
    ),
    CommandTestCase(
        "collname_number_nan",
        docs=None,
        command=lambda ctx: {"distinct": "NaN", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg='distinct should accept "NaN" as collection name without coercion',
    ),
    CommandTestCase(
        "collname_number_infinity",
        docs=None,
        command=lambda ctx: {"distinct": "Infinity", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg='distinct should accept "Infinity" as collection name without coercion',
    ),
    CommandTestCase(
        "collname_number_true",
        docs=None,
        command=lambda ctx: {"distinct": "true", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg='distinct should accept "true" as collection name without coercion',
    ),
    CommandTestCase(
        "collname_number_null",
        docs=None,
        command=lambda ctx: {"distinct": "null", "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg='distinct should accept "null" as collection name without coercion',
    ),
    CommandTestCase(
        "collname_long_name",
        docs=None,
        command=lambda ctx: {"distinct": "a" * 10_000, "key": "x"},
        expected={"values": [], "ok": 1.0},
        msg="distinct should accept very long collection names without error",
    ),
]

# Property [Collection Name UUID Resolution]: Binary subtype 4 (UUID) as the
# distinct field triggers UUID-based collection resolution, producing a namespace
# not found error when the UUID does not match any collection.
DISTINCT_COLLECTION_NAME_UUID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collname_uuid_binary_error",
        docs=None,
        command=lambda ctx: {
            "distinct": Binary(b"\x00" * 16, 4),
            "key": "x",
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg=(
            "distinct should trigger UUID-based resolution for Binary subtype 4,"
            " producing a namespace not found error when UUID does not match"
        ),
    ),
]

# Property [Collection Name UUID Success]: Binary subtype 4 (UUID) as the distinct
# field triggers UUID-based collection resolution; when the UUID matches an existing
# collection, the command succeeds.
DISTINCT_COLLECTION_NAME_UUID_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collname_uuid_success",
        docs=[{"_id": 1, "x": "found"}],
        command=lambda ctx: {"distinct": ctx.uuids[ctx.collection], "key": "x"},
        expected={"values": ["found"], "ok": 1.0},
        msg="distinct should succeed when Binary subtype 4 (UUID) matches an existing collection",
    ),
]

# Property [Null Optional Parameters]: when optional parameters (query, collation,
# readConcern, comment, maxTimeMS) are null, they are treated as omitted.
DISTINCT_NULL_PARAMS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"null_{tid}_param",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        command=lambda ctx, p=param: {"distinct": ctx.collection, "key": "x", p: None},
        expected={"values": ["a", "b"], "ok": 1.0},
        msg=f"distinct should treat {param}=null as omitted",
    )
    for tid, param in [
        ("query", "query"),
        ("collation", "collation"),
        ("read_concern", "readConcern"),
        ("comment", "comment"),
        ("max_time_ms", "maxTimeMS"),
    ]
]

# Property [Query Composition on Views]: the query parameter composes with
# the view's pipeline filter to further restrict visible documents.
DISTINCT_QUERY_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_on_filtered_view",
        target_collection=ViewCollection(pipeline=[{"$match": {"status": "active"}}]),
        docs=[
            {"_id": 1, "status": "active", "cat": "a", "x": 10},
            {"_id": 2, "status": "active", "cat": "b", "x": 20},
            {"_id": 3, "status": "inactive", "cat": "a", "x": 30},
            {"_id": 4, "status": "active", "cat": "a", "x": 40},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "cat",
            "query": {"x": {"$gte": 20}},
        },
        expected={"values": ["a", "b"], "ok": 1},
        ignore_order_in=["values"],
        msg="distinct query should compose with view pipeline filter",
    ),
    CommandTestCase(
        "query_excludes_all_on_filtered_view",
        target_collection=ViewCollection(pipeline=[{"$match": {"status": "active"}}]),
        docs=[
            {"_id": 1, "status": "active", "cat": "a", "x": 10},
            {"_id": 2, "status": "inactive", "cat": "b", "x": 50},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "cat",
            "query": {"x": {"$gte": 50}},
        },
        expected={"values": [], "ok": 1},
        msg="distinct query + view filter should return empty when no docs match both",
    ),
]

DISTINCT_PARAMETER_TESTS: list[CommandTestCase] = (
    DISTINCT_NULL_PARAMS_TESTS
    + DISTINCT_QUERY_SUCCESS_TESTS
    + DISTINCT_QUERY_NO_MATCH_TESTS
    + DISTINCT_COMMENT_TESTS
    + DISTINCT_READCONCERN_SUCCESS_TESTS
    + DISTINCT_MAXTIMEMS_ACCEPTANCE_TESTS
    + DISTINCT_TIMESTAMP_ZERO_TESTS
    + DISTINCT_COLLECTION_NAME_ACCEPTANCE_TESTS
    + DISTINCT_COLLECTION_NAME_UUID_TESTS
    + DISTINCT_COLLECTION_NAME_UUID_SUCCESS_TESTS
    + DISTINCT_QUERY_VIEW_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_PARAMETER_TESTS))
def test_distinct_parameters(database_client: Any, collection: Any, test: CommandTestCase) -> None:
    """Test distinct parameter acceptance cases."""
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
