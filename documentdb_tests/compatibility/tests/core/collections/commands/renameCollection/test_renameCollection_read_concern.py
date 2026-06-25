"""Tests for renameCollection readConcern option."""

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.binary import Binary

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
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [readConcern Document Acceptance]: readConcern accepts a
# valid document with recognized sub-fields.
RENAME_RC_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_empty_document",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {},
        },
        expected={"ok": 1.0},
        msg="readConcern={} should succeed",
    ),
    CommandTestCase(
        "rc_level_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0},
        msg="readConcern level 'local' should succeed",
    ),
    CommandTestCase(
        "rc_provenance_client_supplied",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"provenance": "clientSupplied"},
        },
        expected={"ok": 1.0},
        msg="readConcern provenance 'clientSupplied' should succeed",
    ),
    CommandTestCase(
        "rc_provenance_implicit_default",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"provenance": "implicitDefault"},
        },
        expected={"ok": 1.0},
        msg="readConcern provenance 'implicitDefault' should succeed",
    ),
    CommandTestCase(
        "rc_provenance_custom_default",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"provenance": "customDefault"},
        },
        expected={"ok": 1.0},
        msg="readConcern provenance 'customDefault' should succeed",
    ),
    CommandTestCase(
        "rc_provenance_get_last_error_defaults",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"provenance": "getLastErrorDefaults"},
        },
        expected={"ok": 1.0},
        msg="readConcern provenance 'getLastErrorDefaults' should succeed",
    ),
    CommandTestCase(
        "rc_provenance_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"provenance": None},
        },
        expected={"ok": 1.0},
        msg="readConcern provenance null should succeed",
    ),
]

# Property [readConcern Type Validation]: non-document types for
# readConcern produce a type mismatch error.
RENAME_RC_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"rc_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"readConcern as {tid} should produce TypeMismatch",
    )
    for tid, val in [
        ("string", "local"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["local"]),
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

# Property [readConcern Level Unsupported]: levels other than "local"
# produce an invalid-options error.
RENAME_RC_LEVEL_UNSUPPORTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"rc_level_{level}",
        docs=[{"_id": 1}],
        command=lambda ctx, lvl=level: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": lvl},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"readConcern level '{level}' should be rejected as unsupported",
    )
    for level in ["majority", "available", "linearizable", "snapshot"]
]

# Property [readConcern Null Acceptance]: readConcern=null and
# readConcern.level=null are accepted and treated as unset.
RENAME_RC_NULL_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": None,
        },
        expected={"ok": 1.0},
        msg="readConcern=null should succeed",
    ),
    CommandTestCase(
        "rc_level_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": None},
        },
        expected={"ok": 1.0},
        msg="readConcern level null should succeed",
    ),
]

# Property [readConcern Level Enum Validation]: invalid level strings
# produce a BadValue error; values are case-sensitive.
RENAME_RC_LEVEL_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_level_invalid_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": "bogus"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid readConcern level string should be rejected",
    ),
    CommandTestCase(
        "rc_level_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Empty string readConcern level should be rejected",
    ),
    CommandTestCase(
        "rc_level_case_sensitive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": "Local"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="readConcern level 'Local' (wrong case) should be rejected",
    ),
]

# Property [readConcern Level Type Validation]: non-string types for
# readConcern.level produce a type mismatch error.
RENAME_RC_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"rc_level_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"readConcern level as {tid} should produce TypeMismatch",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["local"]),
        ("object", {"nested": "local"}),
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

# Property [readConcern Unknown Fields]: unknown sub-fields in
# readConcern produce an unrecognized-field error.
RENAME_RC_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"level": "local", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown sub-field in readConcern should be rejected",
    ),
]

# Property [readConcern Provenance Validation]: invalid provenance
# string produces a bad-value error; non-string provenance produces
# a type mismatch error.
RENAME_RC_PROVENANCE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_provenance_invalid_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid readConcern provenance string should be rejected",
    ),
    CommandTestCase(
        "rc_provenance_type_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"provenance": 123},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern provenance as int should produce TypeMismatch",
    ),
]

# Property [readConcern afterClusterTime]: afterClusterTime with a valid
# Timestamp produces an illegal-operation error on standalone; null and
# non-Timestamp types produce a type mismatch error.
RENAME_RC_AFTER_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_after_cluster_time_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="afterClusterTime should be rejected on standalone",
        marks=(pytest.mark.requires(cluster_read_concern=False),),
    ),
    CommandTestCase(
        "rc_after_cluster_time_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"afterClusterTime": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="afterClusterTime=null should produce TypeMismatch",
    ),
    CommandTestCase(
        "rc_after_cluster_time_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"afterClusterTime": 123},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="afterClusterTime as int should produce TypeMismatch",
    ),
]

# Property [readConcern atClusterTime]: atClusterTime produces an
# invalid-options error (requires snapshot level); null and non-Timestamp
# types produce a type mismatch error.
RENAME_RC_AT_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_at_cluster_time_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"atClusterTime": Timestamp(1, 1)},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="atClusterTime without snapshot level should be rejected",
    ),
    CommandTestCase(
        "rc_at_cluster_time_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"atClusterTime": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="atClusterTime=null should produce TypeMismatch",
    ),
    CommandTestCase(
        "rc_at_cluster_time_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "readConcern": {"atClusterTime": 123},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="atClusterTime as int should produce TypeMismatch",
    ),
]

RENAME_RC_TESTS: list[CommandTestCase] = (
    RENAME_RC_SUCCESS_TESTS
    + RENAME_RC_TYPE_ERROR_TESTS
    + RENAME_RC_NULL_SUCCESS_TESTS
    + RENAME_RC_LEVEL_UNSUPPORTED_TESTS
    + RENAME_RC_LEVEL_ENUM_ERROR_TESTS
    + RENAME_RC_LEVEL_TYPE_ERROR_TESTS
    + RENAME_RC_UNKNOWN_FIELD_ERROR_TESTS
    + RENAME_RC_PROVENANCE_ERROR_TESTS
    + RENAME_RC_AFTER_CLUSTER_TIME_TESTS
    + RENAME_RC_AT_CLUSTER_TIME_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_RC_TESTS))
def test_renameCollection_read_concern(database_client, collection, register_db_cleanup, test):
    """Test renameCollection readConcern option."""
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
