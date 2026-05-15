"""Tests for partial index on timeseries collections."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


PARTIAL_TIMESERIES_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="metric_field_gt",
        indexes=(
            {
                "key": {"value": 1},
                "name": "idx_metric_gt",
                "partialFilterExpression": {"value": {"$gt": 10}},
            },
        ),
        expected={"ok": 1.0, "numIndexesAfter": 2},
        msg="Partial index with comparison operator on metric field",
    ),
    IndexTestCase(
        id="ttl_meta_filter",
        indexes=(
            {
                "key": {"ts": 1},
                "name": "idx_ttl_meta",
                "expireAfterSeconds": 3600,
                "partialFilterExpression": {"meta.active": True},
            },
        ),
        expected={"ok": 1.0, "numIndexesAfter": 2},
        msg="TTL index with partialFilterExpression on metaField succeeds",
    ),
    IndexTestCase(
        id="time_field_gt",
        indexes=(
            {
                "key": {"ts": 1},
                "name": "idx_time_gt",
                "partialFilterExpression": {
                    "ts": {"$gt": datetime(2024, 1, 1, tzinfo=timezone.utc)}
                },
            },
        ),
        expected={"ok": 1.0, "numIndexesAfter": 2},
        msg="Partial index with $gt on time field created successfully",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PARTIAL_TIMESERIES_TESTS))
def test_partial_timeseries(database_client, collection, test):
    """Test partial index creation on timeseries collections."""
    ts_name = f"{collection.name}_ts"
    database_client.command(
        {"create": ts_name, "timeseries": {"timeField": "ts", "metaField": "meta"}}
    )
    ts_coll = database_client[ts_name]
    result = execute_command(
        ts_coll,
        {"createIndexes": ts_coll.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)
