"""Tests for count command view support."""

from __future__ import annotations

import pytest
from bson import Decimal128
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    LIMIT_NOT_POSITIVE_ERROR,
    OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    OrphanedViewCollection,
    ViewChainCollection,
    ViewCollection,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
)

# Property [View Support]: count operates on views with the same semantics as
# on collections.
COUNT_VIEW_SUPPORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_basic_count",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 5, "ok": 1.0},
        msg="count should work on a simple view",
    ),
    CommandTestCase(
        "view_with_query",
        target_collection=ViewCollection(),
        docs=[{"_id": i, "x": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$gt": 2}}},
        expected={"n": 2, "ok": 1.0},
        msg="count on view should apply query filter after view pipeline",
    ),
    CommandTestCase(
        "view_pipeline_filters",
        target_collection=ViewCollection(
            options={"pipeline": [{"$match": {"status": "active"}}]},
            suffix="_vpipe",
        ),
        docs=[
            {"_id": 1, "status": "active"},
            {"_id": 2, "status": "active"},
            {"_id": 3, "status": "inactive"},
            {"_id": 4, "status": "active"},
        ],
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 3, "ok": 1.0},
        msg="count on view should apply the view pipeline",
    ),
    CommandTestCase(
        "view_pipeline_plus_query",
        target_collection=ViewCollection(
            options={"pipeline": [{"$match": {"status": "active"}}]},
            suffix="_vpipe",
        ),
        docs=[
            {"_id": 1, "x": 1, "status": "active"},
            {"_id": 2, "x": 5, "status": "active"},
            {"_id": 3, "x": 10, "status": "inactive"},
            {"_id": 4, "x": 8, "status": "active"},
        ],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$gt": 2}}},
        expected={"n": 2, "ok": 1.0},
        msg="count on view should apply query filter after view pipeline",
    ),
    CommandTestCase(
        "view_hint_underlying_index",
        target_collection=ViewCollection(),
        docs=[{"_id": i, "x": i} for i in range(5)],
        indexes=[IndexModel([("x", 1)], name="x_1")],
        command=lambda ctx: {"count": ctx.collection, "hint": "x_1"},
        expected={"n": 5, "ok": 1.0},
        msg="count hint on view should resolve against underlying collection indexes",
    ),
    CommandTestCase(
        "view_limit_positive",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": 3},
        expected={"n": 3, "ok": 1.0},
        msg="count with positive limit on view should cap the result",
    ),
    CommandTestCase(
        "view_limit_zero_int",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": 0},
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="count with limit=0 on view should produce an error",
    ),
    CommandTestCase(
        "view_limit_neg_zero_double",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": DOUBLE_NEGATIVE_ZERO},
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg="count with limit=-0.0 on view should produce an error",
    ),
    CommandTestCase(
        "view_limit_zero_decimal",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": DECIMAL128_ZERO},
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg='count with limit=Decimal128("0") on view should produce an error',
    ),
    CommandTestCase(
        "view_limit_neg_zero_decimal",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "limit": DECIMAL128_NEGATIVE_ZERO,
        },
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg='count with limit=Decimal128("-0") on view should produce an error',
    ),
    CommandTestCase(
        "view_limit_neg_zero_decimal_fractional",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": Decimal128("-0.0")},
        error_code=LIMIT_NOT_POSITIVE_ERROR,
        msg='count with limit=Decimal128("-0.0") on view should produce an error',
    ),
    CommandTestCase(
        "view_limit_negative",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": -3},
        expected={"n": 3, "ok": 1.0},
        msg="count with negative limit on view should use absolute value",
    ),
    CommandTestCase(
        "view_skip",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "skip": 2},
        expected={"n": 3, "ok": 1.0},
        msg="count skip on view should work identically to regular collections",
    ),
    CommandTestCase(
        "view_collation_override_different",
        target_collection=ViewCollection(
            options={"collation": {"locale": "en", "strength": 2}},
            suffix="_cv",
        ),
        docs=[{"_id": 1, "s": "abc"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "fr"},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="count with different collation on collated view should produce an error",
    ),
    CommandTestCase(
        "view_collation_on_uncollated_view",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "s": "abc"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en"},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="count with collation on view without default collation should produce an error",
    ),
    CommandTestCase(
        "view_collation_matching",
        target_collection=ViewCollection(
            options={"collation": {"locale": "en", "strength": 2}},
            suffix="_cv",
        ),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count with matching collation on collated view should succeed",
    ),
    CommandTestCase(
        "view_dropped_source",
        target_collection=OrphanedViewCollection(),
        docs=[{"_id": 1}, {"_id": 2}],
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 0, "ok": 1.0},
        msg="count on view with dropped source collection should return n=0",
    ),
    CommandTestCase(
        "view_nested",
        target_collection=ViewChainCollection(depth=2),
        docs=[{"_id": i} for i in range(3)],
        command=lambda ctx: {"count": ctx.collection},
        expected={"n": 3, "ok": 1.0},
        msg="count on nested view should apply all pipelines correctly",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COUNT_VIEW_SUPPORT_TESTS))
def test_count_views(database_client, collection, test):
    """Test count command view support."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
