"""Tests for $search text operator core matching behavior."""

from __future__ import annotations

import pytest

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


# Property [Index-Covered Matching]: a text operator returns exactly the
# documents whose covered path contains the query token, and a path no document
# covers matches nothing.
SEARCH_MATCHING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "matching_covered_title",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should return the documents whose covered path contains the query token",
    ),
    StageTestCase(
        "matching_covered_body",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "body"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 2)]},
        msg="$search should match only on the specific covered path named in the operator",
    ),
    StageTestCase(
        "matching_uncovered_path",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "nope"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should return no documents for a path no document covers",
    ),
]

# Property [Literal Spec Values]: $search spec values are interpreted as literal
# data, never as field paths, system variables, or expressions.
SEARCH_LITERAL_SPEC_TESTS: list[StageTestCase] = [
    StageTestCase(
        "literal_path_empty",
        pipeline=[{"$search": {"text": {"query": "quick", "path": ""}}}],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should treat an empty path as literal data and match nothing without error",
    ),
    StageTestCase(
        "literal_path_field_ref",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "$title"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should treat a $-prefixed path as literal data, not a field reference",
    ),
    StageTestCase(
        "literal_path_dotted",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "a.b"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should treat a dotted path as literal data with no field-path validation",
    ),
    StageTestCase(
        "literal_path_null_byte",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "ti\x00tle"}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should treat a null-byte path as literal data and match nothing without error",
    ),
    StageTestCase(
        "literal_query_dollar",
        pipeline=[
            {"$search": {"text": {"query": "$quick", "path": "title"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should match a $-prefixed query as literal text, not as a field reference",
    ),
]

# Property [Null Sub-field As Default]: a null document- or string-typed
# sub-field (index, count, highlight, sort, text.fuzzy) is treated as
# missing/default.
SEARCH_NULL_DEFAULT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_default_index",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "index": None}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should treat a null index as the default index and still match",
    ),
    StageTestCase(
        "null_default_count",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "count": None}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should treat a null count as omitted and still match",
    ),
    StageTestCase(
        "null_default_highlight",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "highlight": None}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should treat a null highlight as omitted and still match",
    ),
    StageTestCase(
        "null_default_sort",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "sort": None}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should treat a null sort as omitted and still match",
    ),
    StageTestCase(
        "null_default_fuzzy",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "fuzzy": None}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should treat a null text.fuzzy as omitted and still match",
    ),
]

# Property [Multi-Term OR]: a multi-term query array matches documents containing
# any of its terms.
SEARCH_MULTI_TERM_OR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multi_term_or",
        pipeline=[
            {"$search": {"text": {"query": ["quick", "turtle"], "path": "title"}}},
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
        msg="$search should match documents containing any term in a multi-term query array",
    ),
]

SEARCH_TEXT_BASICS_TESTS = (
    SEARCH_MATCHING_TESTS
    + SEARCH_LITERAL_SPEC_TESTS
    + SEARCH_NULL_DEFAULT_TESTS
    + SEARCH_MULTI_TERM_OR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_TEXT_BASICS_TESTS))
def test_search_text_basics_cases(indexed_collection, test_case: StageTestCase):
    """Test $search core text matching over an indexed collection."""
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
