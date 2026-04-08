"""
Smoke test for $unionWith stage.

Tests basic $unionWith functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_unionWith(collection):
    """Test basic $unionWith behavior."""
    other_collection_name = f"{collection.name}_other"

    collection.insert_many([{"_id": 1, "value": 10}])

    collection.database[other_collection_name].drop()
    collection.database[other_collection_name].insert_many([{"_id": 2, "value": 20}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unionWith": other_collection_name}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "value": 10}, {"_id": 2, "value": 20}]
    assertSuccess(result, expected, msg="Should support $unionWith stage")
