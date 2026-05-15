"""Tests for partial index creation — valid operators, formats, type filters, and signatures."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

PARTIAL_VALID_OPERATORS: list[IndexTestCase] = [
    IndexTestCase(
        id="equality",
        indexes=(
            {"key": {"a": 1}, "name": "idx_eq", "partialFilterExpression": {"status": "active"}},
        ),
        msg="Should create partial index with equality filter",
    ),
    IndexTestCase(
        id="dollar_eq",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_deq",
                "partialFilterExpression": {"status": {"$eq": "active"}},
            },
        ),
        msg="Should create partial index with $eq filter",
    ),
    IndexTestCase(
        id="exists_true",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_exists",
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        msg="Should create partial index with $exists: true",
    ),
    IndexTestCase(
        id="gt",
        indexes=(
            {"key": {"a": 1}, "name": "idx_gt", "partialFilterExpression": {"a": {"$gt": 5}}},
        ),
        msg="Should create partial index with $gt",
    ),
    IndexTestCase(
        id="gte",
        indexes=(
            {"key": {"a": 1}, "name": "idx_gte", "partialFilterExpression": {"a": {"$gte": 5}}},
        ),
        msg="Should create partial index with $gte",
    ),
    IndexTestCase(
        id="lt",
        indexes=(
            {"key": {"a": 1}, "name": "idx_lt", "partialFilterExpression": {"a": {"$lt": 100}}},
        ),
        msg="Should create partial index with $lt",
    ),
    IndexTestCase(
        id="lte",
        indexes=(
            {"key": {"a": 1}, "name": "idx_lte", "partialFilterExpression": {"a": {"$lte": 100}}},
        ),
        msg="Should create partial index with $lte",
    ),
    IndexTestCase(
        id="type_operator",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_type",
                "partialFilterExpression": {"a": {"$type": "string"}},
            },
        ),
        msg="Should create partial index with $type",
    ),
    IndexTestCase(
        id="and",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_and",
                "partialFilterExpression": {"$and": [{"a": {"$gt": 0}}, {"a": {"$lt": 100}}]},
            },
        ),
        msg="Should create partial index with $and",
    ),
    IndexTestCase(
        id="or",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_or",
                "partialFilterExpression": {"$or": [{"a": {"$gt": 50}}, {"b": {"$exists": True}}]},
            },
        ),
        msg="Should create partial index with $or",
    ),
    IndexTestCase(
        id="in",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_in",
                "partialFilterExpression": {"status": {"$in": ["active", "pending"]}},
            },
        ),
        msg="Should create partial index with $in",
    ),
    IndexTestCase(
        id="nested_and_or",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_nested",
                "partialFilterExpression": {
                    "$and": [
                        {"$or": [{"a": {"$gt": 0}}, {"b": {"$exists": True}}]},
                        {"c": {"$lt": 10}},
                    ]
                },
            },
        ),
        msg="Should create partial index with nested $and/$or",
    ),
    IndexTestCase(
        id="all",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_all",
                "partialFilterExpression": {"a": {"$all": [1, 2]}},
            },
        ),
        msg="Should create partial index with $all",
    ),
    IndexTestCase(
        id="geoWithin",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_geo_within",
                "partialFilterExpression": {"loc": {"$geoWithin": {"$center": [[0, 0], 5]}}},
            },
        ),
        msg="Should create partial index with $geoWithin",
    ),
    IndexTestCase(
        id="geoIntersects",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_geo_intersects",
                "partialFilterExpression": {
                    "loc": {
                        "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}
                    }
                },
            },
        ),
        msg="Should create partial index with $geoIntersects",
    ),
    IndexTestCase(
        id="eq_null",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_eq_null",
                "partialFilterExpression": {"a": {"$eq": None}},
            },
        ),
        msg="Should create partial index with $eq null",
    ),
    IndexTestCase(
        id="filter_on_id_field",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_id_filter",
                "partialFilterExpression": {"_id": {"$gt": 0}},
            },
        ),
        msg="Should create partial index with filter on _id field",
    ),
]

PARTIAL_FORMAT_VARIATIONS: list[IndexTestCase] = [
    IndexTestCase(
        id="empty_filter",
        indexes=({"key": {"a": 1}, "name": "idx_empty", "partialFilterExpression": {}},),
        msg="Should create partial index with empty partialFilterExpression",
    ),
    IndexTestCase(
        id="filter_on_same_field",
        indexes=(
            {"key": {"a": 1}, "name": "idx_same", "partialFilterExpression": {"a": {"$gt": 0}}},
        ),
        msg="Should create partial index with filter on same field as key",
    ),
    IndexTestCase(
        id="filter_different_field",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_diff",
                "partialFilterExpression": {"b": {"$exists": True}},
            },
        ),
        msg="Should create partial index with filter on different field",
    ),
    IndexTestCase(
        id="filter_multiple_fields",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_multi",
                "partialFilterExpression": {"b": {"$gt": 0}, "c": {"$exists": True}},
            },
        ),
        msg="Should create partial index with filter on multiple fields",
    ),
    IndexTestCase(
        id="with_unique",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_uniq",
                "partialFilterExpression": {"a": {"$gt": 0}},
                "unique": True,
            },
        ),
        msg="Should create partial index combined with unique",
    ),
    IndexTestCase(
        id="compound_index",
        indexes=(
            {
                "key": {"a": 1, "b": -1},
                "name": "idx_comp",
                "partialFilterExpression": {"a": {"$gt": 0}},
            },
        ),
        msg="Should create partial index on compound key",
    ),
    IndexTestCase(
        id="hashed_index",
        indexes=(
            {
                "key": {"a": "hashed"},
                "name": "idx_hash",
                "partialFilterExpression": {"b": {"$gt": 0}},
            },
        ),
        msg="Should create partial index on hashed key",
    ),
    IndexTestCase(
        id="2dsphere_index",
        indexes=(
            {
                "key": {"loc": "2dsphere"},
                "name": "idx_2ds",
                "partialFilterExpression": {"active": True},
            },
        ),
        msg="Should create partial index on 2dsphere key",
    ),
    IndexTestCase(
        id="wildcard_index",
        indexes=(
            {
                "key": {"$**": 1},
                "name": "idx_wc",
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        msg="Should create partial index on wildcard key",
    ),
]

PARTIAL_TYPE_FILTER_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="type_double",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_double",
                "partialFilterExpression": {"a": {"$type": "double"}},
            },
        ),
        msg="Should create partial index with $type double",
    ),
    IndexTestCase(
        id="type_string",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_string",
                "partialFilterExpression": {"a": {"$type": "string"}},
            },
        ),
        msg="Should create partial index with $type string",
    ),
    IndexTestCase(
        id="type_object",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_object",
                "partialFilterExpression": {"a": {"$type": "object"}},
            },
        ),
        msg="Should create partial index with $type object",
    ),
    IndexTestCase(
        id="type_array",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_array",
                "partialFilterExpression": {"a": {"$type": "array"}},
            },
        ),
        msg="Should create partial index with $type array",
    ),
    IndexTestCase(
        id="type_bool",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_bool",
                "partialFilterExpression": {"a": {"$type": "bool"}},
            },
        ),
        msg="Should create partial index with $type bool",
    ),
    IndexTestCase(
        id="type_date",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_date",
                "partialFilterExpression": {"a": {"$type": "date"}},
            },
        ),
        msg="Should create partial index with $type date",
    ),
    IndexTestCase(
        id="type_null",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_null",
                "partialFilterExpression": {"a": {"$type": "null"}},
            },
        ),
        msg="Should create partial index with $type null",
    ),
    IndexTestCase(
        id="type_int",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_int",
                "partialFilterExpression": {"a": {"$type": "int"}},
            },
        ),
        msg="Should create partial index with $type int",
    ),
    IndexTestCase(
        id="type_long",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_long",
                "partialFilterExpression": {"a": {"$type": "long"}},
            },
        ),
        msg="Should create partial index with $type long",
    ),
    IndexTestCase(
        id="type_decimal",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_decimal",
                "partialFilterExpression": {"a": {"$type": "decimal"}},
            },
        ),
        msg="Should create partial index with $type decimal",
    ),
    IndexTestCase(
        id="type_number",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_number",
                "partialFilterExpression": {"a": {"$type": "number"}},
            },
        ),
        msg="Should create partial index with $type number (alias)",
    ),
    IndexTestCase(
        id="type_multiple",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_multi",
                "partialFilterExpression": {"a": {"$type": ["string", "int"]}},
            },
        ),
        msg="Should create partial index with $type array of multiple types",
    ),
    IndexTestCase(
        id="type_numeric_code",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_t_numeric",
                "partialFilterExpression": {"a": {"$type": 2}},
            },
        ),
        msg="Should create partial index with $type numeric code (2 = string)",
    ),
]

PARTIAL_COLLECTION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="on_nonexistent_collection",
        indexes=(
            {"key": {"a": 1}, "name": "idx_partial", "partialFilterExpression": {"a": {"$gt": 0}}},
        ),
        expected={"ok": 1.0, "createdCollectionAutomatically": True, "numIndexesAfter": 2},
        msg="Should implicitly create collection with partial index",
    ),
]

PARTIAL_CREATE_TESTS = (
    PARTIAL_VALID_OPERATORS
    + PARTIAL_FORMAT_VARIATIONS
    + PARTIAL_TYPE_FILTER_TESTS
    + PARTIAL_COLLECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PARTIAL_CREATE_TESTS))
def test_partial_create(collection, test):
    """Test createIndex with valid partialFilterExpression succeeds."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    expected = test.expected if test.expected is not None else index_created_response()
    assertSuccessPartial(result, expected, msg=test.msg)


