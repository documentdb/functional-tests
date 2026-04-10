"""
Smoke test for $sample stage.

Tests basic $sample functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_sample(collection):
    """Test basic $sample behavior."""
    collection.insert_many([{"_id": 1, "value": 10}])

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$sample": {"size": 1}}], "cursor": {}},
    )

    expected = [{"_id": 1, "value": 10}]
    assertSuccess(result, expected, msg="Should support $sample stage")
