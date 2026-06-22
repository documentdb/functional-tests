"""Tests for getCmdLineOpts command output stability.

Validates that getCmdLineOpts returns consistent results across repeated calls.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.admin


def test_getCmdLineOpts_idempotent(collection):
    """Test calling getCmdLineOpts multiple times returns identical results."""
    result1 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    result2 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    assertSuccess(result2, expected=result1, msg="Should return identical results", raw_res=True)


def test_getCmdLineOpts_parsed_stable(collection):
    """Test the 'parsed' content is identical across consecutive calls."""
    result1 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    result2 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    assertSuccess(
        result2.get("parsed"),
        expected=result1.get("parsed"),
        msg="'parsed' content should be identical across calls",
        raw_res=True,
    )


def test_getCmdLineOpts_argv_stable(collection):
    """Test the 'argv' content is identical across consecutive calls."""
    result1 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    result2 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    assertSuccess(
        result2.get("argv"),
        expected=result1.get("argv"),
        msg="'argv' content should be identical across calls",
        raw_res=True,
    )
