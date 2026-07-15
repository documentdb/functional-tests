"""Tests for the $vectorSearch stage: index and path resolution."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    Len,
    PerDoc,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [index Exact Name Match]: the correct existing index name resolves and
# returns the collection's similarity-ordered documents.
VECTORSEARCH_INDEX_MATCH_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "match_correct_name",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected=PerDoc(
            {"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}, {"_id": Eq(4)}, {"_id": Eq(5)}
        ),
        msg="$vectorSearch should resolve the correct existing index name and return results",
    ),
]

# Property [index Name Silent Miss]: an index name that is not byte-for-byte the
# existing index name returns zero results with no error, because matching is
# exact and literal rather than fuzzy or expression-evaluated.
VECTORSEARCH_INDEX_SILENT_MISS_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"silent_miss_{tid}",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": name,
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg=f"$vectorSearch should silently return zero results for a {tid} index name",
    )
    for tid, name in [
        ("nonexistent", "no_such_index"),
        ("case_variant", "vs_core_index".upper()),
        ("leading_space", " vs_core_index"),
        ("trailing_space", "vs_core_index "),
        ("tab", "vs_core_index\t"),
        ("newline", "vs_core_index\n"),
        ("dollar_prefix", "$vs_core_index"),
        ("dollar_only", "$"),
        ("dollar_now_variable", "$$NOW"),
        ("double_dollar", "$$"),
        ("null_byte", "vs_core_index\x00"),
        ("control_char", "vs\x01core"),
        ("punctuation", '{vs}"core",;'),
        # "e" + U+0301 combining acute accent, not the precomposed "é" (U+00E9).
        ("unicode_combining", "vse\u0301core"),
        ("cjk", "向量索引"),
        ("emoji", "🔍index"),
    ]
]

# Property [index Nonexistent Skips Dimension Check]: a nonexistent index name
# combined with a dimension-mismatched queryVector still returns zero results with
# no error, because the dimension check is skipped when the named index is absent.
VECTORSEARCH_INDEX_DIMENSION_SKIP_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "nonexistent_skips_dimension_check",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "no_such_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should return zero results without a dimension error when "
        "the named index does not exist",
    ),
]

# Property [path Field Resolution]: a path naming the correct vector-indexed
# field resolves and returns the collection's similarity-ordered documents,
# including a dot-notation path resolved against a nested-path index.
VECTORSEARCH_PATH_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"path_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": path,
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected=PerDoc(
            {"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}, {"_id": Eq(4)}, {"_id": Eq(5)}
        ),
        msg=f"$vectorSearch should resolve the {tid} vector path and return results",
    )
    for tid, path in [
        ("top_level", "ve"),
        ("dot_notation_nested", "meta.vec"),
    ]
]

VECTORSEARCH_INDEX_PATH_ALL_TESTS = (
    VECTORSEARCH_INDEX_MATCH_TESTS
    + VECTORSEARCH_INDEX_SILENT_MISS_TESTS
    + VECTORSEARCH_INDEX_DIMENSION_SKIP_TESTS
    + VECTORSEARCH_PATH_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_INDEX_PATH_ALL_TESTS))
def test_vectorSearch_index_path(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: index and path resolution."""
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
        raw_res=test_case.raw_res,
    )
