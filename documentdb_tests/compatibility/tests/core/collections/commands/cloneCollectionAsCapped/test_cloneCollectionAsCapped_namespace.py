"""Tests for cloneCollectionAsCapped namespace validation."""

from typing import Callable

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import NamedCollection

# Property [Source Name Validation Errors]: invalid source names
# produce INVALID_NAMESPACE_ERROR.
SOURCE_NAME_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_string",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="empty string source should fail",
    ),
    CommandTestCase(
        "null_byte_leading",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "\x00coll",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="leading null byte should fail",
    ),
    CommandTestCase(
        "null_byte_middle",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "co\x00ll",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="null byte in middle should fail",
    ),
    CommandTestCase(
        "null_byte_trailing",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "coll\x00",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="trailing null byte should fail",
    ),
    CommandTestCase(
        "leading_dot",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ".coll",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="leading dot should fail",
    ),
    CommandTestCase(
        "dollar_leading",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "$coll",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="leading dollar should fail",
    ),
    CommandTestCase(
        "dollar_middle",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "co$ll",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="dollar in middle should fail",
    ),
    CommandTestCase(
        "dollar_trailing",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "coll$",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="trailing dollar should fail",
    ),
    CommandTestCase(
        "dollar_multiple",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "$co$ll$",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="multiple dollars should fail",
    ),
    CommandTestCase(
        "dollar_double",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "co$$ll",
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="double dollar should fail",
    ),
]

# Property [Destination Name Validation Errors]: invalid destination
# names produce INVALID_NAMESPACE_ERROR.
DEST_NAME_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="empty string dest should fail",
    ),
    CommandTestCase(
        "null_byte_leading",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "\x00coll",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="leading null byte should fail",
    ),
    CommandTestCase(
        "null_byte_middle",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "co\x00ll",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="null byte in middle should fail",
    ),
    CommandTestCase(
        "null_byte_trailing",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "coll\x00",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="trailing null byte should fail",
    ),
    CommandTestCase(
        "leading_dot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": ".coll",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="leading dot should fail",
    ),
    CommandTestCase(
        "dollar_leading",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "$coll",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="leading dollar should fail",
    ),
    CommandTestCase(
        "dollar_middle",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "co$ll",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="dollar in middle should fail",
    ),
    CommandTestCase(
        "dollar_trailing",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "coll$",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="trailing dollar should fail",
    ),
    CommandTestCase(
        "system_other",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.other",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="system.other should fail",
    ),
    CommandTestCase(
        "system_namespaces",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.namespaces",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="system.namespaces should fail",
    ),
    CommandTestCase(
        "system_indexes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.indexes",
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="system.indexes should fail",
    ),
    CommandTestCase(
        "namespace_exceeds_255_bytes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "x" * (255 - len(ctx.database) - 1 + 1),
            "size": 100_000,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="namespace exceeding 255 bytes should fail",
    ),
]

# Property [Destination Name System Accepted]: certain system.*
# names are accepted as valid destination names.
DEST_NAME_SYSTEM_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_users",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.users",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="system.users should succeed",
    ),
    CommandTestCase(
        "system_views",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.views",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="system.views should succeed",
    ),
    CommandTestCase(
        "system_js",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.js",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="system.js should succeed",
    ),
    CommandTestCase(
        "system_profile",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.profile",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="system.profile should succeed",
    ),
]

# Property [Collection Name Acceptance - Valid Patterns]: various
# special characters and Unicode patterns are accepted as valid
# collection names.
VALID_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"valid_name_{id}",
        target_collection=NamedCollection(suffix=f"_{suffix}"),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg=f"{id.replace('_', ' ')} should be accepted as a valid name",
    )
    for id, suffix in [
        ("single_char", "a"),
        ("digits_only", "12345"),
        ("space", " "),
        ("tab", "\t"),
        ("newline", "\n"),
        ("carriage_return", "\r"),
        ("cjk", "\u4e2d\u6587"),
        ("emoji", "\U0001f389"),
        ("non_leading_dot", "a.b"),
        ("dash", "a-b"),
        ("underscore", "a_b"),
        ("backslash", "a\\b"),
        ("forward_slash", "a/b"),
        ("bom", "\ufeff"),
        ("zwsp", "\u200b"),
        ("zwj", "\u200d"),
        ("ltr_mark", "\u200e"),
        ("rtl_mark", "\u200f"),
        ("nbsp", "\u00a0"),
        ("en_space", "\u2000"),
        ("em_space", "\u2003"),
        ("brackets", "[test]"),
        ("braces", "{test}"),
        ("quotes", '"test"'),
        ("fullwidth_dollar", "\uff04test"),
        ("small_dollar", "\ufe69test"),
    ]
]


def _suffix_to_byte_limit(char: str) -> Callable[[str, str], str]:
    """Return a suffix lambda that fills the namespace to exactly 255 bytes."""
    char_bytes = len(char.encode())
    return lambda db, coll: char * ((255 - len(f"{db}.{coll}".encode())) // char_bytes)


# Property [Namespace Byte Limit]: the full namespace (db.collection)
# is limited to 255 bytes, counting by byte length not character count.
NAMESPACE_BYTE_LIMIT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ascii_at_limit",
        target_collection=NamedCollection(suffix=_suffix_to_byte_limit("x")),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "short_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="1-byte ASCII chars at exactly 255 byte namespace should succeed",
    ),
    CommandTestCase(
        "two_byte_at_limit",
        target_collection=NamedCollection(suffix=_suffix_to_byte_limit("\u00e9")),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "short_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="2-byte UTF-8 chars at exactly 255 byte namespace should succeed",
    ),
    CommandTestCase(
        "three_byte_at_limit",
        target_collection=NamedCollection(suffix=_suffix_to_byte_limit("\u4e2d")),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "short_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="3-byte UTF-8 chars at exactly 255 byte namespace should succeed",
    ),
    CommandTestCase(
        "four_byte_at_limit",
        target_collection=NamedCollection(suffix=_suffix_to_byte_limit("\U0001f389")),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "short_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="4-byte UTF-8 chars at exactly 255 byte namespace should succeed",
    ),
]

NAMESPACE_TESTS: list[CommandTestCase] = (
    SOURCE_NAME_VALIDATION_ERROR_TESTS
    + DEST_NAME_VALIDATION_ERROR_TESTS
    + DEST_NAME_SYSTEM_ACCEPTED_TESTS
    + VALID_NAME_TESTS
    + NAMESPACE_BYTE_LIMIT_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(NAMESPACE_TESTS))
def test_clone_collection_as_capped_namespace(database_client, collection, test):
    """Test cloneCollectionAsCapped namespace validation."""
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
