"""Tests for validateDBMetadata collection name acceptance and validation errors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Collection Name Acceptance]: the collection filter accepts any
# string value without validation beyond leading dot and null byte checks.
VALIDATE_DB_METADATA_COLLECTION_NAME_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "coll_name_dollar_prefix",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "$test",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept dollar-prefix collection name",
    ),
    CommandTestCase(
        "coll_name_bare_dollar",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "$",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept bare dollar sign as collection name",
    ),
    CommandTestCase(
        "coll_name_double_dollar",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "$$",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept double-dollar collection name",
    ),
    CommandTestCase(
        "coll_name_space",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept space in collection name",
    ),
    CommandTestCase(
        "coll_name_tab",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\tb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept tab in collection name",
    ),
    CommandTestCase(
        "coll_name_newline",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\nb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept newline in collection name",
    ),
    CommandTestCase(
        "coll_name_carriage_return",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\rb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept carriage return in collection name",
    ),
    CommandTestCase(
        # U+00A0 (non-breaking space).
        "coll_name_nbsp",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\u00a0b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept NBSP in collection name",
    ),
    CommandTestCase(
        # U+2000 (en space).
        "coll_name_en_space",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\u2000b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept en space in collection name",
    ),
    CommandTestCase(
        # U+2003 (em space).
        "coll_name_em_space",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\u2003b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept em space in collection name",
    ),
    CommandTestCase(
        "coll_name_non_leading_dot",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a.b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept non-leading dot in collection name",
    ),
    CommandTestCase(
        "coll_name_system_prefix",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "system.buckets",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept system.* prefix in collection name",
    ),
    CommandTestCase(
        "coll_name_forward_slash",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a/b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept forward slash in collection name",
    ),
    CommandTestCase(
        "coll_name_backslash",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\\b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept backslash in collection name",
    ),
    CommandTestCase(
        "coll_name_curly_braces",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "{a}",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept curly braces in collection name",
    ),
    CommandTestCase(
        "coll_name_square_brackets",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "[a]",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept square brackets in collection name",
    ),
    CommandTestCase(
        "coll_name_double_quote",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": 'a"b',
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept double quote in collection name",
    ),
    CommandTestCase(
        "coll_name_cjk",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "\u4e00\u4e01\u4e02",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept CJK characters in collection name",
    ),
    CommandTestCase(
        "coll_name_emoji",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "\U0001f600",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept emoji in collection name",
    ),
    CommandTestCase(
        # U+0065 (e) + U+0301 (combining acute accent).
        "coll_name_combining_char",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "e\u0301",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept combining characters in collection name",
    ),
    CommandTestCase(
        # U+00E9 (precomposed e-acute).
        "coll_name_precomposed",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "\u00e9",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept precomposed Unicode in collection name",
    ),
    CommandTestCase(
        "coll_name_greek",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "\u03b1\u03b2\u03b3",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept Greek characters in collection name",
    ),
    CommandTestCase(
        "coll_name_cyrillic",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "\u0410\u0411\u0412",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept Cyrillic characters in collection name",
    ),
    CommandTestCase(
        # U+FEFF (BOM / zero-width no-break space).
        "coll_name_bom",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "\ufefftest",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept BOM in collection name",
    ),
    CommandTestCase(
        # U+200B (zero-width space).
        "coll_name_zwsp",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\u200bb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept ZWSP in collection name",
    ),
    CommandTestCase(
        # U+200D (zero-width joiner).
        "coll_name_zwj",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\u200db",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept ZWJ in collection name",
    ),
    CommandTestCase(
        "coll_name_10000_chars",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "x" * 10_000,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept collection names exceeding 255 bytes",
    ),
]

# Property [Collection Name Validation Errors]: empty string, leading
# dot, and null byte in the collection name produce an invalid namespace
# error.
VALIDATE_DB_METADATA_COLLECTION_NAME_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "coll_name_err_empty_string",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject empty string collection name",
    ),
    CommandTestCase(
        "coll_name_err_leading_dot",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": ".abc",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject leading dot in collection name",
    ),
    CommandTestCase(
        "coll_name_err_null_byte",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": "a\x00b",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject null byte in collection name",
    ),
]

VALIDATE_DB_METADATA_COLLECTION_NAME_TESTS: list[CommandTestCase] = (
    VALIDATE_DB_METADATA_COLLECTION_NAME_ACCEPTANCE_TESTS
    + VALIDATE_DB_METADATA_COLLECTION_NAME_VALIDATION_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_COLLECTION_NAME_TESTS))
def test_validateDBMetadata_collection_name(database_client, collection, test):
    """Test validateDBMetadata collection name acceptance and validation errors."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
