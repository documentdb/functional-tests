"""Tests for convertToCapped command - namespace and collection name validation."""

import datetime

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_NAMESPACE_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    NamedCollection,
    SystemBucketsCollection,
    SystemViewsCollection,
    TargetDatabase,
)

# Property [Collection Name Max Length Success]: the maximum accepted name
# length (db_name_len + col_name_len + 26 <= 255) succeeds.
NAME_MAX_LENGTH_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_at_max_length",
        target_collection=NamedCollection(
            suffix=lambda db_name, coll_name: "x"
            * (255 - len(db_name.encode("utf-8")) - 26 - len(coll_name))
        ),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Name at maximum byte length should be accepted",
    ),
]

# Property [Collection Name Valid Characters]: convertToCapped accepts
# collection names containing special and non-ASCII characters.
NAME_VALID_CHARS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hyphen",
        target_collection=NamedCollection(suffix="-name"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Hyphenated name should be accepted",
    ),
    CommandTestCase(
        "space",
        target_collection=NamedCollection(suffix=" space"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Space in name should be accepted",
    ),
    CommandTestCase(
        "non_leading_dot",
        target_collection=NamedCollection(suffix=".dotted"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Non-leading dot in name should be accepted",
    ),
    CommandTestCase(
        "backslash",
        target_collection=NamedCollection(suffix="\\x"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Backslash in name should be accepted",
    ),
    CommandTestCase(
        "braces",
        target_collection=NamedCollection(suffix="{x}"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Braces in name should be accepted",
    ),
    CommandTestCase(
        "brackets",
        target_collection=NamedCollection(suffix="[x]"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Brackets in name should be accepted",
    ),
    CommandTestCase(
        "at_sign",
        target_collection=NamedCollection(suffix="@x"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="At sign in name should be accepted",
    ),
    CommandTestCase(
        "hash",
        target_collection=NamedCollection(suffix="#x"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Hash in name should be accepted",
    ),
    CommandTestCase(
        "percent",
        target_collection=NamedCollection(suffix="%x"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Percent in name should be accepted",
    ),
    CommandTestCase(
        "unicode_2byte",
        target_collection=NamedCollection(suffix="\u00e9"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="2-byte unicode in name should be accepted",
    ),
    CommandTestCase(
        "unicode_3byte",
        target_collection=NamedCollection(suffix="\u4e16"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="3-byte unicode in name should be accepted",
    ),
    CommandTestCase(
        "unicode_4byte",
        target_collection=NamedCollection(suffix="\U0001f600"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="4-byte unicode in name should be accepted",
    ),
    CommandTestCase(
        "control_x01",
        target_collection=NamedCollection(suffix="\x01"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Control char 0x01 in name should be accepted",
    ),
    CommandTestCase(
        "tab",
        target_collection=NamedCollection(suffix="\t"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Tab character in name should be accepted",
    ),
    CommandTestCase(
        "newline",
        target_collection=NamedCollection(suffix="\n"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Newline character in name should be accepted",
    ),
]

# Property [Collection Name Type Errors]: all non-string types for the
# convertToCapped field produce an invalid namespace error.
NAME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"name_{id}",
        docs=None,
        command=lambda ctx, v=val: {"convertToCapped": v, "size": 4096},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"{id} name should produce an invalid namespace error",
    )
    for id, val in [
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 3.14),
        ("decimal128", Decimal128("3.14")),
        ("bool", True),
        ("null", None),
        ("array", ["a", "b"]),
        ("object", {"key": "val"}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"hello")),
        ("regex", Regex("pat", "i")),
        ("code", Code("function() {}")),
        ("code_with_scope", Code("function() {}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("expression_object", {"$concat": ["a", "b"]}),
    ]
]

# Property [Collection Name Value Errors]: invalid string values for the
# collection name (empty, null byte, leading dot) produce an invalid
# namespace error.
NAME_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_empty_string",
        docs=None,
        command=lambda ctx: {"convertToCapped": "", "size": 4096},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty string name should produce an invalid namespace error",
    ),
    CommandTestCase(
        "name_null_byte",
        docs=None,
        command=lambda ctx: {"convertToCapped": "test\x00name", "size": 4096},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Name with null byte should produce an invalid namespace error",
    ),
    CommandTestCase(
        "name_leading_dot",
        docs=None,
        command=lambda ctx: {"convertToCapped": ".leadingdot", "size": 4096},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Name starting with a dot should produce an invalid namespace error",
    ),
]

# Property [Collection Name Dollar Prefix]: dollar-sign prefixed strings
# are treated as literal collection names and produce a namespace-not-found
# error when the collection does not exist.
NAME_DOLLAR_PREFIX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dollar",
        docs=None,
        command=lambda ctx: {"convertToCapped": "$", "size": 4096},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Dollar-sign name should be treated as literal, not field path",
    ),
    CommandTestCase(
        "double_dollar",
        docs=None,
        command=lambda ctx: {"convertToCapped": "$$", "size": 4096},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Double dollar name should be treated as literal, not variable",
    ),
    CommandTestCase(
        "dollar_test",
        docs=None,
        command=lambda ctx: {"convertToCapped": "$test", "size": 4096},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Dollar-prefixed name should be treated as literal collection name",
    ),
    CommandTestCase(
        "dollar_cmd",
        docs=None,
        command=lambda ctx: {"convertToCapped": "$cmd", "size": 4096},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="$cmd should be treated as literal name, not special command namespace",
    ),
]

# Property [System Namespace Errors]: system.buckets.* produces an
# illegal-operation error; system.views produces a bad-value error.
SYSTEM_NAMESPACE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_buckets",
        target_collection=SystemBucketsCollection(),
        docs=None,
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.buckets.* should produce an illegal-operation error",
    ),
    CommandTestCase(
        "system_views",
        target_collection=SystemViewsCollection(),
        docs=None,
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        error_code=BAD_VALUE_ERROR,
        msg="system.views should produce a bad-value error",
    ),
    CommandTestCase(
        "nonexistent_database",
        target_collection=TargetDatabase(suffix="nonexist_xyz"),
        docs=None,
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Non-existent database should produce a namespace-not-found error",
    ),
]

# Property [Collection Name Max Length Error]: exceeding the byte-length
# limit produces an invalid namespace error.
NAME_MAX_LENGTH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_exceeds_max_length",
        target_collection=NamedCollection(
            suffix=lambda db_name, coll_name: "x"
            * (255 - len(db_name.encode("utf-8")) - 26 - len(coll_name) + 1)
        ),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Name exceeding byte-length limit should produce an invalid namespace error",
    ),
]

# Property [Collection Name Case Sensitivity]: collection names are
# case-sensitive; a name with wrong case produces a namespace-not-found
# error rather than matching the existing collection.
NAME_CASE_SENSITIVITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wrong_case_not_found",
        target_collection=NamedCollection(suffix="_TestColl"),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection.lower(),
            "size": 4096,
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Wrong case name should produce not-found error, not match",
    ),
]

CONVERT_TO_CAPPED_NAMESPACE_TESTS: list[CommandTestCase] = (
    NAME_MAX_LENGTH_SUCCESS_TESTS
    + NAME_VALID_CHARS_TESTS
    + NAME_TYPE_ERROR_TESTS
    + NAME_VALUE_ERROR_TESTS
    + NAME_DOLLAR_PREFIX_TESTS
    + SYSTEM_NAMESPACE_ERROR_TESTS
    + NAME_MAX_LENGTH_ERROR_TESTS
    + NAME_CASE_SENSITIVITY_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CONVERT_TO_CAPPED_NAMESPACE_TESTS))
def test_convert_to_capped_namespace(database_client, collection, test):
    """Test convertToCapped command namespace and collection name validation."""
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
