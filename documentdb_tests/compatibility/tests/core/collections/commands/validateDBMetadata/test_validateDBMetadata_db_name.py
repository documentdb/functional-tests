"""Tests for validateDBMetadata db name acceptance and validation errors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EMPTY_DB_NAME_ERROR,
    INVALID_DB_NAME_ERROR,
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [db Name Acceptance]: any string that passes standard database
# name validation is accepted as the db filter without error.
VALIDATE_DB_METADATA_DB_NAME_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "db_name_single_char",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept single-character db name",
    ),
    CommandTestCase(
        "db_name_63_bytes_ascii",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a" * 63,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept 63-byte ASCII db name",
    ),
    CommandTestCase(
        # 21 CJK characters at 3 bytes each = 63 UTF-8 bytes.
        "db_name_63_bytes_cjk",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "\u4e00" * 21,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept 63 UTF-8 bytes of CJK characters",
    ),
    CommandTestCase(
        "db_name_tab",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\tb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept tab in db name",
    ),
    CommandTestCase(
        "db_name_newline",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\nb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept newline in db name",
    ),
    CommandTestCase(
        "db_name_carriage_return",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\rb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept carriage return in db name",
    ),
    CommandTestCase(
        "db_name_dollar_prefix",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "$admin",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept dollar-prefix db name",
    ),
    CommandTestCase(
        "db_name_bare_dollar",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "$",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept bare dollar sign as db name",
    ),
    CommandTestCase(
        "db_name_double_dollar",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "$$",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept double-dollar db name",
    ),
    CommandTestCase(
        "db_name_control_char_01",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\x01b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept U+0001 control character in db name",
    ),
    CommandTestCase(
        "db_name_control_char_1f",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\x1fb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept U+001F control character in db name",
    ),
    CommandTestCase(
        "db_name_control_char_7f",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\x7fb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept U+007F (DEL) in db name",
    ),
    CommandTestCase(
        "db_name_emoji",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "\U0001f600",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept emoji in db name",
    ),
    CommandTestCase(
        # U+0065 (e) + U+0301 (combining acute accent).
        "db_name_combining_char",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "e\u0301",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept combining characters in db name",
    ),
    CommandTestCase(
        # U+00E9 (precomposed e-acute).
        "db_name_precomposed",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "\u00e9",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept precomposed Unicode in db name",
    ),
    CommandTestCase(
        # U+00A0 (non-breaking space).
        "db_name_nbsp",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\u00a0b",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept NBSP in db name",
    ),
    CommandTestCase(
        # U+FEFF (BOM / zero-width no-break space).
        "db_name_bom",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "\ufefftest",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept BOM in db name",
    ),
    CommandTestCase(
        # U+200B (zero-width space).
        "db_name_zwsp",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\u200bb",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept ZWSP in db name",
    ),
    CommandTestCase(
        # U+200F (right-to-left mark).
        "db_name_rtl_mark",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "\u200ftest",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept directional marks in db name",
    ),
    CommandTestCase(
        "db_name_admin",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "admin",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept system db name 'admin'",
    ),
    CommandTestCase(
        "db_name_local",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "local",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept system db name 'local'",
    ),
    CommandTestCase(
        "db_name_config",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "config",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept system db name 'config'",
    ),
]

# Property [db Name Validation Errors]: db names that violate standard
# naming rules are rejected with the appropriate error.
VALIDATE_DB_METADATA_DB_NAME_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "db_name_err_empty_string",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "",
        },
        error_code=EMPTY_DB_NAME_ERROR,
        msg="validateDBMetadata should reject empty string db name",
    ),
    CommandTestCase(
        "db_name_err_dot_middle",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a.b",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject dot in middle of db name",
    ),
    CommandTestCase(
        "db_name_err_dot_leading",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ".abc",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject leading dot in db name",
    ),
    CommandTestCase(
        "db_name_err_dot_trailing",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "abc.",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject trailing dot in db name",
    ),
    CommandTestCase(
        "db_name_err_null_byte",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\x00b",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject null byte in db name",
    ),
    CommandTestCase(
        # 64 ASCII bytes exceeds the 63-byte limit.
        "db_name_err_exceeds_63_bytes",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a" * 64,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject db name exceeding 63 UTF-8 bytes",
    ),
    CommandTestCase(
        # 22 CJK characters at 3 bytes each = 66 UTF-8 bytes.
        "db_name_err_exceeds_63_bytes_cjk",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "\u4e00" * 22,
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validateDBMetadata should reject CJK db name exceeding 63 UTF-8 bytes",
    ),
    CommandTestCase(
        "db_name_err_space",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a b",
        },
        error_code=INVALID_DB_NAME_ERROR,
        msg="validateDBMetadata should reject ASCII space in db name",
    ),
    CommandTestCase(
        "db_name_err_forward_slash",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a/b",
        },
        error_code=INVALID_DB_NAME_ERROR,
        msg="validateDBMetadata should reject forward slash in db name",
    ),
    CommandTestCase(
        "db_name_err_backslash",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "a\\b",
        },
        error_code=INVALID_DB_NAME_ERROR,
        msg="validateDBMetadata should reject backslash in db name",
    ),
    CommandTestCase(
        "db_name_err_double_quote",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": 'a"b',
        },
        error_code=INVALID_DB_NAME_ERROR,
        msg="validateDBMetadata should reject double quote in db name",
    ),
]

VALIDATE_DB_METADATA_DB_NAME_TESTS: list[CommandTestCase] = (
    VALIDATE_DB_METADATA_DB_NAME_ACCEPTANCE_TESTS
    + VALIDATE_DB_METADATA_DB_NAME_VALIDATION_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_DB_NAME_TESTS))
def test_validateDBMetadata_db_name(database_client, collection, test):
    """Test validateDBMetadata db name acceptance and validation errors."""
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
