"""
Smoke test for autoCompact command.

Tests basic autoCompact functionality.
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.commands.autoCompact.utils.autoCompact_common import (  # noqa: E501
    ensure_autocompact_idle,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.error_codes import OBJECT_IS_BUSY_ERROR
from documentdb_tests.framework.executor import execute_admin_with_retry_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_autoCompact(collection):
    """Test basic autoCompact behavior."""
    # Ensure autoCompact is idle first: a leftover non-default config would make
    # this plain enable conflict instead of returning ok.
    ensure_autocompact_idle(collection)
    # Tolerate the transient busy state while a prior compaction winds down.
    result = execute_admin_with_retry_command(
        collection, {"autoCompact": True}, retry_code=OBJECT_IS_BUSY_ERROR
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support autoCompact command")
