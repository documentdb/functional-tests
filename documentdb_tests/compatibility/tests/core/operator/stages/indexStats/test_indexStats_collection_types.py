"""Tests for $indexStats collection type behavior."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.indexStats.utils.indexStats_test_case import (  # noqa: E501
    IndexStatsTestCase,
    prepare_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Collection Existence]: $indexStats handles non-existent, empty,
# and special collection types.
COLLECTION_TYPE_TESTS: list[IndexStatsTestCase] = [
    IndexStatsTestCase(
        id="nonexistent_collection",
        docs=None,
        pipeline=[{"$indexStats": {}}, {"$count": "n"}],
        expected=[],
        msg="Non-existent collection should return 0 documents",
    ),
    IndexStatsTestCase(
        id="empty_collection",
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="Empty collection should return 1 document for the _id index",
    ),
    IndexStatsTestCase(
        id="capped_collection",
        target_collection=CappedCollection(),
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "_id_"}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="Capped collection should report the _id index",
    ),
    IndexStatsTestCase(
        id="timeseries_collection",
        target_collection=TimeseriesCollection(),
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="Time series collection should report at least one index",
    ),
    IndexStatsTestCase(
        id="view_collection",
        target_collection=ViewCollection(),
        docs=[],
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "_id_"}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="View should report the underlying collection's _id index",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(COLLECTION_TYPE_TESTS))
def test_indexStats_collection_types(collection: Collection, test_case: IndexStatsTestCase):
    """Test $indexStats on various collection types."""
    coll = prepare_collection(collection, test_case)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
