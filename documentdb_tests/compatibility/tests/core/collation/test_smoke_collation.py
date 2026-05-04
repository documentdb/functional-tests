"""
Smoke test for collation.

Tests basic collation functionality with locale-specific string comparison.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_collation(collection):
    """Test basic collation behavior with case-insensitive comparison."""
    execute_command(
        collection,
        {"create": f"{collection.name}_collated", "collation": {"locale": "en", "strength": 2.0}},
    )

    collated_collection = collection.database[f"{collection.name}_collated"]
    collated_collection.insert_many(
        [{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Apple"}, {"_id": 3, "name": "banana"}]
    )

    result = execute_command(
        collection, {"find": f"{collection.name}_collated", "filter": {"name": "apple"}}
    )

    expected = [{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Apple"}]
    assertSuccess(result, expected, msg="Should support collation with case-insensitive comparison")
