"""
Smoke test for hello command.

Tests basic hello command functionality by verifying the command returns
a successful response with ok: 1.0.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.smoke]


def test_smoke_hello(collection):
    """Test basic hello command behavior."""
    result = execute_command(collection, {"hello": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="hello should return ok: 1.0")
