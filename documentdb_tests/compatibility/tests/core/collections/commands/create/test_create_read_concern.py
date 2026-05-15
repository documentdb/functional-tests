"""Tests for the create command readConcern option."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [ReadConcern Document Acceptance]: the readConcern option accepts
# a document or null; empty document and level "local" succeed; provenance
# accepts valid enum strings; level null is treated as omitted.
CREATE_RC_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="rc_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": None,
        },
        expected={"ok": 1.0},
        msg="null readConcern should be treated as omitted",
    ),
    CommandTestCase(
        id="rc_empty_document",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {},
        },
        expected={"ok": 1.0},
        msg="Empty readConcern document should succeed",
    ),
    CommandTestCase(
        id="rc_level_local",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0},
        msg="readConcern level 'local' should succeed",
    ),
    CommandTestCase(
        id="rc_level_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": None},
        },
        expected={"ok": 1.0},
        msg="readConcern level null should be treated as omitted",
    ),
    CommandTestCase(
        id="rc_provenance_client_supplied",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local", "provenance": "clientSupplied"},
        },
        expected={"ok": 1.0},
        msg="provenance 'clientSupplied' should succeed",
    ),
    CommandTestCase(
        id="rc_provenance_custom_default",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local", "provenance": "customDefault"},
        },
        expected={"ok": 1.0},
        msg="provenance 'customDefault' should succeed",
    ),
    CommandTestCase(
        id="rc_provenance_implicit_default",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local", "provenance": "implicitDefault"},
        },
        expected={"ok": 1.0},
        msg="provenance 'implicitDefault' should succeed",
    ),
    CommandTestCase(
        id="rc_provenance_get_last_error_defaults",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local", "provenance": "getLastErrorDefaults"},
        },
        expected={"ok": 1.0},
        msg="provenance 'getLastErrorDefaults' should succeed",
    ),
    CommandTestCase(
        id="rc_provenance_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local", "provenance": None},
        },
        expected={"ok": 1.0},
        msg="provenance null should succeed",
    ),
]

# Property [ReadConcern Type Validation]: non-document types for
# readConcern produce TYPE_MISMATCH_ERROR.
CREATE_RC_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"rc_type_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "readConcern": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} readConcern should fail with type mismatch",
    )
    for label, val in [
        ("string", "local"),
        ("int", 1),
        ("bool", True),
        ("array", ["local"]),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"x")),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [ReadConcern Level Unsupported]: levels other than "local" are
# not supported for the create command and produce INVALID_OPTIONS_ERROR.
CREATE_RC_LEVEL_UNSUPPORTED_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"rc_level_{level}",
        command=lambda ctx, lvl=level: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": lvl},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"readConcern level '{level}' should fail as unsupported",
    )
    for level in ["majority", "available", "linearizable", "snapshot"]
]

# Property [ReadConcern Level Enum Validation]: invalid level strings
# produce BAD_VALUE_ERROR; valid values are case-sensitive.
CREATE_RC_LEVEL_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="rc_level_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "bogus"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid readConcern level string should fail",
    ),
    CommandTestCase(
        id="rc_level_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Empty string readConcern level should fail",
    ),
    CommandTestCase(
        id="rc_level_uppercase_local",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "Local"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Uppercase 'Local' is not a valid level (case-sensitive)",
    ),
]

# Property [ReadConcern Level Type Validation]: non-string types for
# readConcern.level produce TYPE_MISMATCH_ERROR.
CREATE_RC_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"rc_level_type_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": val},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} readConcern level should fail with type mismatch",
    )
    for label, val in [
        ("int", 42),
        ("bool", True),
        ("array", ["local"]),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"x")),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [ReadConcern Unknown Fields]: unknown sub-fields in
# readConcern produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CREATE_RC_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="rc_unknown_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown sub-field in readConcern should fail",
    ),
]

# Property [ReadConcern Provenance Validation]: invalid provenance string
# produces BAD_VALUE_ERROR; non-string provenance produces
# TYPE_MISMATCH_ERROR.
CREATE_RC_PROVENANCE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="rc_provenance_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "readConcern": {"level": "local", "provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid provenance string should fail",
    ),
    *[
        CommandTestCase(
            id=f"rc_provenance_non_string_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "readConcern": {"level": "local", "provenance": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string provenance ({tid}) should fail with type mismatch",
        )
        for tid, val in [
            ("int", 123),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [ReadConcern Error Rejection]: invalid readConcern inputs
# (wrong types, unsupported levels, bad enums, unknown fields, invalid
# provenance) are rejected with the appropriate error code.
CREATE_READ_CONCERN_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_RC_TYPE_ERROR_TESTS
    + CREATE_RC_LEVEL_UNSUPPORTED_ERROR_TESTS
    + CREATE_RC_LEVEL_ENUM_ERROR_TESTS
    + CREATE_RC_LEVEL_TYPE_ERROR_TESTS
    + CREATE_RC_UNKNOWN_FIELD_ERROR_TESTS
    + CREATE_RC_PROVENANCE_ERROR_TESTS
)

# Property [ReadConcern Valid Acceptance]: valid readConcern documents
# (null, empty, level "local", valid provenance strings) are accepted
# without error.
CREATE_READ_CONCERN_SUCCESS_TESTS: list[CommandTestCase] = CREATE_RC_SUCCESS_TESTS

CREATE_READ_CONCERN_TESTS: list[CommandTestCase] = (
    CREATE_READ_CONCERN_SUCCESS_TESTS + CREATE_READ_CONCERN_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_READ_CONCERN_TESTS))
def test_create_read_concern(database_client, collection, test):
    """Test create command read concern behavior."""
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
