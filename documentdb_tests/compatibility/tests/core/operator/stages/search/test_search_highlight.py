"""Tests for the $search highlight option and output."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Eq,
    Gt,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Highlight Path Forms]: highlight.path accepts a {wildcard} document
# and an array of paths (the string form is owned by the searchHighlights output
# property).
SEARCH_HIGHLIGHT_PATH_FORM_TESTS: list[StageTestCase] = [
    StageTestCase(
        "highlight_path_wildcard",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "highlight": {"path": {"wildcard": "*"}},
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
        msg="$search should accept a {wildcard} highlight.path and still return its matches",
    ),
    StageTestCase(
        "highlight_path_array",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "highlight": {"path": ["title", "body"]},
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
        msg="$search should accept an array highlight.path and still return its matches",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_HIGHLIGHT_PATH_FORM_TESTS))
def test_search_highlight_path_cases(indexed_collection, test_case: StageTestCase):
    """Test $search highlight path forms."""
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


# Property [SearchHighlights Output]: with highlight enabled, {$meta:
# "searchHighlights"} projects per-path entries that split matched tokens into
# "hit" spans and surrounding context into "text" spans, and a multi-byte matched
# token is highlighted intact as a single hit span with no offset corruption.
SEARCH_HIGHLIGHT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "highlight_ascii_hit_and_text_spans",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "highlight": {"path": "title"},
                }
            },
            {"$limit": 1},
            {"$project": {"_id": 0, "hl": {"$meta": "searchHighlights"}}},
        ],
        expected={
            "hl.0.path": Eq("title"),
            "hl.0.score": Gt(0),
            "hl.0.texts": [
                Contains("type", "hit"),
                Contains("type", "text"),
                Contains("value", "quick"),
            ],
        },
        msg="$search should tag matched tokens as hit spans and surrounding context as "
        "text spans",
    ),
    StageTestCase(
        "highlight_multibyte_intact_span",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "résumé", "path": "title"},
                    "highlight": {"path": "title"},
                }
            },
            {"$limit": 1},
            {"$project": {"_id": 0, "hl": {"$meta": "searchHighlights"}}},
        ],
        expected={
            "hl.0.path": Eq("title"),
            "hl.0.score": Gt(0),
            "hl.0.texts": [Contains("type", "hit"), Contains("value", "résumé")],
        },
        msg="$search should highlight a multi-byte token intact as a single hit span "
        "without offset corruption",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_HIGHLIGHT_TESTS))
def test_search_highlights(indexed_collection, test_case: StageTestCase):
    """Test $search projects searchHighlights spans tagging hits and context."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)


# Property [Highlight Sub-field Validation]: highlight requires a path, rejects a
# path of an unaccepted type (anything but a string, document, or array of paths),
# and rejects an unknown sub-field.
SEARCH_HIGHLIGHT_SUBFIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "highlight_missing_path",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "highlight": {}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a highlight document missing the required path",
    ),
    *[
        StageTestCase(
            f"highlight_path_{tid}",
            pipeline=[
                {
                    "$search": {
                        "text": {"query": "quick", "path": "title"},
                        "highlight": {"path": val},
                    }
                },
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search should reject a {tid} highlight.path as neither a string, document, "
            "nor array",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("objectid", ObjectId("0123456789abcdef01234567")),
            ("datetime", datetime.datetime(2020, 1, 1)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
        ]
    ],
    StageTestCase(
        "highlight_unknown_subfield",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "highlight": {"path": "title", "bogus": 1},
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an unknown highlight sub-field",
    ),
]

# Property [Highlight Integer Bounds]: highlight.maxCharsToExamine and
# highlight.maxNumPassages must each be positive - a tighter bound than the
# non-negative phrase.slop, which accepts zero.
SEARCH_HIGHLIGHT_INTEGER_BOUNDS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"highlight_{opt_id}_{tid}",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "highlight": {"path": "title", opt: val},
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search should reject a {tid} highlight.{opt} as non-positive",
    )
    for opt, opt_id in [
        ("maxCharsToExamine", "max_chars"),
        ("maxNumPassages", "max_passages"),
    ]
    for tid, val in [("zero", 0), ("negative", -1)]
]

SEARCH_HIGHLIGHT_ERROR_TESTS = (
    SEARCH_HIGHLIGHT_SUBFIELD_ERROR_TESTS + SEARCH_HIGHLIGHT_INTEGER_BOUNDS_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_HIGHLIGHT_ERROR_TESTS))
def test_search_highlight_errors(indexed_collection, test_case: StageTestCase):
    """Test $search highlight subfield and integer-bounds validation errors."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
