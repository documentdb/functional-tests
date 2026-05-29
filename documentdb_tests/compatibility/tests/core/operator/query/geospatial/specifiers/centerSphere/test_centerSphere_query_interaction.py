"""Tests for $centerSphere query interaction — $and, $or, $not, multiple
geospatial fields, projection, limit, sort, and skip."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.geospatial.utils.constants import (
    EARTH_RADIUS_KM,
)
from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="combined_with_field_predicate",
        filter={
            "loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}},
            "status": "active",
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "inactive"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
        ],
        msg="Should filter by both $centerSphere and non-geospatial predicate",
    ),
    QueryTestCase(
        id="with_and_combining_two_geo",
        filter={
            "$and": [
                {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 500 / EARTH_RADIUS_KM]}}},
                {"loc": {"$geoWithin": {"$centerSphere": [[5, 0], 500 / EARTH_RADIUS_KM]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [2.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [2.5, 0]}}],
        msg="Should support $and combining two $centerSphere queries (intersection)",
    ),
    QueryTestCase(
        id="with_not",
        filter={"loc": {"$not": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [100, 45]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [100, 45]}},
        ],
        msg="Should support $not to negate $centerSphere query",
    ),
    QueryTestCase(
        id="with_or_combining_two_geo",
        filter={
            "$or": [
                {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
                {"loc": {"$geoWithin": {"$centerSphere": [[50, 50], 0.01]}}},
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [100, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        msg="Should support $or combining two $centerSphere queries (union)",
    ),
    QueryTestCase(
        id="multiple_geospatial_fields",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
        doc=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "alt_loc": {"type": "Point", "coordinates": [100, 45]},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [100, 45]},
                "alt_loc": {"type": "Point", "coordinates": [0, 0]},
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "alt_loc": {"type": "Point", "coordinates": [100, 45]},
            },
        ],
        msg="Query on one geospatial field should not consider other geo fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_centerSphere_query_interaction(collection, test):
    """Verifies $centerSphere works with other query operators and $and."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


def test_centerSphere_with_projection(collection):
    """Verifies $centerSphere works with field projection."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "name": "B"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}},
            "projection": {"name": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "name": "A"}], msg="Should work with projection")


def test_centerSphere_with_limit(collection):
    """Verifies $centerSphere respects limit parameter."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
            "limit": 1,
            "sort": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should return exactly 1 document with limit=1",
    )


def test_centerSphere_with_sort(collection):
    """Verifies $centerSphere works with non-distance sort."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "C"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "name": "A"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}, "name": "B"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
            "sort": {"name": 1},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "name": "A"},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "C"},
        ],
        msg="Should respect sort order on non-distance field",
    )


def test_centerSphere_with_skip(collection):
    """Verifies $centerSphere respects skip parameter."""
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 1]}}},
            "sort": {"_id": 1},
            "skip": 1,
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}}],
        msg="Should return remaining results after skipping 1",
    )
