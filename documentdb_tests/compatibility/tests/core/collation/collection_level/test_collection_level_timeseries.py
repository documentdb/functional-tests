"""Tests for collation behavior with timeseries collections."""

from __future__ import annotations

import datetime
from datetime import timezone

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Timeseries Collection Collation]: a timeseries collection can be
# created with a default collation, and collation affects filter matching on
# the metaField.
COLLATION_TIMESERIES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeseries_default_collation_filter",
        target_collection=CustomCollection(
            options={
                "timeseries": {"timeField": "ts", "metaField": "meta"},
                "collation": {"locale": "en", "strength": 2},
            }
        ),
        docs=[
            {
                "_id": 1,
                "ts": datetime.datetime(2024, 1, 1, tzinfo=timezone.utc),
                "meta": "apple",
                "v": 1,
            },
            {
                "_id": 2,
                "ts": datetime.datetime(2024, 1, 2, tzinfo=timezone.utc),
                "meta": "Apple",
                "v": 2,
            },
            {
                "_id": 3,
                "ts": datetime.datetime(2024, 1, 3, tzinfo=timezone.utc),
                "meta": "banana",
                "v": 3,
            },
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"meta": "apple"},
            "sort": {"_id": 1},
        },
        expected=[
            {
                "_id": 1,
                "ts": datetime.datetime(2024, 1, 1, tzinfo=timezone.utc),
                "meta": "apple",
                "v": 1,
            },
            {
                "_id": 2,
                "ts": datetime.datetime(2024, 1, 2, tzinfo=timezone.utc),
                "meta": "Apple",
                "v": 2,
            },
        ],
        msg="timeseries collection with default collation should use it for filter matching",
    ),
    CommandTestCase(
        "timeseries_explicit_collation_filter",
        target_collection=CustomCollection(
            options={"timeseries": {"timeField": "ts", "metaField": "meta"}}
        ),
        docs=[
            {
                "_id": 1,
                "ts": datetime.datetime(2024, 1, 1, tzinfo=timezone.utc),
                "meta": "apple",
                "v": 1,
            },
            {
                "_id": 2,
                "ts": datetime.datetime(2024, 1, 2, tzinfo=timezone.utc),
                "meta": "Apple",
                "v": 2,
            },
            {
                "_id": 3,
                "ts": datetime.datetime(2024, 1, 3, tzinfo=timezone.utc),
                "meta": "banana",
                "v": 3,
            },
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"meta": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {
                "_id": 1,
                "ts": datetime.datetime(2024, 1, 1, tzinfo=timezone.utc),
                "meta": "apple",
                "v": 1,
            },
            {
                "_id": 2,
                "ts": datetime.datetime(2024, 1, 2, tzinfo=timezone.utc),
                "meta": "Apple",
                "v": 2,
            },
        ],
        msg="timeseries collection should support explicit collation on find",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_TIMESERIES_TESTS))
def test_collation_timeseries(database_client, collection, test):
    """Test collation behavior with timeseries collections."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = test.build_expected(ctx)
    assertResult(
        result,
        expected=expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(expected, list),
    )
