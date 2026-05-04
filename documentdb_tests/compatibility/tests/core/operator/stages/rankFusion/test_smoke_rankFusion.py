"""
Smoke test for $rankFusion stage.

Tests basic $rankFusion stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_rankFusion(collection):
    """Test basic $rankFusion stage behavior."""
    collection.insert_many([{"_id": 1, "name": "test", "score": 10.0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$rankFusion": {
                        "input": {
                            "pipelines": {
                                "pipeline1": [{"$match": {"_id": 1}}, {"$sort": {"score": -1}}]
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "name": "test", "score": 10.0}]
    assertSuccess(result, expected, msg="Should support $rankFusion stage")
