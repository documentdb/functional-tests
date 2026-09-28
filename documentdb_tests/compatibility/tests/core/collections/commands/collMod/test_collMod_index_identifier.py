"""Tests for collMod index identifier resolution by name and keyPattern."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INDEX_NOT_FOUND_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Index Identifier Resolution]: an index identifier given by name or
# by key pattern resolves to the matching existing index, so a paired
# modification applies and its old/new values are echoed in the result.
COLLMOD_INDEX_RESOLUTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "resolution_by_name",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": 200},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": Eq(Int64(100)),
            "expireAfterSeconds_new": Eq(Int64(200)),
        },
        msg="collMod should resolve an index by its name",
    ),
    CommandTestCase(
        "resolution_by_key_pattern",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"keyPattern": {"a": 1}, "hidden": True},
        },
        expected={"ok": Eq(1.0), "hidden_old": Eq(False), "hidden_new": Eq(True)},
        msg="collMod should resolve an index by its key pattern",
    ),
]

# Property [Index Identifier Ambiguity Rejection]: supplying both name and
# keyPattern, or neither, fails to unambiguously identify an index and is
# rejected as an invalid option, even when both refer to the same index.
COLLMOD_INDEX_IDENTIFIER_AMBIGUITY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "identifier_both_name_and_key_pattern",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "keyPattern": {"a": 1}, "hidden": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject specifying both name and keyPattern as an invalid option",
    ),
    CommandTestCase(
        "identifier_neither_name_nor_key_pattern",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "index": {"hidden": True}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject specifying neither name nor keyPattern as an invalid option",
    ),
]

# Property [Index Identifier No-Match Rejection]: a name or keyPattern that
# matches no existing index is rejected as index-not-found, including an empty
# keyPattern and a text-index keyPattern.
COLLMOD_INDEX_IDENTIFIER_NO_MATCH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "no_match_name",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "nonexistent", "hidden": True},
        },
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="collMod should reject a name that matches no existing index as index-not-found",
    ),
    CommandTestCase(
        "no_match_key_pattern",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"keyPattern": {"b": 1}, "hidden": True},
        },
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="collMod should reject a keyPattern that matches no existing index as index-not-found",
    ),
    CommandTestCase(
        "no_match_empty_key_pattern",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"keyPattern": {}, "hidden": True},
        },
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="collMod should reject an empty keyPattern as index-not-found",
    ),
    CommandTestCase(
        "no_match_text_key_pattern",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"keyPattern": {"a": "text"}, "hidden": True},
        },
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="collMod should reject a text-index keyPattern as index-not-found",
    ),
]

# Property [Index Name Null Rejection]: a null index.name is treated as absent,
# so no identifier is supplied and the command is rejected as an invalid option.
COLLMOD_INDEX_NAME_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_null",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": None, "hidden": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should treat a null index name as absent and reject it as an invalid option",
    ),
]

# Property [Index Name Non-String Rejection]: a non-string, non-null index.name
# produces a type-mismatch error.
COLLMOD_INDEX_NAME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"name_type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": v, "hidden": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} index name as a type mismatch",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", ["a_1"]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Index Name Literal Lookup]: an index.name string is always a literal
# lookup key, never a field path or variable, so any string content that names
# no existing index is rejected as index-not-found regardless of length.
COLLMOD_INDEX_NAME_LITERAL_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"name_literal_{tid}",
            indexes=[IndexModel([("a", 1)], name="a_1")],
            docs=[{"_id": 1, "a": 1}],
            command=lambda ctx, v=val: {
                "collMod": ctx.collection,
                "index": {"name": v, "hidden": True},
            },
            error_code=INDEX_NOT_FOUND_ERROR,
            msg=f"collMod should treat a {tid} index name as a literal lookup key",
        )
        for tid, val in [
            ("empty", ""),
            ("space", " "),
            ("tab", "\t"),
            ("newline", "\n"),
            ("cr", "\r"),
            ("nbsp", "\u00a0"),  # U+00A0 no-break space.
            ("name_with_space", "a b"),
            ("unicode_2byte", "caf\u00e9"),  # U+00E9 with accent.
            ("unicode_3byte", "\u4e2d"),  # U+4E2D CJK character.
            ("unicode_4byte", "\U0001f600"),  # U+1F600 emoji.
            ("zwsp", "\u200b"),  # U+200B zero-width space.
            ("bom", "\ufeff"),  # U+FEFF byte order mark.
            ("dollar", "$"),
            ("double_dollar", "$$"),
            ("dotted", "a.b.c"),
            ("control_low", "\x01"),  # U+0001 control char.
            ("control_high", "\x1f"),  # U+001F control char.
        ]
    ],
    *[
        CommandTestCase(
            f"name_literal_large_{size}",
            indexes=[IndexModel([("a", 1)], name="a_1")],
            docs=[{"_id": 1, "a": 1}],
            command=lambda ctx, n=size: {
                "collMod": ctx.collection,
                "index": {"name": "x" * n, "hidden": True},
            },
            error_code=INDEX_NOT_FOUND_ERROR,
            msg="collMod should treat a large index name as a literal lookup key "
            "with no length limit",
        )
        for size in [16_777_215, 16_777_216, 16_777_217]
    ],
]

# Property [Index Key Pattern Null Rejection]: a null index.keyPattern is treated
# as absent, so no identifier is supplied and the command is rejected as an
# invalid option.
COLLMOD_INDEX_KEY_PATTERN_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "key_pattern_null",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"keyPattern": None, "hidden": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should treat a null keyPattern as absent and reject it as an invalid option",
    ),
]

# Property [Index Key Pattern Non-Object Rejection]: a non-object, non-null
# index.keyPattern produces a type-mismatch error.
COLLMOD_INDEX_KEY_PATTERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"key_pattern_type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"keyPattern": v, "hidden": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} keyPattern as a type mismatch",
    )
    for tid, val in [
        ("string", "a_1"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [{"a": 1}]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

COLLMOD_INDEX_IDENTIFIER_TESTS: list[CommandTestCase] = (
    COLLMOD_INDEX_RESOLUTION_TESTS
    + COLLMOD_INDEX_IDENTIFIER_AMBIGUITY_ERROR_TESTS
    + COLLMOD_INDEX_IDENTIFIER_NO_MATCH_ERROR_TESTS
    + COLLMOD_INDEX_NAME_NULL_ERROR_TESTS
    + COLLMOD_INDEX_NAME_TYPE_ERROR_TESTS
    + COLLMOD_INDEX_NAME_LITERAL_ERROR_TESTS
    + COLLMOD_INDEX_KEY_PATTERN_NULL_ERROR_TESTS
    + COLLMOD_INDEX_KEY_PATTERN_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_INDEX_IDENTIFIER_TESTS))
def test_collMod_index_identifier(database_client, collection, test):
    """Test collMod index identifier resolution and rejection."""
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
