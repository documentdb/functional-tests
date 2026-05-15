"""Tests for case-insensitive index creation.

Validates createIndex with collation options for case-insensitive indexes:
valid collation configurations, response structure, idempotent re-creation,
and numeric type variants for strength.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

VALID_CREATE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="strength_1_en",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci_s1", "collation": {"locale": "en", "strength": 1}},
        ),
        msg="Should create index with collation strength 1",
    ),
    IndexTestCase(
        id="locale_fr",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci_fr", "collation": {"locale": "fr", "strength": 2}},
        ),
        msg="Should create index with French locale",
    ),
    IndexTestCase(
        id="locale_de",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci_de", "collation": {"locale": "de", "strength": 2}},
        ),
        msg="Should create index with German locale",
    ),
    IndexTestCase(
        id="locale_es",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci_es", "collation": {"locale": "es", "strength": 2}},
        ),
        msg="Should create index with Spanish locale",
    ),
    IndexTestCase(
        id="compound_index",
        indexes=(
            {
                "key": {"a": 1, "b": 1},
                "name": "idx_ci_compound",
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        msg="Should create compound index with collation",
    ),
    IndexTestCase(
        id="with_partial",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_partial",
                "partialFilterExpression": {"status": "active"},
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        msg="Should create partial case-insensitive index",
    ),
    IndexTestCase(
        id="idempotent_same_index",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        setup_indexes=[
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}}
        ],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=2),
        msg="Re-creating identical index should be a no-op",
    ),
    IndexTestCase(
        id="strength_3_case_sensitive_create",
        indexes=(
            {"key": {"name": 1}, "name": "idx_s3", "collation": {"locale": "en", "strength": 3}},
        ),
        msg="Should create index with strength 3 (case-sensitive with diacritics)",
    ),
    IndexTestCase(
        id="strength_null_defaults",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_null_str",
                "collation": {"locale": "en", "strength": None},
            },
        ),
        msg="Should create index with null strength (uses default)",
    ),
    IndexTestCase(
        id="descending_key",
        indexes=(
            {
                "key": {"name": -1},
                "name": "idx_ci_desc",
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        msg="Should create descending index with collation",
    ),
    IndexTestCase(
        id="strength_as_float",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_float",
                "collation": {"locale": "en", "strength": 2.0},
            },
        ),
        msg="Should create index with float strength",
    ),
    IndexTestCase(
        id="strength_as_int64",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_int64",
                "collation": {"locale": "en", "strength": Int64(2)},
            },
        ),
        msg="Should create index with Int64 strength",
    ),
    IndexTestCase(
        id="strength_as_decimal128",
        indexes=(
            {
                "key": {"name": 1},
                "name": "idx_ci_dec",
                "collation": {"locale": "en", "strength": Decimal128("2")},
            },
        ),
        msg="Should create index with Decimal128 strength",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_CREATE_TESTS))
def test_case_insensitive_create_valid(collection, test):
    """Test createIndex with valid collation options succeeds."""
    if test.setup_indexes:
        execute_command(
            collection,
            {"createIndexes": collection.name, "indexes": test.setup_indexes},
        )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    expected = test.expected if test.expected is not None else index_created_response()
    assertSuccessPartial(result, expected, msg=test.msg)


def test_case_insensitive_create_response_structure(collection):
    """Test createIndex with collation returns correct response fields."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}}
            ],
        },
    )
    expected = {
        "ok": 1.0,
        "createdCollectionAutomatically": True,
        "numIndexesBefore": 1,
        "numIndexesAfter": 2,
    }
    assertSuccessPartial(result, expected, msg="Should return standard createIndex response fields")
