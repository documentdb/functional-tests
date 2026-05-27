"""Tests for count command collection type acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    TimeseriesCollection,
    ViewCollection,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
)

_XFAIL_LIMIT_LEAK = pytest.mark.engine_xfail(
    engine="mongodb",
    reason="Server leaks $limit validation through count on views",
    raises=AssertionError,
)

# Property [Collection Type Acceptance]: count produces correct results
# regardless of the underlying collection type.
COUNT_COLLECTION_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "regular",
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": 1}},
        expected={"n": 2, "ok": 1.0},
        msg="count with query should work on a regular collection",
    ),
    CommandTestCase(
        "view",
        target_collection=ViewCollection(
            options={"pipeline": [{"$match": {"status": "active"}}]},
            suffix="_vpipe",
        ),
        docs=[
            {"_id": 1, "x": 1, "status": "active"},
            {"_id": 2, "x": 5, "status": "active"},
            {"_id": 3, "x": 10, "status": "inactive"},
            {"_id": 4, "x": 8, "status": "active"},
            {"_id": 5, "x": 12, "status": "active"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": {"$gt": 2}},
            "skip": 1,
            "limit": 2,
        },
        expected={"n": 2, "ok": 1.0},
        msg="count on view should apply pipeline, query, skip, and limit together",
    ),
    CommandTestCase(
        "capped",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": 1}},
        expected={"n": 2, "ok": 1.0},
        msg="count with query should work on a capped collection",
    ),
    CommandTestCase(
        "timeseries",
        target_collection=TimeseriesCollection(),
        docs=[
            {"ts": datetime(2024, 1, i, tzinfo=timezone.utc), "meta": "a", "x": i % 3}
            for i in range(1, 6)
        ],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": 1}},
        expected={"n": 2, "ok": 1.0},
        msg="count with query should work on a timeseries collection",
    ),
    CommandTestCase(
        "clustered",
        target_collection=ClusteredCollection(),
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": 1}},
        expected={"n": 2, "ok": 1.0},
        msg="count with query should work on a clustered collection",
    ),
]

# Property [View Limit Zero Consistency]: count with limit=0 on a view should
# behave identically to a normal collection, returning the full count.
COUNT_VIEW_LIMIT_ZERO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "zero_int",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": 0},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=0 on view should mean no limit",
        marks=(_XFAIL_LIMIT_LEAK,),
    ),
    CommandTestCase(
        "zero_double",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": DOUBLE_ZERO},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=0.0 on view should mean no limit",
        marks=(_XFAIL_LIMIT_LEAK,),
    ),
    CommandTestCase(
        "neg_zero_double",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": DOUBLE_NEGATIVE_ZERO},
        expected={"n": 5, "ok": 1.0},
        msg="count with limit=-0.0 on view should mean no limit",
        marks=(_XFAIL_LIMIT_LEAK,),
    ),
    CommandTestCase(
        "zero_decimal128",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": DECIMAL128_ZERO},
        expected={"n": 5, "ok": 1.0},
        msg='count with limit=Decimal128("0") on view should mean no limit',
        marks=(_XFAIL_LIMIT_LEAK,),
    ),
    CommandTestCase(
        "neg_zero_decimal128",
        target_collection=ViewCollection(),
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "limit": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"n": 5, "ok": 1.0},
        msg='count with limit=Decimal128("-0") on view should mean no limit',
        marks=(_XFAIL_LIMIT_LEAK,),
    ),
]

COUNT_ALL_COLLECTION_TYPE_TESTS: list[CommandTestCase] = (
    COUNT_COLLECTION_TYPE_TESTS + COUNT_VIEW_LIMIT_ZERO_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_ALL_COLLECTION_TYPE_TESTS))
def test_count_collection_types(database_client, collection, test):
    """Test count command collection type acceptance."""
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
