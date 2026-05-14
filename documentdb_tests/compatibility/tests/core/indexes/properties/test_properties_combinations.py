"""Tests for index property combinations.

Validates that indexes work correctly with combined properties:
TTL with sparse/partial/unique/collation, and collation with
sparse/background options.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

PROPERTY_COMBINATION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="ttl_with_sparse",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_sparse",
                "expireAfterSeconds": 3600,
                "sparse": True,
            },
        ),
        msg="Should allow TTL + sparse",
    ),
    IndexTestCase(
        id="ttl_with_partial_filter",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_partial",
                "expireAfterSeconds": 3600,
                "partialFilterExpression": {"status": "active"},
            },
        ),
        msg="Should allow TTL + partialFilterExpression",
    ),
    IndexTestCase(
        id="ttl_with_unique",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_unique",
                "expireAfterSeconds": 3600,
                "unique": True,
            },
        ),
        msg="Should allow TTL + unique",
    ),
    IndexTestCase(
        id="ttl_with_collation",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_collation",
                "expireAfterSeconds": 3600,
                "collation": {"locale": "en"},
            },
        ),
        msg="Should allow TTL + collation",
    ),
    IndexTestCase(
        id="ttl_with_sparse_and_unique",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_sparse_unique",
                "expireAfterSeconds": 3600,
                "sparse": True,
                "unique": True,
            },
        ),
        msg="Should allow TTL + sparse + unique",
    ),
    IndexTestCase(
        id="sparse_with_collation",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_sparse",
                "sparse": True,
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        msg="Should create sparse index with collation",
    ),
    IndexTestCase(
        id="background_with_collation",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_bg",
                "background": True,
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        msg="Should create index with background option and collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_COMBINATION_TESTS))
def test_property_combination(collection, test):
    """Test that indexes can be created with combined properties."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, index_created_response(), msg=test.msg)
