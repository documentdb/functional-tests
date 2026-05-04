"""
Smoke test for $listSampledQueries stage.

Tests basic $listSampledQueries stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_listSampledQueries(collection):
    """Test basic $listSampledQueries stage behavior."""
    result = execute_admin_command(
        collection, {"aggregate": 1, "pipeline": [{"$listSampledQueries": {}}], "cursor": {}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $listSampledQueries stage")
