"""Tests for renameCollection writeConcern provenance, getLastError, and unknown fields."""

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Sub-Field - provenance Type]: non-string and
# non-null types produce a type mismatch error.
RENAME_WC_PROVENANCE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_provenance_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"provenance as {tid} should produce TypeMismatch",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["clientSupplied"]),
        ("object", {"p": "clientSupplied"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [writeConcern Sub-Field - provenance Enum Validation]: invalid
# enum strings and case-sensitive mismatches produce a bad-value error.
RENAME_WC_PROVENANCE_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_provenance_invalid_enum",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="provenance='invalid' should be rejected",
    ),
    CommandTestCase(
        "wc_provenance_case_sensitive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": "ClientSupplied"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="provenance='ClientSupplied' (wrong case) should be rejected",
    ),
    CommandTestCase(
        "wc_provenance_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="provenance='' (empty string) should be rejected",
    ),
]

# Property [writeConcern Sub-Field - provenance Success]: valid enum
# strings and null are accepted.
RENAME_WC_PROVENANCE_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_provenance_client_supplied",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": "clientSupplied"},
        },
        expected={"ok": 1.0},
        msg="provenance='clientSupplied' should be accepted",
    ),
    CommandTestCase(
        "wc_provenance_implicit_default",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": "implicitDefault"},
        },
        expected={"ok": 1.0},
        msg="provenance='implicitDefault' should be accepted",
    ),
    CommandTestCase(
        "wc_provenance_custom_default",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": "customDefault"},
        },
        expected={"ok": 1.0},
        msg="provenance='customDefault' should be accepted",
    ),
    CommandTestCase(
        "wc_provenance_get_last_error_defaults",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": "getLastErrorDefaults"},
        },
        expected={"ok": 1.0},
        msg="provenance='getLastErrorDefaults' should be accepted",
    ),
    CommandTestCase(
        "wc_provenance_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"provenance": None},
        },
        expected={"ok": 1.0},
        msg="provenance=null should be accepted",
    ),
]

# Property [writeConcern Sub-Field - getLastError]: accepts any BSON
# type and any value without validation.
RENAME_WC_GETLASTERROR_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_getlasterror_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"getLastError": "anything"},
        },
        expected={"ok": 1.0},
        msg="getLastError as string should be accepted",
    ),
    CommandTestCase(
        "wc_getlasterror_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"getLastError": 123},
        },
        expected={"ok": 1.0},
        msg="getLastError as int should be accepted",
    ),
    CommandTestCase(
        "wc_getlasterror_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"getLastError": None},
        },
        expected={"ok": 1.0},
        msg="getLastError=null should be accepted",
    ),
]

# Property [writeConcern Sub-Field - Unrecognized Fields]: unknown
# fields in writeConcern produce an unrecognized-field error.
RENAME_WC_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field in writeConcern should be rejected",
    ),
    CommandTestCase(
        "wc_unknown_field_with_w",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": 1, "unknownField": "x"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field alongside valid w should be rejected",
    ),
]

RENAME_WC_PROVENANCE_TESTS: list[CommandTestCase] = (
    RENAME_WC_PROVENANCE_TYPE_ERROR_TESTS
    + RENAME_WC_PROVENANCE_ENUM_ERROR_TESTS
    + RENAME_WC_PROVENANCE_SUCCESS_TESTS
    + RENAME_WC_GETLASTERROR_SUCCESS_TESTS
    + RENAME_WC_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_WC_PROVENANCE_TESTS))
def test_renameCollection_wc_provenance(database_client, collection, register_db_cleanup, test):
    """Test renameCollection writeConcern provenance, getLastError, and unknown fields."""
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
