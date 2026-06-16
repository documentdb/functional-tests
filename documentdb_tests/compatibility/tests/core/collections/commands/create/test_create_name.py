"""Tests for the create command collection name parameter."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    ILLEGAL_OPERATION_ERROR,
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Name Unicode Acceptance]: the collection name accepts any Unicode
# characters including CJK, emoji, Latin extended, Greek, and Cyrillic.
CREATE_NAME_UNICODE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_character",
        command=lambda ctx: {"create": f"{ctx.collection}_custom"},
        expected={"ok": 1.0},
        msg="Single character name should succeed",
    ),
    CommandTestCase(
        "digits_only",
        command=lambda ctx: {"create": f"{ctx.collection}_custom"},
        expected={"ok": 1.0},
        msg="Digits-only name should succeed",
    ),
    CommandTestCase(
        "cjk_unicode",
        command=lambda ctx: {"create": f"{ctx.collection}_\u6d4b\u8bd5"},
        expected={"ok": 1.0},
        msg="CJK characters should succeed",
    ),
    CommandTestCase(
        "emoji",
        command=lambda ctx: {"create": f"{ctx.collection}_\U0001f389"},
        expected={"ok": 1.0},
        msg="Emoji (4-byte UTF-8) should succeed",
    ),
    CommandTestCase(
        "latin_extended",
        command=lambda ctx: {"create": f"{ctx.collection}_\u00f1o\u00f1o"},
        expected={"ok": 1.0},
        msg="Latin extended characters should succeed",
    ),
    CommandTestCase(
        "greek",
        command=lambda ctx: {"create": f"{ctx.collection}_\u03b1\u03b2\u03b3"},
        expected={"ok": 1.0},
        msg="Greek characters should succeed",
    ),
    CommandTestCase(
        "cyrillic",
        command=lambda ctx: {"create": f"{ctx.collection}_\u043a\u0438\u0440"},
        expected={"ok": 1.0},
        msg="Cyrillic characters should succeed",
    ),
    CommandTestCase(
        "precomposed_unicode",
        command=lambda ctx: {"create": f"{ctx.collection}_\u00e9"},
        expected={"ok": 1.0},
        msg="Precomposed unicode (U+00E9) should succeed",
    ),
    CommandTestCase(
        "decomposed_unicode",
        command=lambda ctx: {"create": f"{ctx.collection}_e\u0301"},
        expected={"ok": 1.0},
        msg="Decomposed unicode (e + U+0301) should succeed",
    ),
]

# Property [Name Whitespace and Invisible Characters]: whitespace (space, tab,
# newline, CR, NBSP, en space) and invisible characters (BOM, ZWSP, ZWJ, LTR/RTL
# marks) are accepted in collection names.
CREATE_NAME_WHITESPACE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "whitespace_space",
        command=lambda ctx: {"create": f"{ctx.collection} space"},
        expected={"ok": 1.0},
        msg="Space character in name should succeed and not be trimmed",
    ),
    CommandTestCase(
        "whitespace_tab",
        command=lambda ctx: {"create": f"{ctx.collection}\ttab"},
        expected={"ok": 1.0},
        msg="Tab character in name should succeed",
    ),
    CommandTestCase(
        "whitespace_newline",
        command=lambda ctx: {"create": f"{ctx.collection}\nnl"},
        expected={"ok": 1.0},
        msg="Newline character in name should succeed",
    ),
    CommandTestCase(
        "whitespace_cr",
        command=lambda ctx: {"create": f"{ctx.collection}\rcr"},
        expected={"ok": 1.0},
        msg="Carriage return in name should succeed",
    ),
    CommandTestCase(
        "whitespace_nbsp",
        command=lambda ctx: {"create": f"{ctx.collection}\u00a0nbsp"},
        expected={"ok": 1.0},
        msg="NBSP U+00A0 in name should succeed",
    ),
    CommandTestCase(
        "whitespace_en_space",
        command=lambda ctx: {"create": f"{ctx.collection}\u2000en"},
        expected={"ok": 1.0},
        msg="En space U+2000 in name should succeed",
    ),
    CommandTestCase(
        "invisible_bom",
        command=lambda ctx: {"create": f"{ctx.collection}\ufeff"},
        expected={"ok": 1.0},
        msg="BOM U+FEFF in name should succeed",
    ),
    CommandTestCase(
        "invisible_zwsp",
        command=lambda ctx: {"create": f"{ctx.collection}\u200b"},
        expected={"ok": 1.0},
        msg="ZWSP U+200B in name should succeed",
    ),
    CommandTestCase(
        "invisible_zwj",
        command=lambda ctx: {"create": f"{ctx.collection}\u200d"},
        expected={"ok": 1.0},
        msg="ZWJ U+200D in name should succeed",
    ),
    CommandTestCase(
        "invisible_ltr_mark",
        command=lambda ctx: {"create": f"{ctx.collection}\u200e"},
        expected={"ok": 1.0},
        msg="LTR mark U+200E in name should succeed",
    ),
    CommandTestCase(
        "invisible_rtl_mark",
        command=lambda ctx: {"create": f"{ctx.collection}\u200f"},
        expected={"ok": 1.0},
        msg="RTL mark U+200F in name should succeed",
    ),
]

# Property [Name Special Characters]: dots in non-leading positions and
# non-ASCII dollar-like characters are accepted; only ASCII $ is rejected.
CREATE_NAME_SPECIAL_CHARS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dot_middle",
        command=lambda ctx: {"create": f"{ctx.collection}_mid.dle"},
        expected={"ok": 1.0},
        msg="Dot in middle position should succeed",
    ),
    CommandTestCase(
        "dot_trailing",
        command=lambda ctx: {"create": f"{ctx.collection}_trailing."},
        expected={"ok": 1.0},
        msg="Dot in trailing position should succeed",
    ),
    CommandTestCase(
        "fullwidth_dollar",
        command=lambda ctx: {"create": f"{ctx.collection}_\uff04name"},
        expected={"ok": 1.0},
        msg="Fullwidth dollar U+FF04 should succeed (only ASCII $ rejected)",
    ),
    CommandTestCase(
        "small_dollar",
        command=lambda ctx: {"create": f"{ctx.collection}_\ufe69name"},
        expected={"ok": 1.0},
        msg="Small dollar U+FE69 should succeed",
    ),
    CommandTestCase(
        "peso_sign",
        command=lambda ctx: {"create": f"{ctx.collection}_\u20b1name"},
        expected={"ok": 1.0},
        msg="Peso sign U+20B1 should succeed",
    ),
]

# Property [Name Namespace Length Boundary]: names that fill the 255-byte
# namespace limit exactly (with 1-byte, 2-byte, and 4-byte characters) succeed.
CREATE_NAME_LENGTH_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_namespace_length",
        command=lambda ctx: {"create": "x" * (255 - len(ctx.database.encode("utf-8")) - 1)},
        expected={"ok": 1.0},
        msg="Collection at exactly 255-byte namespace boundary should succeed",
    ),
    CommandTestCase(
        "max_namespace_2byte_chars",
        command=lambda ctx: {
            "create": "\u00e9" * ((255 - len(ctx.database.encode("utf-8")) - 1) // 2)
        },
        expected={"ok": 1.0},
        msg="2-byte chars filling namespace to boundary should succeed",
    ),
    CommandTestCase(
        "max_namespace_4byte_chars",
        command=lambda ctx: {
            "create": "\U0001f389" * ((255 - len(ctx.database.encode("utf-8")) - 1) // 4)
        },
        expected={"ok": 1.0},
        msg="4-byte chars filling namespace to boundary should succeed",
    ),
]

# Property [Name System Prefix Exceptions]: system.views, system.profile,
# system.js, system.users, and system.buckets with timeseries are allowed;
# the system. check is case-sensitive.
CREATE_NAME_SYSTEM_EXCEPTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_views",
        command={"create": "system.views"},
        expected={"ok": 1.0},
        msg="system.views should always be allowed",
    ),
    CommandTestCase(
        "system_profile",
        command={"create": "system.profile"},
        expected={"ok": 1.0},
        msg="system.profile should always be allowed",
    ),
    CommandTestCase(
        "system_js",
        command={"create": "system.js"},
        expected={"ok": 1.0},
        msg="system.js should always be allowed",
    ),
    CommandTestCase(
        "system_users",
        command={"create": "system.users"},
        expected={"ok": 1.0},
        msg="system.users should always be allowed",
    ),
    CommandTestCase(
        "system_buckets_with_timeseries",
        command=lambda ctx: {
            "create": f"system.buckets.{ctx.collection}",
            "timeseries": {"timeField": "ts"},
        },
        expected={"ok": 1.0},
        msg="system.buckets.<name> with timeseries options should succeed",
    ),
    CommandTestCase(
        "system_prefix_uppercase",
        command=lambda ctx: {"create": f"{ctx.collection}_System.test"},
        expected={"ok": 1.0},
        msg="Uppercase 'System.' prefix should succeed (check is case-sensitive)",
    ),
]

# Property [Name Type Strictness]: non-string types for the collection name
# produce INVALID_NAMESPACE_ERROR.
CREATE_NAME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"name_{tid}",
        command={"create": val},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"{tid} name should fail",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("null", None),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"hello")),
        ("regex", Regex("test")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Name Value Rejection]: empty strings, embedded null bytes, leading
# dots, ASCII dollar in any position, and namespace exceeding 255 bytes produce
# INVALID_NAMESPACE_ERROR.
CREATE_NAME_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="empty_string",
        command={"create": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty string name should fail",
    ),
    CommandTestCase(
        id="null_byte",
        command={"create": "test\x00coll"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Embedded null byte should fail",
    ),
    CommandTestCase(
        id="leading_dot",
        command={"create": ".leading"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Leading dot should fail",
    ),
    CommandTestCase(
        id="dollar_start",
        command={"create": "$test"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Dollar at start should fail",
    ),
    CommandTestCase(
        id="dollar_middle",
        command={"create": "te$st"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Dollar in middle should fail",
    ),
    CommandTestCase(
        id="dollar_end",
        command={"create": "test$"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Dollar at end should fail",
    ),
    CommandTestCase(
        id="namespace_exceeds_255_bytes",
        command=lambda ctx: {"create": "x" * (256 - len(ctx.database.encode("utf-8")) - 1)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Namespace exceeding 255 bytes should fail",
    ),
]

# Property [System Prefix Restriction]: names starting with lowercase "system."
# other than allowed exceptions produce INVALID_NAMESPACE_ERROR.
CREATE_NAME_SYSTEM_PREFIX_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="system_arbitrary",
        command={"create": "system.test"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="system.* prefix should fail",
    ),
]

# Property [System Buckets Without Timeseries]: system.buckets.<name> without
# timeseries options produces ILLEGAL_OPERATION_ERROR.
CREATE_NAME_SYSTEM_BUCKETS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="system_buckets_no_timeseries",
        command={"create": "system.buckets.test"},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.buckets without timeseries should fail",
    ),
]

CREATE_NAME_TESTS: list[CommandTestCase] = (
    CREATE_NAME_UNICODE_TESTS
    + CREATE_NAME_WHITESPACE_TESTS
    + CREATE_NAME_SPECIAL_CHARS_TESTS
    + CREATE_NAME_LENGTH_BOUNDARY_TESTS
    + CREATE_NAME_SYSTEM_EXCEPTIONS_TESTS
    + CREATE_NAME_TYPE_ERROR_TESTS
    + CREATE_NAME_VALUE_ERROR_TESTS
    + CREATE_NAME_SYSTEM_PREFIX_ERROR_TESTS
    + CREATE_NAME_SYSTEM_BUCKETS_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_NAME_TESTS))
def test_create_name(database_client, collection, test):
    """Test create command name behavior."""
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
