"""Tests for startSession readConcern handling."""

from __future__ import annotations

import pytest

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
from documentdb_tests.framework.property_checks import Eq

# Property [readConcern Type Rejection]: non-document readConcern values produce a type error.
STARTSESSION_RC_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"rc_type_reject_{tid}",
        command=lambda ctx, v=val: {"startSession": 1, "readConcern": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"startSession should reject {tid} readConcern with type mismatch error",
    )
    for tid, val in [
        ("string", "local"),
        ("int32", 1),
        ("bool", True),
        ("array", []),
    ]
]

# Property [readConcern Document Acceptance]: valid document readConcern values are accepted.
STARTSESSION_RC_DOC_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_doc_accept_empty",
        command=lambda ctx: {"startSession": 1, "readConcern": {}},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept empty document readConcern",
    ),
    CommandTestCase(
        "rc_doc_accept_null",
        command=lambda ctx: {"startSession": 1, "readConcern": None},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept null readConcern as omitted",
    ),
    CommandTestCase(
        "rc_doc_accept_level_local",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": "local"}},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept readConcern level local",
    ),
    CommandTestCase(
        "rc_doc_accept_level_null",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": None}},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept readConcern with null level",
    ),
]

# Property [readConcern Level Rejection]: unsupported readConcern levels are rejected.
STARTSESSION_RC_LEVEL_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"rc_level_reject_{level}",
        command=lambda ctx, v=level: {"startSession": 1, "readConcern": {"level": v}},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"startSession should reject readConcern level {level}",
    )
    for level in ["available", "majority", "linearizable", "snapshot"]
]

# Property [readConcern Invalid Level]: invalid readConcern level strings are rejected.
STARTSESSION_RC_INVALID_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_invalid_level_string",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="startSession should reject invalid readConcern level string",
    ),
    CommandTestCase(
        "rc_invalid_level_empty_string",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="startSession should reject empty string readConcern level",
    ),
]

# Property [readConcern Sub-field Validation]: readConcern sub-field structure is validated.
STARTSESSION_RC_SUBFIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_subfield_unknown",
        command=lambda ctx: {
            "startSession": 1,
            "readConcern": {"level": "local", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="startSession should reject readConcern with unknown sub-field",
    ),
    CommandTestCase(
        "rc_subfield_other_name",
        command=lambda ctx: {"startSession": 1, "readConcern": {"other": "val"}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="startSession should reject readConcern with non-level sub-field",
    ),
    CommandTestCase(
        "rc_subfield_level_type_int",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="startSession should reject readConcern with int level",
    ),
    CommandTestCase(
        "rc_subfield_level_type_bool",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": True}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="startSession should reject readConcern with bool level",
    ),
]

STARTSESSION_RC_SUCCESS_TESTS = STARTSESSION_RC_DOC_ACCEPTANCE_TESTS

STARTSESSION_RC_ERROR_TESTS = (
    STARTSESSION_RC_TYPE_REJECTION_TESTS
    + STARTSESSION_RC_LEVEL_REJECTION_TESTS
    + STARTSESSION_RC_INVALID_LEVEL_TESTS
    + STARTSESSION_RC_SUBFIELD_TESTS
)

STARTSESSION_RC_TESTS = STARTSESSION_RC_SUCCESS_TESTS + STARTSESSION_RC_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_RC_TESTS))
def test_startSession_readconcern(database_client, collection, test):
    """Test startSession readConcern handling."""
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
