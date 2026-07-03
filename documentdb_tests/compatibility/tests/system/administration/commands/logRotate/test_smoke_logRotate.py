"""Smoke test for logRotate command."""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.error_codes import FILE_RENAME_FAILED_ERROR
from documentdb_tests.framework.executor import execute_admin_with_retry_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_logRotate(collection):
    """Test basic logRotate behavior."""
    result = execute_admin_with_retry_command(
        collection, {"logRotate": 1}, retry_code=FILE_RENAME_FAILED_ERROR
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should support logRotate command")
