"""Tests for getCmdLineOpts command output stability.

Validates that getCmdLineOpts returns consistent results across repeated calls.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.admin


def test_getCmdLineOpts_parsed_stable(collection):
    """Test the 'parsed' content is identical across consecutive calls."""
    result1 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    result2 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    failure = next((r for r in (result1, result2) if isinstance(r, Exception)), None)
    assertSuccess(
        failure if failure is not None else result2["parsed"],
        expected=None if failure is not None else result1["parsed"],
        msg="'parsed' content should be identical across calls",
        raw_res=True,
    )


def test_getCmdLineOpts_argv_stable(collection):
    """Test the 'argv' content is identical across consecutive calls."""
    result1 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    result2 = execute_admin_command(collection, {"getCmdLineOpts": 1})
    failure = next((r for r in (result1, result2) if isinstance(r, Exception)), None)
    assertSuccess(
        failure if failure is not None else result2["argv"],
        expected=None if failure is not None else result1["argv"],
        msg="'argv' content should be identical across calls",
        raw_res=True,
    )
