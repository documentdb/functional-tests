"""
Smoke test for writeConcern.

Tests basic writeConcern functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_write_concern(collection):
    """Test basic writeConcern behavior."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 1, "name": "test"}],
            "writeConcern": {"w": 1},
        },
    )

    expected = {"ok": 1.0, "n": 1}
    assertSuccessPartial(result, expected, msg="Should support writeConcern")
