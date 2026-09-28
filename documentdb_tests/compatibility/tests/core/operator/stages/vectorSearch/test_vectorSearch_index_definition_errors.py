"""Tests for the $vectorSearch stage: vectorSearch index definition errors.

These are createSearchIndexes-time validation errors for definition options that
the $vectorSearch surface owns (nestedRoot, storedSource, and the vector field's
numDimensions, against which a query vector's length is checked). They fail
synchronously at index-create time, so unlike the query-path tests they do not
build a READY index or run an aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_FAILED_ERROR,
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

pytestmark = pytest.mark.requires(search=True)


@dataclass(frozen=True)
class IndexDefinitionErrorTest(BaseTestCase):
    """A vectorSearch index definition that createSearchIndexes must reject."""

    definition: dict[str, Any] = field(default_factory=dict)


# Property [nestedRoot Path Mismatch]: a vectorSearch index whose nestedRoot does
# not name any vector field path in the definition is rejected at index-create time.
VECTORSEARCH_NESTED_ROOT_MISMATCH_ERROR_TESTS: list[IndexDefinitionErrorTest] = [
    IndexDefinitionErrorTest(
        "nested_root_does_not_match_vector_path",
        definition={
            "nestedRoot": "nonexistent",
            "fields": [
                {
                    "type": "vector",
                    "path": "reviews.embedding",
                    "numDimensions": 3,
                    "similarity": "cosine",
                }
            ],
        },
        error_code=COMMAND_FAILED_ERROR,
        msg="createSearchIndexes should reject a vectorSearch index whose nestedRoot "
        "does not match any vector field path",
    ),
]

# Property [storedSource true Unsupported]: a vectorSearch index defined with
# storedSource: true is rejected at index-create time, because only include,
# exclude, or false are accepted.
VECTORSEARCH_STORED_SOURCE_TRUE_ERROR_TESTS: list[IndexDefinitionErrorTest] = [
    IndexDefinitionErrorTest(
        "stored_source_true_unsupported",
        definition={
            "storedSource": True,
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": 3,
                    "similarity": "cosine",
                }
            ],
        },
        error_code=UNKNOWN_ERROR,
        msg="createSearchIndexes should reject a vectorSearch index defined with "
        "storedSource true",
    ),
]

# Property [numDimensions Bounds]: a vector field whose numDimensions falls
# outside the accepted range is rejected at index-create time, asserted at both
# boundaries.
VECTORSEARCH_NUM_DIMENSIONS_BOUNDS_ERROR_TESTS: list[IndexDefinitionErrorTest] = [
    IndexDefinitionErrorTest(
        f"num_dimensions_bounds_{tid}",
        definition={
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": ndim,
                    "similarity": "cosine",
                }
            ],
        },
        error_code=UNKNOWN_ERROR,
        msg=f"createSearchIndexes should reject a vector field with a {tid} "
        "numDimensions as out of bounds",
    )
    for tid, ndim in [
        ("below_lower", 0),
        ("above_upper", 8193),
    ]
]

VECTORSEARCH_INDEX_DEFINITION_ERROR_TESTS = (
    VECTORSEARCH_NESTED_ROOT_MISMATCH_ERROR_TESTS
    + VECTORSEARCH_STORED_SOURCE_TRUE_ERROR_TESTS
    + VECTORSEARCH_NUM_DIMENSIONS_BOUNDS_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_INDEX_DEFINITION_ERROR_TESTS))
def test_vectorSearch_index_definition_errors(test_case: IndexDefinitionErrorTest, collection):
    """$vectorSearch: vectorSearch index definition errors."""
    collection.insert_one(
        {
            "_id": 1,
            "embedding": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
            "reviews": [{"embedding": [1.0, DOUBLE_ZERO, DOUBLE_ZERO], "rating": 5}],
        }
    )
    result = execute_command(
        collection,
        {
            "createSearchIndexes": collection.name,
            "indexes": [
                {"name": "vidx", "type": "vectorSearch", "definition": test_case.definition}
            ],
        },
    )
    assertResult(
        result,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
