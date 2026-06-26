"""Tests for $searchMeta facet boundary, numBuckets, and token-mapping errors."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    open_search_collection,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Module-scoped metadata search collection (default + alt_idx indexes)."""
    with open_search_collection(engine_client, worker_id, f"{__name__}::search_collection") as coll:
        yield coll


# Property [Facet Number Boundaries Validation]: number-facet boundaries must be
# two to a thousand distinct numbers in ascending order, so too few, too many,
# non-ascending, duplicate adjacent, or non-numeric boundaries are rejected.
SEARCHMETA_FACET_BOUNDARIES_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "boundaries_single_element",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {"facets": {"nf": {"type": "number", "path": "n", "boundaries": [0]}}}
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a number facet with fewer than two boundaries",
    ),
    StageTestCase(
        "boundaries_above_max",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": list(range(1_001)),
                            }
                        }
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a number facet with more than the maximum boundary count",
    ),
    StageTestCase(
        "boundaries_unsorted",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [40, 0, 20]}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject non-ascending number facet boundaries",
    ),
    StageTestCase(
        "boundaries_duplicate_adjacent",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 0, 25]}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject duplicate adjacent number facet boundaries as not distinct",
    ),
    StageTestCase(
        "boundaries_non_numeric",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": ["a", "b"]}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject non-numeric number facet boundaries",
    ),
]

# Property [Facet Date Boundaries Type]: a date facet with numeric (non-datetime)
# boundaries is rejected.
SEARCHMETA_FACET_DATE_BOUNDARIES_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "date_boundaries_numeric",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "date", "path": "n", "boundaries": [0, 25]}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject numeric boundaries for a date facet",
    ),
]

# Property [Facet NumBuckets Bounds]: a string-facet numBuckets outside
# [1..1000] is rejected.
SEARCHMETA_FACET_NUMBUCKETS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "numbuckets_zero",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {"facets": {"nf": {"type": "string", "path": "cat", "numBuckets": 0}}}
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a numBuckets below the lower bound",
    ),
    StageTestCase(
        "numbuckets_above_max",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "string", "path": "cat", "numBuckets": 1001}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a numBuckets above the upper bound",
    ),
]

# Property [Facet String Boundaries Unrecognized]: a string facet rejects the
# boundaries field as unrecognized.
SEARCHMETA_FACET_STRING_BOUNDARIES_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_facet_with_boundaries",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "string", "path": "cat", "boundaries": [0, 25]}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject boundaries on a string facet as an unrecognized field",
    ),
]

# Property [Facet Number NumBuckets Unrecognized]: a number facet rejects the
# numBuckets field as unrecognized.
SEARCHMETA_FACET_NUMBER_NUMBUCKETS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "number_facet_with_numbuckets",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0, 25],
                                "numBuckets": 1,
                            }
                        }
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject numBuckets on a number facet as an unrecognized field",
    ),
]

# Property [Facet Token Mapping]: a string facet on a dynamically-indexed field
# is rejected because dynamic mapping does not token-index string fields.
SEARCHMETA_FACET_TOKEN_MAPPING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_facet_dynamic_field",
        pipeline=[
            {"$searchMeta": {"facet": {"facets": {"nf": {"type": "string", "path": "cat"}}}}}
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject string faceting on a dynamically-indexed string field",
    ),
]

SEARCHMETA_SPEC_FACET_BOUNDARY_ERROR_TESTS: list[StageTestCase] = (
    SEARCHMETA_FACET_BOUNDARIES_ERROR_TESTS
    + SEARCHMETA_FACET_DATE_BOUNDARIES_ERROR_TESTS
    + SEARCHMETA_FACET_NUMBUCKETS_ERROR_TESTS
    + SEARCHMETA_FACET_STRING_BOUNDARIES_ERROR_TESTS
    + SEARCHMETA_FACET_NUMBER_NUMBUCKETS_ERROR_TESTS
    + SEARCHMETA_FACET_TOKEN_MAPPING_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_SPEC_FACET_BOUNDARY_ERROR_TESTS))
def test_searchMeta_spec_facet_boundary_errors(search_collection, test_case: StageTestCase):
    """Test $searchMeta facet boundary, numBuckets, and token-mapping errors."""
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
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
