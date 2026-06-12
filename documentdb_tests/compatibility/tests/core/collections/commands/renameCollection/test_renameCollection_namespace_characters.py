"""Tests for renameCollection valid characters in namespace."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Valid Characters]: collection names accept any character
# except null byte (U+0000), leading dot, and ASCII dollar sign.
RENAME_VALID_CHARACTERS_TESTS: list[CommandTestCase] = [
    # Control characters (SOH through DEL, excluding null).
    CommandTestCase(
        "valid_chars_control_soh",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\x01soh",
        },
        expected={"ok": 1.0},
        msg="SOH (U+0001) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_control_del",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\x7fdel",
        },
        expected={"ok": 1.0},
        msg="DEL (U+007F) should be accepted in collection name",
    ),
    # Invisible/zero-width characters in collection names.
    CommandTestCase(
        "valid_chars_bom_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\ufeffbom",
        },
        expected={"ok": 1.0},
        msg="BOM (U+FEFF) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_zwsp_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u200bzwsp",
        },
        expected={"ok": 1.0},
        msg="ZWSP (U+200B) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_zwj_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u200dzwj",
        },
        expected={"ok": 1.0},
        msg="ZWJ (U+200D) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_ltr_mark_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u200eltr",
        },
        expected={"ok": 1.0},
        msg="LTR mark (U+200E) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_rtl_mark_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u200frtl",
        },
        expected={"ok": 1.0},
        msg="RTL mark (U+200F) should be accepted in collection name",
    ),
    # Invisible/zero-width characters in database names.
    CommandTestCase(
        "valid_chars_bom_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\ufeff.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="BOM (U+FEFF) should be accepted in database name",
    ),
    CommandTestCase(
        "valid_chars_zwsp_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\u200b.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="ZWSP (U+200B) should be accepted in database name",
    ),
    CommandTestCase(
        "valid_chars_zwj_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\u200d.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="ZWJ (U+200D) should be accepted in database name",
    ),
    CommandTestCase(
        "valid_chars_ltr_mark_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\u200e.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="LTR mark (U+200E) should be accepted in database name",
    ),
    CommandTestCase(
        "valid_chars_rtl_mark_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\u200f.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="RTL mark (U+200F) should be accepted in database name",
    ),
    # Unicode whitespace in database names.
    CommandTestCase(
        "valid_chars_nbsp_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\u00a0.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="NBSP (U+00A0) should be accepted in database name",
    ),
    CommandTestCase(
        "valid_chars_en_space_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\u2002.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="En space (U+2002) should be accepted in database name",
    ),
    CommandTestCase(
        "valid_chars_em_space_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}\u2003.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Em space (U+2003) should be accepted in database name",
    ),
    # Unicode whitespace in collection names.
    CommandTestCase(
        "valid_chars_nbsp_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u00a0nbsp",
        },
        expected={"ok": 1.0},
        msg="NBSP (U+00A0) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_en_space_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u2002ensp",
        },
        expected={"ok": 1.0},
        msg="En space (U+2002) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_em_space_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u2003emsp",
        },
        expected={"ok": 1.0},
        msg="Em space (U+2003) should be accepted in collection name",
    ),
    # Multi-byte Unicode, emoji, non-leading dots, and special punctuation.
    CommandTestCase(
        "valid_chars_emoji",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\U0001f600emoji",
        },
        expected={"ok": 1.0},
        msg="Emoji (U+1F600) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_non_leading_dot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_mid.dot",
        },
        expected={"ok": 1.0},
        msg="Non-leading dot should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_special_punctuation",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_!@#%^&()",
        },
        expected={"ok": 1.0},
        msg="Special punctuation (!@#%^&()) should be accepted in collection name",
    ),
    CommandTestCase(
        "valid_chars_multibyte_cjk",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_\u4e16\u754c",
        },
        expected={"ok": 1.0},
        # U+4E16 U+754C = Chinese characters for "world".
        msg="Multi-byte CJK characters should be accepted in collection name",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_VALID_CHARACTERS_TESTS))
def test_renameCollection_namespace_characters(
    database_client, collection, register_db_cleanup, test
):
    """Test renameCollection valid characters in namespace."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