PARTIAL_SIGNATURE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="different_filter_creates_separate",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_partial_gt5",
                "partialFilterExpression": {"a": {"$gt": 5}},
            },
        ),
        setup_indexes=[
            {
                "key": {"a": 1},
                "name": "idx_partial_gt10",
                "partialFilterExpression": {"a": {"$gt": 10}},
            }
        ],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=3),
        msg="Different partialFilterExpression on same key creates separate index",
    ),
    IndexTestCase(
        id="same_filter_noop",
        indexes=(
            {"key": {"a": 1}, "name": "idx_partial", "partialFilterExpression": {"a": {"$gt": 5}}},
        ),
        setup_indexes=[
            {"key": {"a": 1}, "name": "idx_partial", "partialFilterExpression": {"a": {"$gt": 5}}}
        ],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=2),
        msg="Same partialFilterExpression on same key is a no-op",
    ),
    IndexTestCase(
        id="partial_separate_from_basic",
        indexes=(
            {"key": {"a": 1}, "name": "idx_partial", "partialFilterExpression": {"a": {"$gt": 0}}},
        ),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_basic"}],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=3),
        msg="Partial index should be separate from basic index on same key",
    ),
    IndexTestCase(
        id="and_clause_order_is_same_signature",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx_and_ab",
                "partialFilterExpression": {"$and": [{"b": 2}, {"a": 1}]},
            },
        ),
        setup_indexes=[
            {
                "key": {"a": 1},
                "name": "idx_and_ab",
                "partialFilterExpression": {"$and": [{"a": 1}, {"b": 2}]},
            }
        ],
        expected=index_created_response(num_indexes_before=2, num_indexes_after=2),
        msg="$and with reordered clauses is normalized to same signature (no-op)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PARTIAL_SIGNATURE_TESTS))
