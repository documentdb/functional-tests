"""
Smoke test for dropDatabase change stream event.

Tests basic dropDatabase change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_dropDatabase(collection):
    """Test basic dropDatabase change stream event behavior."""
    execute_command(collection, {"create": f"{collection.name}_temp"})

    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [{"$changeStream": {}}, {"$match": {"operationType": "dropDatabase"}}],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_command(collection, {"dropDatabase": 1})

    result = execute_command(collection, {"getMore": cursor_id, "collection": "$cmd.aggregate"})
    result = result["cursor"]["nextBatch"][0]

    expected = {"operationType": "dropDatabase", "ns": {"db": collection.database.name}}
    assertSuccessPartial(result, expected, msg="Should support dropDatabase change stream event")
