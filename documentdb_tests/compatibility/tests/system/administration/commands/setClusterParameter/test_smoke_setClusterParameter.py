"""
Smoke test for setClusterParameter command.

Tests basic setClusterParameter functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.no_parallel]


def test_smoke_setClusterParameter(collection):
    """Test basic setClusterParameter behavior."""
    get_result = execute_admin_command(collection, {"getClusterParameter": "changeStreamOptions"})

    original_seconds = 3600
    if not isinstance(get_result, Exception) and "clusterParameters" in get_result:
        params = get_result.get("clusterParameters", [])
        if params:
            original_seconds = params[0].get("preAndPostImages", {}).get("expireAfterSeconds", 3600)

    new_seconds = 7200 if original_seconds != 7200 else 3600
    result = execute_admin_command(
        collection,
        {
            "setClusterParameter": {
                "changeStreamOptions": {"preAndPostImages": {"expireAfterSeconds": new_seconds}}
            }
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support setClusterParameter command")

    execute_admin_command(
        collection,
        {
            "setClusterParameter": {
                "changeStreamOptions": {
                    "preAndPostImages": {"expireAfterSeconds": original_seconds}
                }
            }
        },
    )
