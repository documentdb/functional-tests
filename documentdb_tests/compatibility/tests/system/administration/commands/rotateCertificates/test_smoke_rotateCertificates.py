"""
Smoke test for rotateCertificates command.

Tests basic rotateCertificates functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_rotateCertificates(collection):
    """Test basic rotateCertificates behavior."""
    result = execute_admin_command(collection, {"rotateCertificates": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support rotateCertificates command")
