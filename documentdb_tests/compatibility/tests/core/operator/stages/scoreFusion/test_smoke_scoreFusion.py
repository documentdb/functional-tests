"""Smoke test for the $scoreFusion stage (GA in 8.3): the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_scoreFusion(collection):
    """Test the engine accepts the $scoreFusion stage."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$scoreFusion": {
                        "input": {
                            "pipelines": {"p1": [{"$score": {"score": "$x"}}]},
                            "normalization": "none",
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $scoreFusion stage")
