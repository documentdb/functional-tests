"""Smoke test for the $score stage (new in 8.2): the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_score(collection):
    """Test the engine accepts the $score stage."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$score": {"score": "$x"}}],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $score stage")
