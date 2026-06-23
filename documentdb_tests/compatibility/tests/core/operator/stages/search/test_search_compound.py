"""Tests for the $search compound operator."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SEARCH_EXECUTOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Compound Clause Composition]: the must, should, mustNot, and filter
# clauses compose into one clause set, so the matched documents are the must/filter
# intersection minus the mustNot matches, with should only optional.
SEARCH_COMPOUND_COMPOSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_must_intersects",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [
                            {"text": {"query": "quick", "path": "title"}},
                            {"text": {"query": "rabbit", "path": "title"}},
                        ]
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 3)]},
        msg="$search compound should intersect multiple must clauses, matching only the "
        "document satisfying every clause",
    ),
    StageTestCase(
        "compound_must_not_excludes",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [{"text": {"query": "quick", "path": "title"}}],
                        "mustNot": [{"text": {"query": "rabbit", "path": "title"}}],
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 4)]},
        msg="$search compound should exclude the mustNot matches from the must matches",
    ),
    StageTestCase(
        "compound_filter_selects",
        pipeline=[
            {"$search": {"compound": {"filter": [{"text": {"query": "quick", "path": "title"}}]}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search compound should select the documents matching a filter clause",
    ),
    StageTestCase(
        "compound_all_clause_types",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [{"text": {"query": "quick", "path": "title"}}],
                        "should": [{"text": {"query": "brown", "path": "title"}}],
                        "mustNot": [{"text": {"query": "rabbit", "path": "title"}}],
                        "filter": [{"text": {"query": "fox", "path": "title"}}],
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search compound should compose all four clause types in one clause set, "
        "intersecting must and filter and removing the mustNot matches",
    ),
]

# Property [Compound Should-Only Matching]: when a compound has no must or filter
# clause, the should clauses become a required OR (minimumShouldMatch defaults to 1),
# so the matched set is the union of the should clauses.
SEARCH_COMPOUND_SHOULD_ONLY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_should_optional_or",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "should": [
                            {"text": {"query": "quick", "path": "title"}},
                            {"text": {"query": "turtle", "path": "title"}},
                        ]
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
        msg="$search compound should match the union of its should clauses when no must "
        "clause is present",
    ),
]

# Property [Compound minimumShouldMatch]: minimumShouldMatch accepts 0 through the
# number of should clauses and requires at least that many should clauses to match
# alongside the must clause.
SEARCH_COMPOUND_MIN_SHOULD_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_min_should_match_0",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [{"text": {"query": "quick", "path": "title"}}],
                        "should": [
                            {"text": {"query": "brown", "path": "title"}},
                            {"text": {"query": "rabbit", "path": "title"}},
                        ],
                        "minimumShouldMatch": 0,
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
        msg="$search compound with minimumShouldMatch 0 should require no should clause, "
        "matching every must document",
    ),
    StageTestCase(
        "compound_min_should_match_1",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [{"text": {"query": "quick", "path": "title"}}],
                        "should": [
                            {"text": {"query": "brown", "path": "title"}},
                            {"text": {"query": "rabbit", "path": "title"}},
                        ],
                        "minimumShouldMatch": 1,
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 3)]},
        msg="$search compound with minimumShouldMatch 1 should require at least one should "
        "clause to match alongside the must clause",
    ),
    StageTestCase(
        "compound_min_should_match_all",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [{"text": {"query": "quick", "path": "title"}}],
                        "should": [
                            {"text": {"query": "brown", "path": "title"}},
                            {"text": {"query": "rabbit", "path": "title"}},
                        ],
                        "minimumShouldMatch": 2,
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search compound with minimumShouldMatch equal to the should-clause count should "
        "require every should clause to match",
    ),
]

# Property [Compound Score And Nesting]: a clause-level score boost, a
# compound-level score, and a compound nested at least three levels deep all
# execute and return the matched documents.
SEARCH_COMPOUND_SCORE_NESTING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_clause_level_score_boost",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [
                            {
                                "text": {
                                    "query": "quick",
                                    "path": "title",
                                    "score": {"boost": {"value": 2.0}},
                                }
                            }
                        ]
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
        msg="$search compound should accept a clause-level score boost and still return the "
        "matches",
    ),
    StageTestCase(
        "compound_level_score",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [{"text": {"query": "quick", "path": "title"}}],
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
        msg="$search compound should accept a compound-level score and still return the matches",
    ),
    StageTestCase(
        "compound_nested_three_levels",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "must": [
                            {
                                "compound": {
                                    "must": [
                                        {
                                            "compound": {
                                                "must": [
                                                    {
                                                        "text": {
                                                            "query": "quick",
                                                            "path": "title",
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
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
        msg="$search compound should execute a compound nested at least three levels deep",
    ),
]

# Property [Compound Single-Document Clause]: a compound clause accepts a single
# operator document in place of a one-element array, matching identically to the
# array-wrapped form.
SEARCH_COMPOUND_SINGLE_DOC_CLAUSE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_single_doc_must",
        pipeline=[
            {"$search": {"compound": {"must": {"text": {"query": "quick", "path": "title"}}}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search compound should accept a single operator document as a must clause, "
        "matching identically to the array-wrapped form",
    ),
]

SEARCH_COMPOUND_TESTS = (
    SEARCH_COMPOUND_COMPOSITION_TESTS
    + SEARCH_COMPOUND_SHOULD_ONLY_TESTS
    + SEARCH_COMPOUND_MIN_SHOULD_MATCH_TESTS
    + SEARCH_COMPOUND_SCORE_NESTING_TESTS
    + SEARCH_COMPOUND_SINGLE_DOC_CLAUSE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_COMPOUND_TESTS))
def test_search_compound_cases(indexed_collection, test_case: StageTestCase):
    """Test $search compound clause composition, should-only, minimumShouldMatch, scoring."""
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


# Property [Compound minimumShouldMatch Bounds]: compound.minimumShouldMatch must
# be between 0 and the number of should clauses, so a negative value or one
# greater than the should-clause count is rejected.
SEARCH_COMPOUND_MIN_SHOULD_MATCH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "min_should_match_negative",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "should": [{"text": {"query": "quick", "path": "title"}}],
                        "minimumShouldMatch": -1,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject a negative compound.minimumShouldMatch",
    ),
    StageTestCase(
        "min_should_match_over_clause_count",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "should": [{"text": {"query": "quick", "path": "title"}}],
                        "minimumShouldMatch": 2,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject a compound.minimumShouldMatch greater than the should-clause "
        "count",
    ),
]

# Property [Compound minimumShouldMatch Type]: compound.minimumShouldMatch must
# be an integer, so a non-integer type is rejected and null is treated as the default.
SEARCH_COMPOUND_MIN_SHOULD_MATCH_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"min_should_match_type_{tid}",
        pipeline=[
            {
                "$search": {
                    "compound": {
                        "should": [{"text": {"query": "quick", "path": "title"}}],
                        "minimumShouldMatch": val,
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg=f"$search should reject a {tid} compound.minimumShouldMatch as a non-integer",
    )
    for tid, val in [
        ("string", "1"),
        ("double", 1.5),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", [1]),
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
]

# Property [Compound Requires A Clause]: a compound with none of the four clause
# types present is rejected as it composes no clauses.
SEARCH_COMPOUND_EMPTY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_empty",
        pipeline=[{"$search": {"compound": {}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject an empty compound with no clause type present",
    ),
]

# Property [Compound Clause Array Non-Empty]: a present compound clause array must
# contain at least one clause, so an empty array in any clause slot is rejected.
SEARCH_COMPOUND_EMPTY_CLAUSE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_empty_must",
        pipeline=[{"$search": {"compound": {"must": []}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject an empty compound must clause array",
    ),
]

SEARCH_COMPOUND_ERROR_TESTS = (
    SEARCH_COMPOUND_MIN_SHOULD_MATCH_ERROR_TESTS
    + SEARCH_COMPOUND_MIN_SHOULD_MATCH_TYPE_ERROR_TESTS
    + SEARCH_COMPOUND_EMPTY_ERROR_TESTS
    + SEARCH_COMPOUND_EMPTY_CLAUSE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_COMPOUND_ERROR_TESTS))
def test_search_compound_errors(indexed_collection, test_case: StageTestCase):
    """Test $search compound minimumShouldMatch and empty-clause validation errors."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
