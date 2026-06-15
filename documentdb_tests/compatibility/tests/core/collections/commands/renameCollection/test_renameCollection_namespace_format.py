"""Tests for renameCollection namespace format validation."""

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
from documentdb_tests.framework.error_codes import (
    ILLEGAL_OPERATION_ERROR,
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Namespace Format Validation - Accepted Characters]: characters
# that are not explicitly forbidden in database or collection names are
# accepted without error.
RENAME_NAMESPACE_FORMAT_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "tab_in_target_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"te\tst.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Tab character in db name should be accepted",
    ),
    CommandTestCase(
        "question_mark_in_target_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"te?st.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Question mark in db name should be accepted",
    ),
    CommandTestCase(
        "asterisk_in_target_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"te*st.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Asterisk in db name should be accepted",
    ),
    CommandTestCase(
        "angle_brackets_in_target_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"te<>st.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Angle brackets in db name should be accepted",
    ),
    CommandTestCase(
        "pipe_in_target_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"te|st.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Pipe in db name should be accepted",
    ),
    CommandTestCase(
        "colon_in_target_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"te:st.{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Colon in db name should be accepted",
    ),
    CommandTestCase(
        "fullwidth_dollar_in_target_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.\uff04{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Fullwidth dollar U+FF04 should be accepted",
    ),
    CommandTestCase(
        "small_dollar_in_target_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.\ufe69{ctx.collection}_dest",
        },
        expected={"ok": 1.0},
        msg="Small dollar U+FE69 should be accepted",
    ),
]

# Property [Namespace Format Validation - Invalid Format]: a namespace
# must contain a dot separator with non-empty database and collection
# portions, must not contain null bytes or forbidden characters in the
# database name, and the collection must not start with a dot.
RENAME_NAMESPACE_FORMAT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "source_no_dot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "nodot",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source without dot should be rejected",
    ),
    CommandTestCase(
        "source_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty source namespace should be rejected",
    ),
    CommandTestCase(
        "source_empty_db_portion",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ".coll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source with empty database portion should be rejected",
    ),
    CommandTestCase(
        "source_empty_coll_portion",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "test.",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source with empty collection portion should be rejected",
    ),
    CommandTestCase(
        "source_coll_starts_with_dot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "test..coll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source collection starting with dot should be rejected",
    ),
    CommandTestCase(
        "source_null_byte",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "test.co\x00ll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source with null byte should be rejected",
    ),
    CommandTestCase(
        "source_forward_slash_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "te/st.coll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source with forward slash in db name should be rejected",
    ),
    CommandTestCase(
        "source_backslash_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "te\\st.coll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source with backslash in db name should be rejected",
    ),
    CommandTestCase(
        "source_space_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "te st.coll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source with space in db name should be rejected",
    ),
    CommandTestCase(
        "source_double_quote_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": 'te"st.coll',
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source with double quote in db name should be rejected",
    ),
    CommandTestCase(
        "target_no_dot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "nodot",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target without dot should be rejected",
    ),
    CommandTestCase(
        "target_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty target namespace should be rejected",
    ),
    CommandTestCase(
        "target_empty_db_portion",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": ".coll",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target with empty database portion should be rejected",
    ),
    CommandTestCase(
        "target_empty_coll_portion",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "test.",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target with empty collection portion should be rejected",
    ),
    CommandTestCase(
        "target_coll_starts_with_dot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "test..coll",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target collection starting with dot should be rejected",
    ),
    CommandTestCase(
        "target_null_byte",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "test.co\x00ll",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target with null byte should be rejected",
    ),
    CommandTestCase(
        "target_forward_slash_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "te/st.coll",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target with forward slash in db name should be rejected",
    ),
    CommandTestCase(
        "target_backslash_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "te\\st.coll",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target with backslash in db name should be rejected",
    ),
    CommandTestCase(
        "target_space_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "te st.coll",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target with space in db name should be rejected",
    ),
    CommandTestCase(
        "target_double_quote_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": 'te"st.coll',
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target with double quote in db name should be rejected",
    ),
]

# Property [Namespace Format Validation - Dollar Sign]: ASCII dollar
# sign (U+0024) anywhere in the database or collection name produces
# an illegal-operation error; this applies to both source and target.
RENAME_NAMESPACE_DOLLAR_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "source_dollar_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "te$st.coll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Source with dollar in db name should be rejected",
    ),
    CommandTestCase(
        "source_dollar_in_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": "test.$coll",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Source with dollar in collection name should be rejected",
    ),
    CommandTestCase(
        "target_dollar_in_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "te$st.dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Target with dollar in db name should be rejected",
    ),
    CommandTestCase(
        "target_dollar_in_coll",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": "test.$dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Target with dollar in collection name should be rejected",
    ),
]

RENAME_NAMESPACE_FORMAT_TESTS: list[CommandTestCase] = (
    RENAME_NAMESPACE_FORMAT_ACCEPTED_TESTS
    + RENAME_NAMESPACE_FORMAT_ERROR_TESTS
    + RENAME_NAMESPACE_DOLLAR_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_NAMESPACE_FORMAT_TESTS))
def test_renameCollection_namespace_format(database_client, collection, register_db_cleanup, test):
    """Test renameCollection namespace format validation."""
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
