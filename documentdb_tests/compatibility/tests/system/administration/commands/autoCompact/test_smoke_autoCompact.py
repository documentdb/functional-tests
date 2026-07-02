"""
Smoke test for autoCompact command.

Tests basic autoCompact functionality.
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.commands.autoCompact.utils.autoCompact_common import (  # noqa: E501
    ensure_autocompact_idle,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_autoCompact(collection):
    """Test basic autoCompact behavior."""
    # Ensure autoCompact is idle first: a leftover non-default config would make
    # this plain enable conflict instead of returning ok.
    ensure_autocompact_idle(collection)
    result = execute_admin_command(collection, {"autoCompact": True})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support autoCompact command")
