"""Tests for createIndexes restrictions on timeseries collections."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
    INVALID_OPTIONS_ERROR,
    WILDCARD_MULTIPLE_FIELDS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import TimeseriesCollection

pytestmark = pytest.mark.index


@pytest.fixture
def timeseries_coll(database_client, collection):
    """Create a timeseries collection for index tests."""
    return TimeseriesCollection(
        timeseries_options={"timeField": "time", "metaField": "meta"}
    ).resolve(database_client, collection)


# Property [Rejected Index Types]: text, unique, sparse, hashed, wildcard,
# and 2d indexes are not supported on timeseries collections.
TIMESERIES_INDEX_REJECTED_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        "text_rejected",
        indexes=({"key": {"v": "text"}, "name": "v_text"},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject text index on timeseries",
    ),
    IndexTestCase(
        "unique_rejected",
        indexes=({"key": {"v": 1}, "name": "v_uniq", "unique": True},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject unique index on timeseries",
    ),
    IndexTestCase(
        "sparse_rejected",
        indexes=({"key": {"v": 1}, "name": "v_sparse", "sparse": True},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject sparse index on timeseries",
    ),
    IndexTestCase(
        "hashed_rejected",
        indexes=({"key": {"v": "hashed"}, "name": "v_hashed"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject hashed index on timeseries",
    ),
    IndexTestCase(
        "2d_rejected",
        indexes=({"key": {"loc": "2d"}, "name": "loc_2d"},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject 2d index on timeseries",
    ),
    IndexTestCase(
        "wildcard_rejected",
        indexes=({"key": {"$**": 1}, "name": "wc"},),
        error_code=WILDCARD_MULTIPLE_FIELDS_ERROR,
        msg="Should reject wildcard index on timeseries",
    ),
    IndexTestCase(
        "ttl_without_partial_rejected",
        indexes=({"key": {"time": 1}, "name": "time_ttl", "expireAfterSeconds": 3600},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject TTL index without partialFilterExpression on timeseries",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TIMESERIES_INDEX_REJECTED_TESTS))
def test_createIndexes_timeseries_rejected(timeseries_coll, test):
    """Test createIndexes rejected index types on timeseries."""
    result = execute_command(
        timeseries_coll,
        {"createIndexes": timeseries_coll.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Accepted Index Types]: 2dsphere, partial filter, compound,
# descending, hidden, collation, and metaField-specific (sparse, 2d)
# indexes are supported on timeseries.
TIMESERIES_INDEX_ACCEPTED_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        "2dsphere_accepted",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2dsphere"},),
        msg="Should accept 2dsphere index on timeseries",
    ),
    IndexTestCase(
        "partial_filter_accepted",
        indexes=(
            {
                "key": {"v": 1},
                "name": "v_partial",
                "partialFilterExpression": {"v": {"$gt": 5}},
            },
        ),
        msg="Should accept partial filter index on timeseries",
    ),
    IndexTestCase(
        "compound_accepted",
        indexes=({"key": {"meta": 1, "v": 1}, "name": "compound"},),
        msg="Should accept compound index on timeseries",
    ),
    IndexTestCase(
        "descending_accepted",
        indexes=({"key": {"v": -1}, "name": "v_desc"},),
        msg="Should accept descending index on timeseries",
    ),
    IndexTestCase(
        "hidden_accepted",
        indexes=({"key": {"v": 1}, "name": "v_hidden", "hidden": True},),
        msg="Should accept hidden index on timeseries",
    ),
    IndexTestCase(
        "collation_accepted",
        indexes=({"key": {"v": 1}, "name": "v_coll", "collation": {"locale": "en"}},),
        msg="Should accept collation index on timeseries",
    ),
    IndexTestCase(
        "on_metafield_accepted",
        indexes=({"key": {"meta": 1}, "name": "meta_solo"},),
        msg="Should accept index on metaField on timeseries",
    ),
    IndexTestCase(
        "sparse_on_metafield_accepted",
        indexes=({"key": {"meta": 1}, "name": "meta_sparse", "sparse": True},),
        msg="Should accept sparse index on metaField on timeseries",
    ),
    IndexTestCase(
        "2d_on_metafield_accepted",
        indexes=({"key": {"meta": "2d"}, "name": "meta_2d"},),
        msg="Should accept 2d index on metaField on timeseries",
    ),
    IndexTestCase(
        "on_timefield_accepted",
        indexes=({"key": {"time": 1}, "name": "time_solo"},),
        msg="Should accept index on timeField on timeseries",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TIMESERIES_INDEX_ACCEPTED_TESTS))
def test_createIndexes_timeseries_accepted(timeseries_coll, test):
    """Test createIndexes accepted index types on timeseries."""
    result = execute_command(
        timeseries_coll,
        {"createIndexes": timeseries_coll.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, index_created_response(), msg=test.msg)
