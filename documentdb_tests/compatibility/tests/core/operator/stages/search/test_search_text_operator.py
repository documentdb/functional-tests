"""Tests for $search text operator options (path forms, matchCriteria, score, fuzzy)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    QUERY_CLAUSE_CAP,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)

pytestmark = pytest.mark.requires(search=True)


# Property [text Path Forms]: the text operator accepts a {value} document, a
# {wildcard} document, and an array of paths, each resolving to the covered
# field(s) it names.
SEARCH_TEXT_PATH_FORMS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "path_value_document",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": {"value": "title"}}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a {value} path document resolving to the named field",
    ),
    StageTestCase(
        "path_wildcard_document",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": {"wildcard": "*"}}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a {wildcard} path document spanning every covered field",
    ),
    StageTestCase(
        "path_array",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": ["title", "body"]}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept an array of paths and match across all of them",
    ),
]

# Property [text matchCriteria]: matchCriteria "all" requires every query term to
# be present (AND) while "any" requires only one (OR).
SEARCH_TEXT_MATCH_CRITERIA_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_criteria_all",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick brown", "path": "title", "matchCriteria": "all"}
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search should match only documents containing every term when matchCriteria is all",
    ),
    StageTestCase(
        "match_criteria_any",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick brown", "path": "title", "matchCriteria": "any"}
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should match documents containing any term when matchCriteria is any",
    ),
]

# Property [text score Document]: the text operator accepts a score document and
# still returns the matched documents.
SEARCH_TEXT_SCORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_document",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "quick",
                        "path": "title",
                        "score": {"boost": {"value": 2.0}},
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a text.score document and still return the matches",
    ),
]

# Property [text query Array Cap]: a query array of the maximum 1024 elements
# (inclusive) is accepted and matches as a multi-term OR.
SEARCH_TEXT_QUERY_ARRAY_CAP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "query_array_max_clauses",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": ["quick"] + [f"nomatch{i}" for i in range(QUERY_CLAUSE_CAP - 1)],
                        "path": "title",
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a query array sized at the inclusive clause cap",
    ),
]

# Property [text Fuzzy Matching]: the text operator accepts a fuzzy document and
# matches within a code-point-based edit distance applied independently per
# query-array element.
SEARCH_TEXT_FUZZY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fuzzy_empty_document",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "fuzzy": {}}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept an empty fuzzy document and still match the exact term",
    ),
    StageTestCase(
        "fuzzy_max_edits_1_codepoint",
        # cafe -> café is one code-point edit (é ↔ e), not two bytes.
        pipeline=[
            {"$search": {"text": {"query": "cafe", "path": "title", "fuzzy": {"maxEdits": 1}}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 11)]},
        msg="$search should treat an accent difference as one code-point edit at maxEdits 1",
    ),
    StageTestCase(
        "fuzzy_max_edits_2_codepoint",
        # resume -> résumé is two code-point edits.
        pipeline=[
            {"$search": {"text": {"query": "resume", "path": "title", "fuzzy": {"maxEdits": 2}}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 5), Contains("_id", 10)]},
        msg="$search should match within two code-point edits at maxEdits 2",
    ),
    StageTestCase(
        "fuzzy_max_expansions_min",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "cafe",
                        "path": "title",
                        "fuzzy": {"maxEdits": 1, "maxExpansions": 1},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 11)]},
        msg="$search should accept fuzzy.maxExpansions at the lower bound and still match",
    ),
    StageTestCase(
        "fuzzy_max_expansions_max",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "cafe",
                        "path": "title",
                        "fuzzy": {"maxEdits": 1, "maxExpansions": 1000},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 11)]},
        msg="$search should accept fuzzy.maxExpansions at the upper bound and still match",
    ),
    StageTestCase(
        "fuzzy_per_element_array",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": ["quik", "turtl"],
                        "path": "title",
                        "fuzzy": {"maxEdits": 1},
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should apply fuzzy matching independently to each query-array element",
    ),
]

# Property [text Fuzzy prefixLength]: fuzzy.prefixLength locks a code-point-counted
# prefix from edits, so a typo within that prefix does not match.
SEARCH_TEXT_FUZZY_PREFIX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fuzzy_prefix_unlocked",
        # éfoy -> éfox is one edit at code point 3; prefixLength 0 locks nothing.
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "\u00e9foy",
                        "path": "title",
                        "fuzzy": {"maxEdits": 1, "prefixLength": 0},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 18)]},
        msg="$search should allow a fuzzy edit outside the prefix when prefixLength is 0",
    ),
    StageTestCase(
        "fuzzy_prefix_locked_codepoint",
        # prefixLength 4 locks all four code points of éfox (5 bytes), so the typo
        # at code point 3 falls inside the locked prefix; byte counting would lock
        # only éfo (3 code points) and still allow the edit.
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "\u00e9foy",
                        "path": "title",
                        "fuzzy": {"maxEdits": 1, "prefixLength": 4},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should count prefixLength in code points so a locked-prefix typo does "
        "not match",
    ),
]

SEARCH_TEXT_OPERATOR_TESTS = (
    SEARCH_TEXT_PATH_FORMS_TESTS
    + SEARCH_TEXT_MATCH_CRITERIA_TESTS
    + SEARCH_TEXT_SCORE_TESTS
    + SEARCH_TEXT_QUERY_ARRAY_CAP_TESTS
    + SEARCH_TEXT_FUZZY_TESTS
    + SEARCH_TEXT_FUZZY_PREFIX_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_TEXT_OPERATOR_TESTS))
def test_search_text_operator_cases(indexed_collection, test_case: StageTestCase):
    """Test $search text operator path forms, matchCriteria, score, fuzzy."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )
