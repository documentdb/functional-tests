"""Tests for partial index error cases — invalid creation, constraint violations, rejections."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    EXPR_IN_ARRAY_FILTERS_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
    INVALID_OPTIONS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

PARTIAL_INVALID_OPERATORS: list[IndexTestCase] = [
    IndexTestCase(
        id="ne",
        indexes=(
            {"key": {"a": 1}, "name": "idx_ne", "partialFilterExpression": {"a": {"$ne": 5}}},
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $ne in partialFilterExpression",
    ),
    IndexTestCase(
        id="nin",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_nin",
                "partialFilterExpression": {"a": {"$nin": [1, 2]}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $nin in partialFilterExpression",
    ),
    IndexTestCase(
        id="not",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_not",
                "partialFilterExpression": {"a": {"$not": {"$gt": 5}}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $not in partialFilterExpression",
    ),
    IndexTestCase(
        id="nor",
        indexes=(
            {"key": {"a": 1}, "name": "idx_nor", "partialFilterExpression": {"$nor": [{"a": 1}]}},
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $nor in partialFilterExpression",
    ),
    IndexTestCase(
        id="regex",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_regex",
                "partialFilterExpression": {"a": {"$regex": "^test"}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $regex in partialFilterExpression",
    ),
    IndexTestCase(
        id="expr",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_expr",
                "partialFilterExpression": {"$expr": {"$gt": ["$a", 5]}},
            },
        ),
        error_code=EXPR_IN_ARRAY_FILTERS_ERROR,
        msg="Should reject $expr in partialFilterExpression",
    ),
    IndexTestCase(
        id="where",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_where",
                "partialFilterExpression": {"$where": "this.a > 5"},
            },
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $where in partialFilterExpression",
    ),
    IndexTestCase(
        id="elemMatch",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_elem",
                "partialFilterExpression": {"arr": {"$elemMatch": {"x": 1}}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $elemMatch in partialFilterExpression",
    ),
    IndexTestCase(
        id="size",
        indexes=(
            {"key": {"a": 1}, "name": "idx_size", "partialFilterExpression": {"a": {"$size": 3}}},
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $size in partialFilterExpression",
    ),
    IndexTestCase(
        id="mod",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_mod",
                "partialFilterExpression": {"a": {"$mod": [2, 0]}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $mod in partialFilterExpression",
    ),
    IndexTestCase(
        id="text",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_text",
                "partialFilterExpression": {"$text": {"$search": "hello"}},
            },
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $text in partialFilterExpression",
    ),
    IndexTestCase(
        id="exists_false",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_exists_false",
                "partialFilterExpression": {"a": {"$exists": False}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $exists: false in partialFilterExpression",
    ),
    IndexTestCase(
        id="exists_zero",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_exists_zero",
                "partialFilterExpression": {"a": {"$exists": 0}},
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject $exists: 0 (falsy int) in partialFilterExpression",
    ),
    IndexTestCase(
        id="empty_and",
        indexes=(
            {"key": {"a": 1}, "name": "idx_empty_and", "partialFilterExpression": {"$and": []}},
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty $and in partialFilterExpression",
    ),
    IndexTestCase(
        id="empty_or",
        indexes=(
            {"key": {"a": 1}, "name": "idx_empty_or", "partialFilterExpression": {"$or": []}},
        ),
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty $or in partialFilterExpression",
    ),
    IndexTestCase(
        id="sparse_combination",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_partial_sparse",
                "partialFilterExpression": {"a": {"$gt": 0}},
                "sparse": True,
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject sparse combined with partialFilterExpression",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PARTIAL_INVALID_OPERATORS))
def test_partial_errors(collection, test):
    """Test partial index error cases — invalid creation."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


PARTIAL_TIMESERIES_ERRORS: list[IndexTestCase] = [
    IndexTestCase(
        id="ttl_data_field_filter",
        indexes=(
            {
                "key": {"ts": 1},
                "name": "idx_ttl_data",
                "expireAfterSeconds": 3600,
                "partialFilterExpression": {"value": {"$gt": 0}},
            },
        ),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject TTL partial index with filter on data field in timeseries",
    ),
    IndexTestCase(
        id="collation_conflict",
        indexes=(
            {
                "key": {"meta.name": 1},
                "name": "idx_collation_partial",
                "partialFilterExpression": {"meta.active": True},
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Should reject collation + partialFilterExpression on timeseries",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PARTIAL_TIMESERIES_ERRORS))
def test_partial_timeseries_errors(database_client, collection, test):
    """Test partial index error cases on timeseries collections."""
    ts_name = f"{collection.name}_ts"
    database_client.command(
        {"create": ts_name, "timeseries": {"timeField": "ts", "metaField": "meta"}}
    )
    ts_coll = database_client[ts_name]
    result = execute_command(
        ts_coll,
        {"createIndexes": ts_coll.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_partial_create_on_view_error(database_client, collection):
    """Test createIndex with partialFilterExpression on view returns error."""
    view_name = f"{collection.name}_view"
    database_client.create_collection(collection.name)
    database_client.command({"create": view_name, "viewOn": collection.name, "pipeline": []})
    view_coll = database_client[view_name]
    result = execute_command(
        view_coll,
        {
            "createIndexes": view_coll.name,
            "indexes": [
                {
                    "key": {"a": 1},
                    "name": "idx_partial",
                    "partialFilterExpression": {"a": {"$gt": 0}},
                }
            ],
        },
    )
    assertFailureCode(result, COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR)
