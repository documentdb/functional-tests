"""Tests for collation effects on $top, $bottom, $topN, $bottomN, $minN, $maxN accumulators."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [$top Accumulator Collation]: $top uses command-level collation for
# its sortBy comparison, returning the document with the smallest value under
# collation ordering.
COLLATION_TOP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "top_sortby_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file10"},
            {"_id": 2, "x": "file2"},
            {"_id": 3, "x": "file1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$top": {"sortBy": {"x": 1}, "output": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "result": "file1"}],
        msg="$top sortBy should use collation numericOrdering",
    ),
    CommandTestCase(
        "top_sortby_case_insensitive",
        docs=[
            {"_id": 1, "x": "Banana"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$top": {"sortBy": {"x": 1}, "output": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": None, "result": "apple"}],
        msg="$top sortBy should use collation for case-insensitive ordering",
    ),
]

# Property [$bottom Accumulator Collation]: $bottom uses command-level collation
# for its sortBy comparison, returning the document with the largest value under
# collation ordering.
COLLATION_BOTTOM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bottom_sortby_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file10"},
            {"_id": 2, "x": "file2"},
            {"_id": 3, "x": "file1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$bottom": {"sortBy": {"x": 1}, "output": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "result": "file10"}],
        msg="$bottom sortBy should use collation numericOrdering",
    ),
    CommandTestCase(
        "bottom_sortby_case_insensitive",
        docs=[
            {"_id": 1, "x": "Banana"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$bottom": {"sortBy": {"x": 1}, "output": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": None, "result": "cherry"}],
        msg="$bottom sortBy should use collation for case-insensitive ordering",
    ),
]

# Property [$topN Accumulator Collation]: $topN uses command-level collation for
# its sortBy comparison, returning the N documents with the smallest values
# under collation ordering.
COLLATION_TOPN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "topn_sortby_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file10"},
            {"_id": 2, "x": "file2"},
            {"_id": 3, "x": "file1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {
                            "$topN": {"n": 2, "sortBy": {"x": 1}, "output": "$x"},
                        },
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "result": ["file1", "file2"]}],
        msg="$topN sortBy should use collation numericOrdering",
    ),
    CommandTestCase(
        "topn_sortby_case_insensitive",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "B"},
            {"_id": 3, "x": "c"},
            {"_id": 4, "x": "D"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {
                            "$topN": {"n": 2, "sortBy": {"x": 1}, "output": "$x"},
                        },
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "result": ["a", "B"]}],
        msg="$topN sortBy with strength 1 should use linguistic ordering",
    ),
]

# Property [$bottomN Accumulator Collation]: $bottomN uses command-level
# collation for its sortBy comparison, returning the N documents with the
# largest values under collation ordering.
COLLATION_BOTTOMN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bottomn_sortby_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file10"},
            {"_id": 2, "x": "file2"},
            {"_id": 3, "x": "file1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {
                            "$bottomN": {"n": 2, "sortBy": {"x": 1}, "output": "$x"},
                        },
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "result": ["file2", "file10"]}],
        msg="$bottomN sortBy should use collation numericOrdering",
    ),
    CommandTestCase(
        "bottomn_sortby_case_insensitive",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "B"},
            {"_id": 3, "x": "c"},
            {"_id": 4, "x": "D"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {
                            "$bottomN": {"n": 2, "sortBy": {"x": 1}, "output": "$x"},
                        },
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": None, "result": ["c", "D"]}],
        msg="$bottomN sortBy with strength 1 should use linguistic ordering",
    ),
]

# Property [$minN Accumulator Collation]: $minN uses command-level collation for
# string comparisons, returning the N smallest values under collation ordering.
COLLATION_MINN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "minn_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file10"},
            {"_id": 2, "x": "file2"},
            {"_id": 3, "x": "file1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$minN": {"n": 2, "input": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "result": ["file1", "file2"]}],
        msg="$minN should use collation numericOrdering for string comparison",
    ),
    CommandTestCase(
        "minn_case_insensitive",
        docs=[
            {"_id": 1, "x": "Cherry"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "Banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$minN": {"n": 2, "input": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": None, "result": ["apple", "Banana"]}],
        msg="$minN should use collation for case-insensitive ordering",
    ),
]

# Property [$maxN Accumulator Collation]: $maxN uses command-level collation for
# string comparisons, returning the N largest values under collation ordering.
COLLATION_MAXN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxn_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file10"},
            {"_id": 2, "x": "file2"},
            {"_id": 3, "x": "file1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$maxN": {"n": 2, "input": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[{"_id": None, "result": ["file10", "file2"]}],
        msg="$maxN should use collation numericOrdering for string comparison",
    ),
    CommandTestCase(
        "maxn_case_insensitive",
        docs=[
            {"_id": 1, "x": "Cherry"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "Banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "result": {"$maxN": {"n": 2, "input": "$x"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": None, "result": ["Cherry", "Banana"]}],
        msg="$maxN should use collation for case-insensitive ordering",
    ),
]

COLLATION_AGGREGATE_ACCUMULATOR_TESTS: list[CommandTestCase] = (
    COLLATION_TOP_TESTS
    + COLLATION_BOTTOM_TESTS
    + COLLATION_TOPN_TESTS
    + COLLATION_BOTTOMN_TESTS
    + COLLATION_MINN_TESTS
    + COLLATION_MAXN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_ACCUMULATOR_TESTS))
def test_collation_aggregate_accumulators(database_client, collection, test):
    """Test collation effects on $top, $bottom, $topN, $bottomN, $minN, $maxN."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