def test_partial_signature(collection, test):
    """Test partialFilterExpression as index signature differentiator."""
    if test.setup_indexes:
        execute_command(
            collection,
            {"createIndexes": collection.name, "indexes": test.setup_indexes},
        )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_partial_create_on_capped(database_client, collection):
    """Test createIndex with partialFilterExpression on capped collection."""
    capped_name = f"{collection.name}_capped"
    database_client.create_collection(capped_name, capped=True, size=100000)
    capped_coll = database_client[capped_name]
    result = execute_command(
        capped_coll,
        {
            "createIndexes": capped_coll.name,
            "indexes": [
                {
                    "key": {"a": 1},
                    "name": "idx_partial",
                    "partialFilterExpression": {"a": {"$gt": 0}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "numIndexesAfter": 2}, msg="Should create partial index on capped"
    )


def test_partial_create_on_clustered(database_client, collection):
    """Test createIndex with partialFilterExpression on clustered collection."""
    clustered_name = f"{collection.name}_clustered"
    database_client.create_collection(
        clustered_name, clusteredIndex={"key": {"_id": 1}, "unique": True}
    )
    clustered_coll = database_client[clustered_name]
    result = execute_command(
        clustered_coll,
        {
            "createIndexes": clustered_coll.name,
            "indexes": [
                {
                    "key": {"a": 1},
                    "name": "idx_partial",
                    "partialFilterExpression": {"a": {"$gt": 0}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "numIndexesAfter": 1}, msg="Should create partial index on clustered"
    )
