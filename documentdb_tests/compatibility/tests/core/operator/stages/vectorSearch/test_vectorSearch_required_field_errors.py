"""Tests for the $vectorSearch stage: required-field and null-as-absent errors."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_NOT_OBJECT_ERROR,
    UNKNOWN_ERROR,
    VECTOR_SEARCH_LIMIT_NOT_NUMBER_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [Required Fields and Null-as-Absent]: each required field, when
# omitted or set to null, surfaces that field's required-field error with null
# treated as field-absent, except limit null (a type error) and filter null (a
# parse error), which are not treated as absent.
VECTORSEARCH_REQUIRED_FIELD_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "index_omitted",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should require the index field when it is omitted",
    ),
    VectorSearchTest(
        "index_null",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": None,
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should treat index null as field-absent and require the index field",
    ),
    VectorSearchTest(
        "path_omitted",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should require the path field when it is omitted",
    ),
    VectorSearchTest(
        "path_null",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": None,
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should treat path null as field-absent and require the path field",
    ),
    VectorSearchTest(
        "query_vector_omitted",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should require queryVector when it is omitted",
    ),
    VectorSearchTest(
        "query_vector_null",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": None,
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should treat queryVector null as field-absent and require queryVector",
    ),
    VectorSearchTest(
        "limit_omitted",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should require the limit field when it is omitted",
    ),
    VectorSearchTest(
        "limit_omitted_enn",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": True,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should require the limit field when it is omitted under ENN",
    ),
    VectorSearchTest(
        "limit_null",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": None,
                }
            }
        ],
        error_code=VECTOR_SEARCH_LIMIT_NOT_NUMBER_ERROR,
        msg="$vectorSearch should treat limit null as a wrong type rather than field-absent",
    ),
    VectorSearchTest(
        "num_candidates_omitted",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should require numCandidates for ANN when it is omitted",
    ),
    VectorSearchTest(
        "num_candidates_null",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": None,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should treat numCandidates null as field-absent and require it for ANN",
    ),
    VectorSearchTest(
        "filter_null",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": None,
                }
            }
        ],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$vectorSearch should reject filter null as a non-object, not treat it as omitted",
    ),
    VectorSearchTest(
        "empty_spec",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[{"$vectorSearch": {}}],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should require the index field for an empty spec",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_REQUIRED_FIELD_ERROR_TESTS))
def test_vectorSearch_required_field_errors(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: required-field and null-as-absent errors."""
    coll = request.getfixturevalue(test_case.collection_fixture)
    result = execute_command(
        coll,
        {"aggregate": coll.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
