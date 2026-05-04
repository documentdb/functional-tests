"""
Smoke test for timeseries.

Tests basic timeseries collection functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_timeseries(collection):
    """Test basic timeseries collection creation."""
    result = execute_command(
        collection,
        {
            "create": f"{collection.name}_timeseries",
            "timeseries": {
                "timeField": "timestamp",
                "metaField": "metadata",
                "granularity": "seconds",
            },
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support creating timeseries collections")
