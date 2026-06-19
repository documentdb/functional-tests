"""Tests for $searchMeta number-facet bucketing result behavior."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from bson import Int64
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    CollectionFixtureTestCase,
    build_collection,
    open_search_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Module-scoped metadata search collection (default + alt_idx indexes)."""
    with open_search_collection(engine_client, worker_id, f"{__name__}::search_collection") as coll:
        yield coll


# Dates spanning two query buckets: ids 1-3 fall in the first interval and ids
# 4-5 in the second, so the asserted bucket counts (3 and 2) are observable.
_DATE_FACET_DOCS = [
    {"_id": 1, "d": datetime(2024, 1, 15, tzinfo=timezone.utc)},
    {"_id": 2, "d": datetime(2024, 2, 15, tzinfo=timezone.utc)},
    {"_id": 3, "d": datetime(2024, 3, 15, tzinfo=timezone.utc)},
    {"_id": 4, "d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
    {"_id": 5, "d": datetime(2024, 9, 15, tzinfo=timezone.utc)},
]


@pytest.fixture(scope="module")
def date_facet_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Indexed collection with an explicit date mapping for date faceting.

    The faceted field carries an explicit ``date`` mapping so the index types it
    as a date rather than relying on dynamic mapping.
    """
    with build_collection(
        engine_client,
        worker_id,
        f"{__name__}::date_facet_collection",
        "searchmeta_date_facet",
        _DATE_FACET_DOCS,
        [
            {
                "name": "default",
                "definition": {"mappings": {"dynamic": True, "fields": {"d": [{"type": "date"}]}}},
            }
        ],
    ) as coll:
        yield coll


# Property [Facet Collector Envelope]: a facet collector returns a combined
# count sub-document and per-name buckets array; the count defaults to lowerBound
# and the embedded operator is optional (omitting it matches all documents).
SEARCHMETA_FACET_ENVELOPE_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "facet_envelope_with_operator",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "operator": {"text": {"query": "quick", "path": "title"}},
                        "facets": {
                            "nf": {"type": "number", "path": "n", "boundaries": [0, 5, 10, 25]}
                        },
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(3)},
                "facet": {
                    "nf": {
                        "buckets": [
                            {"_id": 0, "count": Int64(1)},
                            {"_id": 5, "count": Int64(1)},
                            {"_id": 10, "count": Int64(1)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta facet collector should return a combined count and facet buckets "
        "envelope for an embedded operator",
    ),
    CollectionFixtureTestCase(
        "facet_envelope_match_all",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 10, 25]}}
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "nf": {
                        "buckets": [
                            {"_id": 0, "count": Int64(2)},
                            {"_id": 10, "count": Int64(3)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta facet collector should match all documents and default to a "
        "lower-bound count when the operator is omitted",
    ),
]

# Property [Facet Number Bucket Boundaries]: each number-facet bucket _id is the
# lower boundary of its range, and float boundaries are preserved as double _id
# values.
SEARCHMETA_FACET_BOUNDARY_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "facet_number_float_boundaries",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0.5, 10.5, 25.5],
                            }
                        }
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "nf": {
                        "buckets": [
                            {"_id": 0.5, "count": Int64(3)},
                            {"_id": 10.5, "count": Int64(2)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta number facet should preserve float boundaries as double bucket _ids",
    ),
]

# Property [Facet Default Overflow Bucket]: a default overflow bucket is emitted
# only when default is set, is always emitted when set (including with zero
# overflow), and its string _id never collides with a numeric boundary _id.
SEARCHMETA_FACET_DEFAULT_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "facet_default_omitted_drops_overflow",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 5]}}
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {"nf": {"buckets": [{"_id": 0, "count": Int64(1)}]}},
            }
        ],
        msg="$searchMeta number facet should drop out-of-range values when no default is set",
    ),
    CollectionFixtureTestCase(
        "facet_default_emits_overflow",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0, 5, 10],
                                "default": "over",
                            }
                        }
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "nf": {
                        "buckets": [
                            {"_id": 0, "count": Int64(1)},
                            {"_id": 5, "count": Int64(1)},
                            {"_id": "over", "count": Int64(3)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta number facet should collect out-of-range values into the default "
        "overflow bucket when default is set",
    ),
    CollectionFixtureTestCase(
        "facet_default_zero_overflow",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0, 100],
                                "default": "over",
                            }
                        }
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "nf": {
                        "buckets": [
                            {"_id": 0, "count": Int64(5)},
                            {"_id": "over", "count": INT64_ZERO},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta number facet should emit the default overflow bucket with a zero "
        "count when no values overflow",
    ),
    CollectionFixtureTestCase(
        "facet_default_string_id_no_collision",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0, 5],
                                "default": "0",
                            }
                        }
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "nf": {
                        "buckets": [
                            {"_id": 0, "count": Int64(1)},
                            {"_id": "0", "count": Int64(4)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta number facet should keep a string default _id distinct from a "
        "numeric boundary _id of the same digits",
    ),
]

# Property [Facet Zero-Match Buckets]: a zero-match facet query over an indexed
# collection returns the bucket structure with zero counts.
SEARCHMETA_FACET_ZERO_MATCH_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "facet_zero_match",
        collection_fixture="search_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "operator": {"text": {"query": "nonexistentxyz", "path": "title"}},
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 2, 25]}},
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": INT64_ZERO},
                "facet": {
                    "nf": {
                        "buckets": [
                            {"_id": 0, "count": INT64_ZERO},
                            {"_id": 2, "count": INT64_ZERO},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta facet collector should return zero-count buckets for a zero-match "
        "query",
    ),
]

# Property [Facet Date Bucket Boundaries]: each date-facet bucket _id is its
# range's lower-boundary datetime, and datetimes are bucketed like number facets.
SEARCHMETA_DATE_FACET_TESTS: list[CollectionFixtureTestCase] = [
    CollectionFixtureTestCase(
        "date_facet_boundaries",
        collection_fixture="date_facet_collection",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "df": {
                                "type": "date",
                                "path": "d",
                                "boundaries": [
                                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                                    datetime(2024, 4, 1, tzinfo=timezone.utc),
                                    datetime(2024, 12, 1, tzinfo=timezone.utc),
                                ],
                            }
                        }
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "df": {
                        "buckets": [
                            {"_id": datetime(2024, 1, 1, tzinfo=timezone.utc), "count": Int64(3)},
                            {"_id": datetime(2024, 4, 1, tzinfo=timezone.utc), "count": Int64(2)},
                        ]
                    }
                },
            }
        ],
        msg="$searchMeta date facet should bucket datetimes by their lower boundary and echo "
        "each bucket _id as the boundary datetime",
    ),
]

# Number facets run against the standard search collection; date faceting needs
# an index with an explicit date mapping, so its case names a different fixture.
# Both share one execution path, with the collection carried as data.
SEARCHMETA_FACET_RESULT_TESTS: list[CollectionFixtureTestCase] = (
    SEARCHMETA_FACET_ENVELOPE_TESTS
    + SEARCHMETA_FACET_BOUNDARY_TESTS
    + SEARCHMETA_FACET_DEFAULT_TESTS
    + SEARCHMETA_FACET_ZERO_MATCH_TESTS
    + SEARCHMETA_DATE_FACET_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_FACET_RESULT_TESTS))
def test_searchMeta_facets(engine_client, request, test_case: CollectionFixtureTestCase):
    """Test $searchMeta number- and date-facet bucket result behavior."""
    collection = request.getfixturevalue(test_case.collection_fixture)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
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
