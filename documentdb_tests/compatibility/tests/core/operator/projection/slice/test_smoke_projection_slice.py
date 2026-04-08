"""
Smoke test for $slice projection operator.

Tests basic $slice projection functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_projection_slice(collection):
    """Test basic $slice projection behavior."""
    collection.insert_many(
        [{"_id": 1, "scores": [80, 85, 90, 95, 100]}, {"_id": 2, "scores": [70, 75, 80]}]
    )

    result = execute_command(
        collection, {"find": collection.name, "projection": {"scores": {"$slice": 2}}}
    )

    expected = [{"_id": 1, "scores": [80, 85]}, {"_id": 2, "scores": [70, 75]}]
    assertSuccess(result, expected, msg="Should support $slice projection")
