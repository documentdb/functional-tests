"""Tests for setParameter hierarchical/object parameter handling.

Validates logComponentVerbosity nested parameter behavior including
read defaults, type/member validation, multi-member set, atomic rejection,
and bare numeric form.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_setParameter_hierarchical_param_readable(collection):
    """Test reading logComponentVerbosity returns a defined value."""
    result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should be able to read hierarchical param")


def test_setParameter_hierarchical_top_level_verbosity(collection):
    """Test top-level verbosity of hierarchical parameter matches scalar logLevel default."""
    execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
    result2 = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        result2,
        {"logComponentVerbosity": {"verbosity": 0}},
        msg="Top-level verbosity should match logLevel",
    )


def test_setParameter_hierarchical_nested_field_defined(collection):
    """Test a deeply nested verbosity field is defined."""
    result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    # network.asio is a deeply nested component
    assertSuccessPartial(
        result,
        {"logComponentVerbosity": {"network": {"asio": {"verbosity": -1}}}},
        msg="Nested component should have defined verbosity",
    )


def test_setParameter_hierarchical_string_value_fails(collection):
    """Test setting logComponentVerbosity to a plain string fails with TypeMismatch."""
    result = execute_admin_command(collection, {"setParameter": 1, "logComponentVerbosity": "abc"})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="String should fail for object param")


def test_setParameter_hierarchical_nested_string_verbosity_fails(collection):
    """Test setting a nested verbosity member to a non-numeric string fails."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": "abc"}}},
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="String verbosity should fail")


def test_setParameter_hierarchical_nested_overflow_fails(collection):
    """Test setting a nested verbosity member above max safe integer fails."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": 2147483648}}},
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Overflow verbosity should fail")


def test_setParameter_hierarchical_nested_underflow_fails(collection):
    """Test setting a nested verbosity member below min safe integer fails."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": -2147483649}}},
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Underflow verbosity should fail")


def test_setParameter_hierarchical_unknown_component_fails(collection):
    """Test setting an unrecognized nested component name fails."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"unknownComponent": {"verbosity": 1}}},
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Unknown component should fail")


def test_setParameter_hierarchical_multi_member_set(collection):
    """Test setting several nested members in one command succeeds."""
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
    assertSuccessPartial(result, {"ok": 1.0}, msg="Multi-member set should succeed")
    # Cleanup
    execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": -1}, "network": {"verbosity": -1}},
        },
    )


def test_setParameter_hierarchical_multi_member_readback(collection):
    """Test reading back reflects each member set in a multi-member command."""
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
        msg="Both members should be set",
    )
    # Cleanup
    execute_admin_command(
        collection,
        {
            "setParameter": 1,
            "logComponentVerbosity": {"command": {"verbosity": -1}, "network": {"verbosity": -1}},
        },
    )


def test_setParameter_hierarchical_atomic_rejection(collection):
    """Test no members are changed when a multi-member set is rejected."""
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
        msg="Command verbosity should remain unchanged after atomic rejection",
    )


def test_setParameter_hierarchical_clear_with_negative(collection):
    """Test clearing nested members with -1 resets them to inherited default."""
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
        msg="Cleared member should fall back to -1 (inherited)",
    )


def test_setParameter_hierarchical_bare_numeric_form(collection):
    """Test setting a nested component verbosity using bare numeric level succeeds."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "logComponentVerbosity": {"command": 4}}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Bare numeric form should succeed")
    execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": -1}}},
    )


def test_setParameter_hierarchical_bare_numeric_readback(collection):
    """Test bare numeric component set takes effect when read back."""
    execute_admin_command(collection, {"setParameter": 1, "logComponentVerbosity": {"command": 4}})
    read_result = execute_admin_command(collection, {"getParameter": 1, "logComponentVerbosity": 1})
    assertSuccessPartial(
        read_result,
        {"logComponentVerbosity": {"command": {"verbosity": 4}}},
        msg="Bare numeric should set verbosity",
    )
    execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": -1}}},
    )


def test_setParameter_hierarchical_nested_nan_verbosity_fails(collection):
    """Test setting a nested verbosity member to NaN fails with BadValue."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "logComponentVerbosity": {"command": {"verbosity": float("nan")}}},
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="NaN verbosity should fail")
