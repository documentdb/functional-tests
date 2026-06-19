"""Tests for $searchMeta string-facet bucket selection and ordering."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from bson import Int64
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    build_collection,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def string_facet_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Indexed collection with a token mapping for string faceting.

    String facets are rejected under a plain dynamic mapping, so this collection
    declares an explicit token mapping. Category counts (a=3, b=2, c=1) make
    truncation and ordering by count observable.
    """
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::string_facet_collection",
        "searchmeta_string_facet",
        [
            {"_id": 1, "cat": "a"},
            {"_id": 2, "cat": "b"},
            {"_id": 3, "cat": "a"},
            {"_id": 4, "cat": "c"},
            {"_id": 5, "cat": "b"},
            {"_id": 6, "cat": "a"},
        ],
        [
            {
                "name": "default",
                "definition": {
                    "mappings": {"dynamic": True, "fields": {"cat": [{"type": "token"}]}}
                },
            }
        ],
    ) as coll:
        yield coll


# Property [Facet String NumBuckets]: numBuckets greater than the distinct value
# count returns all buckets, while fewer truncates to the top-N values by count.
SEARCHMETA_STRING_NUMBUCKETS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_numbuckets_all",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {"facets": {"sf": {"type": "string", "path": "cat", "numBuckets": 10}}}
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(6)},
                "facet": {
                    "sf": {
                        "buckets": [
                            {"_id": "a", "count": Int64(3)},
                            {"_id": "b", "count": Int64(2)},
                            {"_id": "c", "count": Int64(1)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta string facet should return all buckets when numBuckets exceeds the "
        "distinct value count",
    ),
    StageTestCase(
        "string_numbuckets_topn",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {"facets": {"sf": {"type": "string", "path": "cat", "numBuckets": 2}}}
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(6)},
                "facet": {
                    "sf": {
                        "buckets": [
                            {"_id": "a", "count": Int64(3)},
                            {"_id": "b", "count": Int64(2)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta string facet should truncate to the top-N values by count when "
        "numBuckets is below the distinct value count",
    ),
]

# Property [Facet Empty Buckets]: a no-match query yields an empty buckets array
# for a string facet, which emits only buckets backed by matching values.
SEARCHMETA_STRING_EMPTY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_facet_no_match_empty_buckets",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "operator": {"text": {"query": "nonexistentxyz", "path": "cat"}},
                        "facets": {"sf": {"type": "string", "path": "cat"}},
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": INT64_ZERO},
                "facet": {"sf": {"buckets": []}},
            }
        ],
        msg="$searchMeta string facet should return an empty buckets array when no document "
        "matches the query",
    ),
]

SEARCHMETA_STRING_FACET_TESTS: list[StageTestCase] = (
    SEARCHMETA_STRING_NUMBUCKETS_TESTS + SEARCHMETA_STRING_EMPTY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_STRING_FACET_TESTS))
def test_searchMeta_string_facet(string_facet_collection, test_case: StageTestCase):
    """Test $searchMeta string facet bucket selection and ordering."""
    result = execute_command(
        string_facet_collection,
        {
            "aggregate": string_facet_collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
