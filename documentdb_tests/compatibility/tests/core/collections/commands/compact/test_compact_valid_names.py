"""Tests for compact command collection name acceptance."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    NamedCollection,
)

# Property [Collection Name Acceptance - Valid Patterns]: compact accepts
# collection names with arbitrary valid characters and encodings up to the
# namespace byte limit.
COMPACT_VALID_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "digits_only",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_999"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with digits should be accepted",
    ),
    CommandTestCase(
        "space",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_ _"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with space should be accepted",
    ),
    CommandTestCase(
        "tab",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\t"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with tab should be accepted",
    ),
    CommandTestCase(
        "newline",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\n"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with newline should be accepted",
    ),
    CommandTestCase(
        "carriage_return",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\r"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with carriage return should be accepted",
    ),
    CommandTestCase(
        "control_char_u0001",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\x01"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with control character U+0001 should be accepted",
    ),
    CommandTestCase(
        "control_char_u001f",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\x1f"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with control character U+001F should be accepted",
    ),
    CommandTestCase(
        "cjk",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u4e2d\u6587"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with CJK characters should be accepted",
    ),
    CommandTestCase(
        "emoji",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\U0001f600"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with emoji should be accepted",
    ),
    CommandTestCase(
        "zwj_emoji_sequence",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(
            suffix="_\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466"
        ),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with ZWJ emoji sequence should be accepted",
    ),
    CommandTestCase(
        "non_leading_dot",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_a.b"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with non-leading dot should be accepted",
    ),
    CommandTestCase(
        "dash",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_a-b"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with dash should be accepted",
    ),
    CommandTestCase(
        "backslash",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_a\\b"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with backslash should be accepted",
    ),
    CommandTestCase(
        "forward_slash",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_a/b"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with forward slash should be accepted",
    ),
    CommandTestCase(
        "bom",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\ufeff"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with BOM U+FEFF should be accepted",
    ),
    CommandTestCase(
        "zwsp",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u200b"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with ZWSP U+200B should be accepted",
    ),
    CommandTestCase(
        "zwj",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u200d"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with ZWJ U+200D should be accepted",
    ),
    CommandTestCase(
        "ltr_mark",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u200e"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with LTR mark U+200E should be accepted",
    ),
    CommandTestCase(
        "nbsp",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u00a0"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with NBSP U+00A0 should be accepted",
    ),
    CommandTestCase(
        "en_space",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u2000"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with en space U+2000 should be accepted",
    ),
    CommandTestCase(
        "punctuation",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix='_!@#%^&(){}[]"'),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with punctuation should be accepted",
    ),
    CommandTestCase(
        "precomposed_e_acute",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u00e9"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with precomposed U+00E9 should be accepted",
    ),
    CommandTestCase(
        "combining_e_acute",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_e\u0301"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with combining sequence should be accepted",
    ),
    CommandTestCase(
        "two_byte_utf8",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u00f1"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with 2-byte UTF-8 character should be accepted",
    ),
    CommandTestCase(
        "three_byte_utf8",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\u2603"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with 3-byte UTF-8 character should be accepted",
    ),
    CommandTestCase(
        "four_byte_utf8",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(suffix="_\U00010000"),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection name with 4-byte UTF-8 character should be accepted",
    ),
    CommandTestCase(
        "namespace_at_255_byte_limit",
        docs=[{"_id": 1}],
        target_collection=NamedCollection(
            suffix=lambda db_name, coll_name: "a"
            * (255 - len(db_name.encode("utf-8")) - 1 - len(coll_name))
        ),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Namespace at 255-byte limit should succeed",
    ),
]


@pytest.mark.requires(unforced_compact=True)
@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_VALID_NAME_TESTS))
def test_compact_valid_names(database_client, collection, test):
    """Test compact command accepts valid collection names."""
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
