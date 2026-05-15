"""
Tests for combinations of geospatial query operators with logical ($and, $or, $not, $nor)
and array ($elemMatch) operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POLYGON = {
    "$geometry": {
        "type": "Polygon",
        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
    }
}

POLYGON2 = {
    "$geometry": {
        "type": "Polygon",
        "coordinates": [[[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]]],
    }
}


LOGICAL_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="and_geo_with_non_geo",
        filter={"$and": [{"loc": {"$geoWithin": POLYGON}}, {"status": "active"}]},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}, "status": "inactive"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"}],
        msg="$and combining geo and non-geo filter should intersect results",
    ),
    QueryTestCase(
        id="or_two_geo_queries",
        filter={"$or": [{"loc": {"$geoWithin": POLYGON}}, {"loc": {"$geoWithin": POLYGON2}}]},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [25, 25]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [25, 25]}},
        ],
        msg="$or combining two geo queries should union results",
    ),
    QueryTestCase(
        id="or_geo_with_non_geo",
        filter={"$or": [{"loc": {"$geoWithin": POLYGON}}, {"status": "active"}]},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "inactive"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [60, 60]}, "status": "inactive"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "inactive"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
        ],
        msg="$or combining geo and non-geo filter should union results",
    ),
    QueryTestCase(
        id="nor_two_geo_queries",
        filter={"$nor": [{"loc": {"$geoWithin": POLYGON}}, {"loc": {"$geoWithin": POLYGON2}}]},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [25, 25]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}}],
        msg="$nor should return documents not matching any condition",
    ),
    QueryTestCase(
        id="nor_geo_with_non_geo",
        filter={"$nor": [{"loc": {"$geoWithin": POLYGON}}, {"status": "inactive"}]},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "status": "active"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [60, 60]}, "status": "inactive"},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "status": "active"}
        ],
        msg="$nor combining geo and non-geo filter should exclude both",
    ),
    QueryTestCase(
        id="elemMatch_geo",
        filter={"locations": {"$elemMatch": {"$geoWithin": POLYGON}}},
        doc=[
            {
                "_id": 1,
                "locations": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [50, 50]},
                ],
            },
            {
                "_id": 2,
                "locations": [
                    {"type": "Point", "coordinates": [50, 50]},
                    {"type": "Point", "coordinates": [60, 60]},
                ],
            },
        ],
        expected=[
            {
                "_id": 1,
                "locations": [
                    {"type": "Point", "coordinates": [0, 0]},
                    {"type": "Point", "coordinates": [50, 50]},
                ],
            }
        ],
        msg="$elemMatch with $geoWithin should match if any array element is within",
    ),
    QueryTestCase(
        id="not_geo",
        filter={"loc": {"$not": {"$geoWithin": POLYGON}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [60, 60]}},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [60, 60]}},
        ],
        msg="$not with $geoWithin should return documents NOT within the polygon",
    ),
    QueryTestCase(
        id="and_negated_geo_with_non_geo",
        filter={"$and": [{"loc": {"$not": {"$geoWithin": POLYGON}}}, {"name": "B"}]},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "name": "B"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [60, 60]}, "name": "B"},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}, "name": "B"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [60, 60]}, "name": "B"},
        ],
        msg="$and combining negated $geoWithin with equality match on non-geo field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOGICAL_OPERATOR_TESTS))
def test_geoWithin_logical_operators(collection, test):
    """Test $geoWithin with logical operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
