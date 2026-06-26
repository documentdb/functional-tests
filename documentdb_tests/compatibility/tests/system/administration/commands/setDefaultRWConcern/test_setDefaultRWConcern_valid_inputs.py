"""Accepted-input tests for setDefaultRWConcern."""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.admin_test_case import (
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


VALID_INPUT_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "both_defaults_plus_command_write_concern",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "defaultWriteConcern": {"w": 1},
            "writeConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="both defaults plus a command-level writeConcern succeeds",
    ),
    AdminTestCase(
        "empty_read_concern_satisfies_requirement",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {}},
        expected={"ok": Eq(1.0)},
        msg="empty document {} for defaultReadConcern satisfies the at-least-one requirement",
    ),
    AdminTestCase(
        "accepts_command_write_concern",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "writeConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="command accepts its own writeConcern field for acknowledgement",
    ),
    AdminTestCase(
        "command_write_concern_w0",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "writeConcern": {"w": 0},
        },
        expected={"ok": Eq(1.0)},
        msg="command-level writeConcern w:0 should work independently of defaultWriteConcern",
    ),
    AdminTestCase(
        "read_level_local",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "local"}},
        expected={"ok": Eq(1.0)},
        msg="level 'local' is accepted",
    ),
    AdminTestCase(
        "read_level_available",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "available"}},
        expected={"ok": Eq(1.0)},
        msg="level 'available' is accepted",
    ),
    AdminTestCase(
        "read_level_majority",
        command={"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "majority"}},
        expected={"ok": Eq(1.0)},
        msg="level 'majority' is accepted",
    ),
    AdminTestCase(
        "write_concern_w_majority",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": "majority"}},
        expected={"ok": Eq(1.0)},
        msg="w:'majority' is accepted",
    ),
    AdminTestCase(
        "write_concern_journal_flag",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1, "j": True}},
        expected={"ok": Eq(1.0)},
        msg="journal/j boolean flag is accepted",
    ),
    AdminTestCase(
        "write_concern_fractional_w",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1.5}},
        expected={"ok": Eq(1.0)},
        msg="fractional double w is accepted",
    ),
    AdminTestCase(
        "write_concern_wtimeout_string",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1, "wtimeout": "100"}},
        expected={"ok": Eq(1.0)},
        msg="wtimeout as string is accepted (coerced)",
    ),
    AdminTestCase(
        "write_concern_negative_wtimeout",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1, "wtimeout": -1}},
        expected={"ok": Eq(1.0)},
        msg="negative wtimeout is accepted (coerced)",
    ),
    AdminTestCase(
        "write_concern_wtimeout_stored",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1, "wtimeout": 5000}},
        expected={"ok": Eq(1.0), "defaultWriteConcern": {"w": Eq(1), "wtimeout": Eq(5000)}},
        msg="wtimeout should be stored",
    ),
    AdminTestCase(
        "write_concern_wtimeout_defaults_to_zero",
        command={"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}},
        expected={"ok": Eq(1.0), "defaultWriteConcern": {"w": Eq(1), "wtimeout": Eq(0)}},
        msg="wtimeout should default to 0",
    ),
    AdminTestCase(
        "read_concern_null_as_omitted",
        command={
            "setDefaultRWConcern": 1,
            "defaultReadConcern": None,
            "defaultWriteConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="defaultReadConcern null is treated as omitted",
    ),
    AdminTestCase(
        "write_concern_null_as_omitted",
        command={
            "setDefaultRWConcern": 1,
            "defaultWriteConcern": None,
            "defaultReadConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="defaultWriteConcern null is treated as omitted",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_INPUT_TESTS))
def test_setDefaultRWConcern_valid_inputs(collection, test):
    """Run a setDefaultRWConcern accepted-input case."""
    for setup in test.setup_commands:
        execute_admin_command(collection, setup)
    result = execute_admin_command(collection, test.command)
    assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)
