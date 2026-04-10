"""
Smoke test for $regex query operator.

Tests basic $regex functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_regex(collection):
    """Test basic $regex query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "name": "apple"}, {"_id": 2, "name": "banana"}, {"_id": 3, "name": "apricot"}]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"name": {"$regex": "^ap"}}}
    )

    expected = [{"_id": 1, "name": "apple"}, {"_id": 3, "name": "apricot"}]
    assertSuccess(result, expected, msg="Should support $regex query operator")
