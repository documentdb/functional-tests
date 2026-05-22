"""Tests for caseFirst sort ordering and null acceptance in collation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [caseFirst Sort Ordering]: caseFirst "upper" sorts uppercase before
# lowercase within the same base character, "lower" sorts lowercase first, and
# "off" behaves identically to "lower"; caseFirst affects comparison operators
# but does NOT affect equality matching.
COLLATION_CASEFIRST_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "casefirst_upper_sort",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[
            {"_id": 2, "x": "A"},
            {"_id": 1, "x": "a"},
            {"_id": 4, "x": "B"},
            {"_id": 3, "x": "b"},
        ],
        msg="caseFirst upper should sort uppercase before lowercase",
    ),
    CommandTestCase(
        "casefirst_lower_sort",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "lower"},
        },
        expected=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        msg="caseFirst lower should sort lowercase before uppercase",
    ),
    CommandTestCase(
        "casefirst_off_sort",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "off"},
        },
        expected=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        msg="caseFirst off should behave identically to lower",
    ),
    CommandTestCase(
        "casefirst_upper_gt_comparison",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$gt": "A"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[
            {"_id": 1, "x": "a"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        msg="caseFirst upper should affect $gt so that a > A",
    ),
    CommandTestCase(
        "casefirst_upper_lt_comparison",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$lt": "a"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[{"_id": 2, "x": "A"}],
        msg="caseFirst upper should affect $lt so that A < a",
    ),
    CommandTestCase(
        "casefirst_lower_gt_comparison",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$gt": "A"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "lower"},
        },
        expected=[{"_id": 3, "x": "b"}, {"_id": 4, "x": "B"}],
        msg="caseFirst lower should affect $gt so that only b/B > A",
    ),
    CommandTestCase(
        "casefirst_upper_eq_not_affected",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="caseFirst upper should not affect $eq matching",
    ),
    CommandTestCase(
        "casefirst_upper_ne_not_affected",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$ne": "a"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[{"_id": 2, "x": "A"}, {"_id": 3, "x": "b"}],
        msg="caseFirst upper should not affect $ne matching",
    ),
    CommandTestCase(
        "casefirst_upper_in_not_affected",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$in": ["a"]}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="caseFirst upper should not affect $in matching",
    ),
    CommandTestCase(
        "casefirst_upper_gte_comparison",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$gte": "a"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[
            {"_id": 1, "x": "a"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        msg="caseFirst upper should affect $gte so that a >= a but A < a",
    ),
    CommandTestCase(
        "casefirst_upper_lte_comparison",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$lte": "A"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[{"_id": 2, "x": "A"}],
        msg="caseFirst upper should affect $lte so that only A <= A",
    ),
    CommandTestCase(
        "casefirst_upper_cmp_comparison",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"x": 1, "cmp": {"$cmp": ["$x", "A"]}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[
            {"_id": 1, "x": "a", "cmp": 1},
            {"_id": 2, "x": "A", "cmp": 0},
            {"_id": 3, "x": "b", "cmp": 1},
            {"_id": 4, "x": "B", "cmp": 1},
        ],
        msg="caseFirst upper should affect $cmp so that a > A",
    ),
]

# Property [caseFirst Null Acceptance]: null for caseFirst is treated as
# omitted, using the default value of "off".
COLLATION_CASEFIRST_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "casefirst_null_uses_default_off",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "caseFirst": None},
        },
        expected=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        msg="aggregate should treat null caseFirst as omitted (default off)",
    ),
]

COLLATION_CASEFIRST_TESTS: list[CommandTestCase] = (
    COLLATION_CASEFIRST_SORT_TESTS + COLLATION_CASEFIRST_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_CASEFIRST_TESTS))
def test_collation_casefirst(database_client, collection, test):
    """Test caseFirst collation option for upper/lower ordering."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
