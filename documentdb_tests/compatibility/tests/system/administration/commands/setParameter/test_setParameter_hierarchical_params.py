"""Tests for setParameter hierarchical/object parameter handling (success cases).

Validates logComponentVerbosity nested parameter behavior including
read defaults, multi-member set, atomic rejection, and bare numeric form.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Single-Command Hierarchical]: simple set/read operations.
HIERARCHICAL_SINGLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "multi_member_set",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": 2}, "network": {"verbosity": 3}},
        },
        expected={"ok": 1.0},
        msg="setParameter multi-member set should succeed",
    ),
    CommandTestCase(
        "bare_numeric_form",
        command=lambda ctx: {"setParameter": 1, "logComponentVerbosity": {"command": 4}},
        expected={"ok": 1.0},
        msg="setParameter should accept bare numeric form",
    ),
]


@pytest.mark.parametrize("test", pytest_params(HIERARCHICAL_SINGLE_TESTS))
def test_setParameter_hierarchical_single(database_client, collection, test):
    """Test setParameter hierarchical single-command cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


# Property [Readability]: logComponentVerbosity is readable with defined defaults.
def test_setParameter_hierarchical_param_readable(collection):
    """Test setParameter reading logComponentVerbosity returns a defined value."""
    result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setParameter should be able to read hierarchical param"
    )


def test_setParameter_hierarchical_nested_field_defined(collection):
    """Test setParameter deeply nested verbosity field is defined."""
    result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        result,
        {"logComponentVerbosity": {"network": {"asio": {"verbosity": -1}}}},
        msg="setParameter nested component should have defined verbosity",
    )


# Property [Top-Level Verbosity]: top-level verbosity matches scalar logLevel.
def test_setParameter_hierarchical_top_level_verbosity(collection):
    """Test setParameter top-level verbosity matches scalar logLevel default."""
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        result,
        {"logComponentVerbosity": {"verbosity": 0}},
        msg="setParameter top-level verbosity should match logLevel",
    )


# Property [Multi-Member Readback]: reading back reflects each member set.
def test_setParameter_hierarchical_multi_member_readback(collection):
    """Test setParameter reading back reflects each member set in a multi-member command."""
    execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": 2}, "network": {"verbosity": 3}},
        },
    )
    read_result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        read_result,
        {"logComponentVerbosity": {"command": {"verbosity": 2}, "network": {"verbosity": 3}}},
        msg="setParameter should reflect both members after set",
    )


# Property [Atomic Rejection]: no members change when a multi-member set is rejected.
def test_setParameter_hierarchical_atomic_rejection(collection):
    """Test setParameter no members are changed when a multi-member set is rejected."""
    execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": -1}}},
    )
    execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": 2}, "unknownXYZ": {"verbosity": 1}},
        },
    )
    result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        result,
        {"logComponentVerbosity": {"command": {"verbosity": -1}}},
        msg="setParameter should not change any member on atomic rejection",
    )


# Property [Clear With Negative]: setting -1 resets to inherited default.
def test_setParameter_hierarchical_clear_with_negative(collection):
    """Test setParameter clearing nested members with -1 resets to inherited default."""
    execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": 3}}},
    )
    execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": -1}}},
    )
    result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        result,
        {"logComponentVerbosity": {"command": {"verbosity": -1}}},
        msg="setParameter should reset member to -1 (inherited) after clear",
    )


# Property [Bare Numeric Readback]: bare numeric form takes effect when read back.
def test_setParameter_hierarchical_bare_numeric_readback(collection):
    """Test setParameter bare numeric component set takes effect when read back."""
    execute_admin_command(collection, {"setParameter": 1, "logComponentVerbosity": {"command": 4}})
    read_result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        read_result,
        {"logComponentVerbosity": {"command": {"verbosity": 4}}},
        msg="setParameter bare numeric should set verbosity",
    )
