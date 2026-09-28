"""Tests for $searchMeta facet count modifiers, key echo, and multiple facets."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(search=True)


# Property [Facet Stage Count Modifier]: a stage-level count modifier changes
# only the count sub-document flavor and leaves the facet result unchanged.
SEARCHMETA_FACET_COUNT_MODIFIER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_count_total",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}}
                    },
                    "count": {"type": "total"},
                }
            }
        ],
        expected=[
            {
                "count": {"total": Int64(5)},
                "facet": {"nf": {"buckets": [{"_id": 0, "count": Int64(5)}]}},
            }
        ],
        msg="$searchMeta should apply a stage-level total count modifier on top of the facet "
        "result without changing the buckets",
    ),
    StageTestCase(
        "facet_count_lower_bound",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}}
                    },
                    "count": {"type": "lowerBound"},
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {"nf": {"buckets": [{"_id": 0, "count": Int64(5)}]}},
            }
        ],
        msg="$searchMeta should apply a stage-level lower-bound count modifier on top of the "
        "facet result without changing the buckets",
    ),
]

# Property [Facet Key Echo]: facet map keys are not field-path validated and are
# echoed back verbatim as result keys.
SEARCHMETA_FACET_KEY_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"facet_key_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {key: {"type": "number", "path": "n", "boundaries": [0, 25]}}
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {key: {"buckets": [{"_id": 0, "count": Int64(5)}]}},
            }
        ],
        msg=f"$searchMeta should echo a {suffix} facet key verbatim without field-path "
        "validation",
    )
    for key, suffix in [
        ("", "empty"),
        ("$x", "dollar_prefixed"),
        ("a.b", "dotted"),
    ]
]

# Property [Multiple Facets in One Collector]: a collector with multiple named
# facets computes each independently under its own key while sharing one count
# sub-document; a default bucket on one facet does not affect a sibling without
# one.
SEARCHMETA_MULTI_FACET_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multi_facet_different_paths",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {"type": "number", "path": "n", "boundaries": [0, 10, 25]},
                            "idf": {"type": "number", "path": "_id", "boundaries": [0, 3, 10]},
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
                            {"_id": 0, "count": Int64(2)},
                            {"_id": 10, "count": Int64(3)},
                        ]
                    },
                    "idf": {
                        "buckets": [
                            {"_id": 0, "count": Int64(2)},
                            {"_id": 3, "count": Int64(3)},
                        ]
                    },
                },
            }
        ],
        msg="$searchMeta should compute sibling facets over different paths independently "
        "under a single shared count",
    ),
    StageTestCase(
        "multi_facet_same_path_different_boundaries",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf1": {"type": "number", "path": "n", "boundaries": [0, 10, 25]},
                            "nf2": {"type": "number", "path": "n", "boundaries": [0, 5, 25]},
                        }
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "nf1": {
                        "buckets": [
                            {"_id": 0, "count": Int64(2)},
                            {"_id": 10, "count": Int64(3)},
                        ]
                    },
                    "nf2": {
                        "buckets": [
                            {"_id": 0, "count": Int64(1)},
                            {"_id": 5, "count": Int64(4)},
                        ]
                    },
                },
            }
        ],
        msg="$searchMeta should compute sibling facets over the same path with different "
        "boundaries independently",
    ),
    StageTestCase(
        "multi_facet_independent_default",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "withd": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0, 5],
                                "default": "over",
                            },
                            "nod": {"type": "number", "path": "n", "boundaries": [0, 5]},
                        }
                    }
                }
            }
        ],
        expected=[
            {
                "count": {"lowerBound": Int64(5)},
                "facet": {
                    "withd": {
                        "buckets": [
                            {"_id": 0, "count": Int64(1)},
                            {"_id": "over", "count": Int64(4)},
                        ]
                    },
                    "nod": {"buckets": [{"_id": 0, "count": Int64(1)}]},
                },
            }
        ],
        msg="$searchMeta should keep a default overflow bucket independent per facet so a "
        "sibling without default drops its overflow",
    ),
]

SEARCHMETA_FACET_ADVANCED_TESTS: list[StageTestCase] = (
    SEARCHMETA_FACET_COUNT_MODIFIER_TESTS
    + SEARCHMETA_FACET_KEY_TESTS
    + SEARCHMETA_MULTI_FACET_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_FACET_ADVANCED_TESTS))
def test_searchMeta_facets_advanced(search_collection, test_case: StageTestCase):
    """Test $searchMeta facet count modifiers, key echo, and multiple facets."""
    result = execute_command(
        search_collection,
        {
            "aggregate": search_collection.name,
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
