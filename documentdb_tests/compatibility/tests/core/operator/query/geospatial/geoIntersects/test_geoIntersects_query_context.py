"""
Tests for $geoIntersects query context and index behavior — find,
$not/$and/$or/$nor combinations, and 2dsphere index scenarios.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Standard query polygon
QUERY_POLYGON = {
    "$geometry": {
        "type": "Polygon",
        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
    }
}

QUERY_CONTEXT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="find_query",
        filter={"loc": {"$geoIntersects": QUERY_POLYGON}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects in find() query should work",
    ),
    QueryTestCase(
        id="not_negation",
        filter={"loc": {"$not": {"$geoIntersects": QUERY_POLYGON}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}}],
        msg="$not with $geoIntersects should return non-intersecting documents",
    ),
    QueryTestCase(
        id="and_with_non_geo_condition",
        filter={
            "$and": [
                {"loc": {"$geoIntersects": QUERY_POLYGON}},
                {"status": "active"},
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "inactive"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"}],
        msg="$and with $geoIntersects and non-geo condition should work",
    ),
    QueryTestCase(
        id="or_with_geo_conditions",
        filter={
            "$or": [
                {"loc": {"$geoIntersects": QUERY_POLYGON}},
                {"status": "special"},
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "normal"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "special"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "normal"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "normal"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "special"},
        ],
        msg="$or with $geoIntersects should work",
    ),
    QueryTestCase(
        id="and_with_multiple_geoIntersects",
        filter={
            "$and": [
                {
                    "loc": {
                        "$geoIntersects": {
                            "$geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [[-10, -10], [5, -10], [5, 10], [-10, 10], [-10, -10]]
                                ],
                            }
                        }
                    }
                },
                {
                    "loc": {
                        "$geoIntersects": {
                            "$geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [[-5, -10], [10, -10], [10, 10], [-5, 10], [-5, -10]]
                                ],
                            }
                        }
                    }
                },
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-8, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [8, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg=(
            "$and with multiple $geoIntersects should return only"
            " docs in intersection of both regions"
        ),
    ),
    QueryTestCase(
        id="nor_with_geoIntersects",
        filter={"$nor": [{"loc": {"$geoIntersects": QUERY_POLYGON}}]},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}}],
        msg="$nor with $geoIntersects should return non-intersecting documents",
    ),
    QueryTestCase(
        id="or_with_many_points",
        filter={
            "$or": [
                {
                    "loc": {
                        "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}
                    }
                },
                {
                    "loc": {
                        "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [10, 10]}}
                    }
                },
                {
                    "loc": {
                        "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [20, 20]}}
                    }
                },
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [20, 20]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [20, 20]}},
        ],
        msg="$or with multiple $geoIntersects Point queries should work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(QUERY_CONTEXT_TESTS))
def test_geoIntersects_query_context(collection, test):
    """Test $geoIntersects in various query contexts."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


def test_geoIntersects_basic_2dsphere(collection):
    """Test $geoIntersects with basic 2dsphere index."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ]
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"loc": {"$geoIntersects": QUERY_POLYGON}}}
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$geoIntersects should work with 2dsphere index",
    )


def test_geoIntersects_with_non_geo_filter(collection):
    """Test $geoIntersects with non-geo filter on indexed collection."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "status": "inactive"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoIntersects": QUERY_POLYGON}, "status": "active"},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"}],
        msg="$geoIntersects with non-geo filter on indexed collection should work",
    )


def test_geoIntersects_compound_2dsphere(collection):
    """Test $geoIntersects with compound 2dsphere index."""
    collection.create_index([("loc", "2dsphere"), ("status", 1)])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoIntersects": QUERY_POLYGON}, "status": "active"},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"}],
        msg="$geoIntersects should work with compound 2dsphere index",
    )
