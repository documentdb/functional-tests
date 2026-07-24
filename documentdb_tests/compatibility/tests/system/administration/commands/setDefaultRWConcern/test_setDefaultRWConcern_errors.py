"""Failure-case tests for setDefaultRWConcern: input rejections, atomic-failure
behavior, and rejection outside the admin database."""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.admin_test_case import (
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    TYPE_MISMATCH_ERROR,
    UNAUTHORIZED_ERROR,
    UNKNOWN_REPL_WRITE_CONCERN_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


ERROR_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "neither_default_specified",
        command={"setDefaultRWConcern": 1},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject when neither default specified",
    ),
    AdminTestCase(
        "unrecognized_field",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject unrecognized fields",
    ),
    AdminTestCase(
        "comment_does_not_mask_error",
        command={"setDefaultRWConcern": 1, "comment": "a comment"},
        error_code=BAD_VALUE_ERROR,
        msg="Comment should not mask at-least-one error",
    ),
    AdminTestCase(
        "both_null_fails",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": None,
            "defaultWriteConcern": None,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Both null should fail like both absent",
    ),
    AdminTestCase(
        "command_write_concern_unknown_tag_rejected",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "writeConcern": {"w": "customTag"},
        },
        error_code=UNKNOWN_REPL_WRITE_CONCERN_ERROR,
        msg="unknown tag in the command-level writeConcern should be rejected",
    ),
    AdminTestCase(
        "read_level_linearizable_rejected",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "linearizable"}},
        error_code=BAD_VALUE_ERROR,
        msg="linearizable not supported as default",
    ),
    AdminTestCase(
        "read_level_snapshot_rejected",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "snapshot"}},
        error_code=BAD_VALUE_ERROR,
        msg="snapshot not supported as default",
    ),
    AdminTestCase(
        "unsupported_read_level_arbitrary",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "foobar"}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject arbitrary string level",
    ),
    AdminTestCase(
        "write_concern_unknown_tag",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": "customTag"}},
        error_code=UNKNOWN_REPL_WRITE_CONCERN_ERROR,
        msg="Unknown tag should be rejected",
    ),
    AdminTestCase(
        "write_concern_w0_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 0}},
        error_code=BAD_VALUE_ERROR,
        msg="w:0 unsupported as default",
    ),
    AdminTestCase(
        "read_level_non_string_type",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": 123}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="level must be string",
    ),
    AdminTestCase(
        "read_concern_extra_key_rejected",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "local", "extra": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Extra key should be rejected",
    ),
    AdminTestCase(
        "non_level_key_in_read_concern",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"readPreference": "primary"}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject non-level key in defaultReadConcern",
    ),
    AdminTestCase(
        "read_level_empty_string_rejected",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty string level should be rejected",
    ),
    AdminTestCase(
        "read_level_wrong_case_rejected",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "LOCAL"}},
        error_code=BAD_VALUE_ERROR,
        msg="Levels are case-sensitive",
    ),
    AdminTestCase(
        "write_concern_negative_w_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Negative w should be rejected",
    ),
    AdminTestCase(
        "write_concern_w_bool_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="boolean w should be rejected",
    ),
    AdminTestCase(
        "write_concern_w_null_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": None}},
        error_code=UNKNOWN_REPL_WRITE_CONCERN_ERROR,
        msg="null w is coerced to an empty mode name and rejected",
    ),
    AdminTestCase(
        "write_concern_wtimeout_only_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"wtimeout": 100}},
        error_code=BAD_VALUE_ERROR,
        msg="wtimeout-only should be rejected",
    ),
    AdminTestCase(
        "write_concern_journal_non_bool_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1, "j": "true"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="j must be boolean",
    ),
    AdminTestCase(
        "read_concern_nested_level_rejected",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": {"nested": "local"}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Nested level object should be rejected",
    ),
    AdminTestCase(
        "write_concern_oversized_w_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 9999}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Oversized w should be rejected",
    ),
    AdminTestCase(
        "write_concern_extra_field_rejected",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1, "unknownField": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Extra WC field should be rejected",
    ),
    AdminTestCase(
        "atomic_failure_invalid_read_with_valid_write",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "snapshot"},
            "defaultWriteConcern": {"w": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should fail atomically when read concern is invalid",
    ),
    AdminTestCase(
        "atomic_failure_invalid_write",
        setup_commands=({"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "local"}},),
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "majority"},
            "defaultWriteConcern": {"w": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should fail atomically when write concern is invalid",
    ),
    AdminTestCase(
        "write_concern_cannot_unset_once_set",
        setup_commands=({"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},),
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {}},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Cannot unset write concern once set",
    ),
    AdminTestCase(
        "set_read_and_unset_write_rejected",
        setup_commands=({"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},),
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "defaultWriteConcern": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Cannot unset write concern even with valid read",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_setDefaultRWConcern_errors(collection, test):
    """Run a setDefaultRWConcern error case."""
    for setup in test.setup_commands:
        execute_admin_command(collection, setup)
    result = execute_admin_command(collection, test.command)
    assertResult(result, error_code=test.error_code, msg=test.msg)


STATE_INTACT_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "rejected_read_keeps_write_concern",
        setup_commands=(
            {
                "setDefaultRWConcern": 1,
                "defaultReadConcern": {"level": "local"},
                "defaultWriteConcern": {"w": "majority"},
            },
        ),
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "snapshot"},
            "defaultWriteConcern": {"w": 1},
        },
        msg="Invalid read concern must not persist the valid write concern",
    ),
    AdminTestCase(
        "rejected_write_keeps_read_concern",
        setup_commands=(
            {
                "setDefaultRWConcern": 1,
                "defaultReadConcern": {"level": "local"},
                "defaultWriteConcern": {"w": "majority"},
            },
        ),
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "majority"},
            "defaultWriteConcern": {"w": 0},
        },
        msg="Invalid write concern must not persist the valid read concern",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STATE_INTACT_TESTS))
def test_setDefaultRWConcern_failed_set_leaves_defaults_unchanged(collection, test):
    """A rejected setDefaultRWConcern must not persist the valid half sent with it."""
    for setup in test.setup_commands:
        execute_admin_command(collection, setup)
    before = execute_admin_command(collection, {"getDefaultRWConcern": 1})

    execute_admin_command(collection, test.command)

    after = execute_admin_command(collection, {"getDefaultRWConcern": 1})
    assertResult(
        after,
        expected={
            "defaultReadConcern": Eq(before["defaultReadConcern"]),
            "defaultWriteConcern": Eq(before["defaultWriteConcern"]),
            "updateOpTime": Eq(before["updateOpTime"]),
        },
        raw_res=True,
        msg=test.msg,
    )


def test_setDefaultRWConcern_non_admin_database_rejected(collection):
    """Test setDefaultRWConcern is rejected when run against a non-admin database."""
    result = execute_command(
        collection, {"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "local"}}
    )
    assertResult(result, error_code=UNAUTHORIZED_ERROR, msg="Should fail on non-admin database")
