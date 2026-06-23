"""Tests for $search recognized-but-unsupported operator validation (hierarchy, vector)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SEARCH_EXECUTOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(search=True)


# Property [EmbeddedDocument/HasAncestor/HasRoot Validation]: each
# hierarchical-relationship operator rejects a spec that targets a non-embedded
# path or omits its required sub-field with a validation error.
SEARCH_HIERARCHY_OP_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "embedded_document_non_subfield_path",
        pipeline=[
            {
                "$search": {
                    "embeddedDocument": {
                        "path": "title",
                        "operator": {"text": {"query": "quick", "path": "title"}},
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search embeddedDocument should reject a path not mapped as an "
        "embeddedDocuments field",
    ),
    StageTestCase(
        "has_ancestor_missing_ancestor_path",
        pipeline=[{"$search": {"hasAncestor": {}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search hasAncestor should reject a spec missing the required ancestorPath",
    ),
    StageTestCase(
        "has_root_missing_operator",
        pipeline=[{"$search": {"hasRoot": {}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search hasRoot should reject a spec missing the required operator",
    ),
]

# Property [Vector-Search Operator Validation]: the vectorSearch and knnBeta
# operators are recognized but reject a non-vector index and any malformed or
# missing required field with a validation error.
SEARCH_VECTOR_OP_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "vector_search_non_vector_index",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {
                        "path": "title",
                        "queryVector": [0.1, 0.2, 0.3],
                        "numCandidates": 10,
                        "limit": 5,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject a path not indexed as vector",
    ),
    StageTestCase(
        "vector_search_index_inside_operator",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {
                        "path": "title",
                        "queryVector": [0.1, 0.2, 0.3],
                        "numCandidates": 10,
                        "limit": 5,
                        "index": "default",
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject an index field placed inside the operator",
    ),
    StageTestCase(
        "vector_search_non_array_query_vector",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {
                        "path": "title",
                        "queryVector": "not_an_array",
                        "numCandidates": 10,
                        "limit": 5,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject a non-array queryVector",
    ),
    StageTestCase(
        "vector_search_string_query_vector",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {
                        "path": "title",
                        "queryVector": ["a", "b", "c"],
                        "numCandidates": 10,
                        "limit": 5,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject a queryVector array of strings",
    ),
    StageTestCase(
        "vector_search_empty_query_vector",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {
                        "path": "title",
                        "queryVector": [],
                        "numCandidates": 10,
                        "limit": 5,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject an empty queryVector",
    ),
    StageTestCase(
        "vector_search_missing_query_vector",
        pipeline=[
            {"$search": {"vectorSearch": {"path": "title", "numCandidates": 10, "limit": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject a spec missing both query and queryVector",
    ),
    StageTestCase(
        "vector_search_missing_path",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {
                        "queryVector": [0.1, 0.2, 0.3],
                        "numCandidates": 10,
                        "limit": 5,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject a spec missing the required path",
    ),
    StageTestCase(
        "vector_search_missing_num_candidates",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {"path": "title", "queryVector": [0.1, 0.2, 0.3], "limit": 5}
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject a spec missing the required numCandidates",
    ),
    StageTestCase(
        "vector_search_missing_limit",
        pipeline=[
            {
                "$search": {
                    "vectorSearch": {
                        "path": "title",
                        "queryVector": [0.1, 0.2, 0.3],
                        "numCandidates": 10,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search vectorSearch should reject a spec missing the required limit",
    ),
    StageTestCase(
        "knn_beta_non_knn_vector_index",
        pipeline=[
            {"$search": {"knnBeta": {"path": "title", "vector": [0.1, 0.2, 0.3], "k": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search knnBeta should reject a path not indexed as knnVector",
    ),
    StageTestCase(
        "knn_beta_non_array_vector",
        pipeline=[
            {"$search": {"knnBeta": {"path": "title", "vector": "not_an_array", "k": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search knnBeta should reject a non-array vector",
    ),
    StageTestCase(
        "knn_beta_empty_vector",
        pipeline=[
            {"$search": {"knnBeta": {"path": "title", "vector": [], "k": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search knnBeta should reject an empty vector",
    ),
    StageTestCase(
        "knn_beta_string_vector",
        pipeline=[
            {"$search": {"knnBeta": {"path": "title", "vector": ["a", "b", "c"], "k": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search knnBeta should reject a vector array of strings",
    ),
    StageTestCase(
        "knn_beta_missing_vector",
        pipeline=[{"$search": {"knnBeta": {"path": "title", "k": 5}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search knnBeta should reject a spec missing the required vector",
    ),
    StageTestCase(
        "knn_beta_missing_k",
        pipeline=[
            {"$search": {"knnBeta": {"path": "title", "vector": [0.1, 0.2, 0.3]}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search knnBeta should reject a spec missing the required k",
    ),
    StageTestCase(
        "knn_beta_missing_path",
        pipeline=[
            {"$search": {"knnBeta": {"vector": [0.1, 0.2, 0.3], "k": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search knnBeta should reject a spec missing the required path",
    ),
]

SEARCH_UNSUPPORTED_OP_ERROR_TESTS = SEARCH_HIERARCHY_OP_ERROR_TESTS + SEARCH_VECTOR_OP_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_UNSUPPORTED_OP_ERROR_TESTS))
def test_search_unsupported_operator_errors(indexed_collection, test_case: StageTestCase):
    """Test $search recognized-but-unsupported hierarchy and vector operators reject their specs."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
