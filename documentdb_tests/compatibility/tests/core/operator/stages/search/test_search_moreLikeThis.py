"""Tests for the $search moreLikeThis operator."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Len

pytestmark = pytest.mark.requires(search=True)


# Property [moreLikeThis Similarity]: a like seed document returns the documents
# that share indexed terms with it, and excludes documents that share none.
SEARCH_MORELIKETHIS_SUCCESS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "morelikethis_like_document",
        pipeline=[{"$search": {"moreLikeThis": {"like": {"title": "quick brown fox"}}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search moreLikeThis should return documents sharing terms with the like seed "
        "document",
    ),
]

# Property [moreLikeThis Validation]: moreLikeThis requires a like field that is
# a document (or array of documents), so an omitted or non-document like is
# rejected.
SEARCH_MORELIKETHIS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "morelikethis_missing_like",
        pipeline=[{"$search": {"moreLikeThis": {}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search moreLikeThis should reject a spec missing the required like field",
    ),
    StageTestCase(
        "morelikethis_like_non_document",
        pipeline=[{"$search": {"moreLikeThis": {"like": "quick"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search moreLikeThis should reject a non-document like value",
    ),
]

SEARCH_MORELIKETHIS_TESTS = SEARCH_MORELIKETHIS_SUCCESS_TESTS + SEARCH_MORELIKETHIS_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_MORELIKETHIS_TESTS))
def test_search_moreLikeThis_cases(indexed_collection, test_case: StageTestCase):
    """Test $search moreLikeThis similarity matching and validation."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
