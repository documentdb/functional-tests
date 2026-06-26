"""Tests for setParameter hierarchical/object parameter handling.

Validates logComponentVerbosity nested parameter behavior including
read defaults, type/member validation, multi-member set, atomic rejection,
and bare numeric form.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Type Rejection]: logComponentVerbosity rejects invalid types and values.
HIERARCHICAL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string_value",
        command=lambda ctx: {"setParameter": 1, "logComponentVerbosity": "abc"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="setParameter should reject string for logComponentVerbosity",
    ),
    CommandTestCase(
        "nested_string_verbosity",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": "abc"}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject string for nested verbosity",
    ),
    CommandTestCase(
        "nested_overflow",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": 2_147_483_648}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject overflow for nested verbosity",
    ),
    CommandTestCase(
        "nested_underflow",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": -2_147_483_649}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject underflow for nested verbosity",
    ),
    CommandTestCase(
        "unknown_component",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"unknownComponent": {"verbosity": 1}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject unknown component name",
    ),
    CommandTestCase(
        "nested_nan_verbosity",
        command=lambda ctx: {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": float("nan")}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setParameter should reject NaN for nested verbosity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(HIERARCHICAL_ERROR_TESTS))
def test_setParameter_hierarchical_errors(database_client, collection, test):
    """Test setParameter hierarchical parameter error cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


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


# Standalone tests below require save/restore of server state after each set.


# Property [Top-Level Verbosity]: top-level verbosity matches scalar logLevel.
def test_setParameter_hierarchical_top_level_verbosity(collection):
    """Test setParameter top-level verbosity matches scalar logLevel default."""
    execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result2 = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        result2,
        {"logComponentVerbosity": {"verbosity": 0}},
        msg="setParameter top-level verbosity should match logLevel",
    )


# Property [Multi-Member Set]: setting several nested members in one command succeeds.
def test_setParameter_hierarchical_multi_member_set(collection):
    """Test setParameter setting several nested members in one command succeeds."""
    execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": -1}, "network": {"verbosity": -1}},
        },
    )
    result = execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": 2}, "network": {"verbosity": 3}},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="setParameter multi-member set should succeed")
    execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": -1}, "network": {"verbosity": -1}},
        },
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
    execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": -1}, "network": {"verbosity": -1}},
        },
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


# Property [Bare Numeric Form]: setting component with bare numeric level succeeds.
def test_setParameter_hierarchical_bare_numeric_form(collection):
    """Test setParameter setting nested component with bare numeric level succeeds."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "logComponentVerbosity": {"command": 4}}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="setParameter should accept bare numeric form")
    execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": -1}}},
    )


def test_setParameter_hierarchical_bare_numeric_readback(collection):
    """Test setParameter bare numeric component set takes effect when read back."""
    execute_admin_command(collection, {"setParameter": 1, "logComponentVerbosity": {"command": 4}})
    read_result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        read_result,
        {"logComponentVerbosity": {"command": {"verbosity": 4}}},
        msg="setParameter bare numeric should set verbosity",
    )
    execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": -1}}},
    )
