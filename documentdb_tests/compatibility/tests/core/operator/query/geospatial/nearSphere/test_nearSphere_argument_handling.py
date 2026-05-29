"""Tests for $nearSphere argument handling — valid arguments, query interactions, field paths."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

VALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="coordinates_before_type",
        filter={"loc": {"$nearSphere": {"$geometry": {"coordinates": [0, 0], "type": "Point"}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should accept coordinates before type in $geometry (field order doesn't matter)",
    ),
    QueryTestCase(
        id="missing_type_defaults_to_point",
        filter={"loc": {"$nearSphere": {"$geometry": {"coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should default to Point when type field is missing from $geometry",
    ),
    QueryTestCase(
        id="geometry_with_extra_fields",
        filter={
            "loc": {
                "$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0], "extra": 1}}
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should ignore extra fields in $geometry object",
    ),
    QueryTestCase(
        id="inside_nested_and",
        filter={
            "$and": [
                {
                    "$and": [
                        {
                            "loc": {
                                "$nearSphere": {
                                    "$geometry": {"type": "Point", "coordinates": [0, 0]}
                                }
                            }
                        }
                    ]
                }
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should work inside nested $and",
    ),
    QueryTestCase(
        id="coordinates_mixed_numeric",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [-73.9667, Int64(40)]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-73.9667, 40]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-73.9667, 40]}}],
        msg="Should accept mixed numeric types in coordinates",
    ),
]

LEGACY_VALID_COORD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="legacy_coordinates_double",
        filter={"loc": {"$nearSphere": [-73.9667, 40.78]}},
        doc=[{"_id": 1, "loc": [-73.9667, 40.78]}],
        expected=[{"_id": 1, "loc": [-73.9667, 40.78]}],
        msg="Should accept legacy double coordinates",
    ),
    QueryTestCase(
        id="legacy_coordinates_int",
        filter={"loc": {"$nearSphere": [-74, 40]}},
        doc=[{"_id": 1, "loc": [-74, 40]}],
        expected=[{"_id": 1, "loc": [-74, 40]}],
        msg="Should accept legacy int coordinates",
    ),
    QueryTestCase(
        id="legacy_coordinates_long",
        filter={"loc": {"$nearSphere": [Int64(-74), Int64(40)]}},
        doc=[{"_id": 1, "loc": [-74, 40]}],
        expected=[{"_id": 1, "loc": [-74, 40]}],
        msg="Should accept legacy long coordinates",
    ),
    QueryTestCase(
        id="legacy_coordinates_decimal128",
        filter={"loc": {"$nearSphere": [Decimal128("-73.9667"), Decimal128("40.78")]}},
        doc=[{"_id": 1, "loc": [-73.9667, 40.78]}],
        expected=[{"_id": 1, "loc": [-73.9667, 40.78]}],
        msg="Should accept legacy decimal128 coordinates",
    ),
]

QUERY_INTERACTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nearSphere_inside_and",
        filter={
            "$and": [
                {"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
                {"category": "A"},
            ]
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "category": "B"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "category": "A"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 2]}, "category": "A"},
        ],
        msg="Should work inside $and with additional filter",
    ),
    QueryTestCase(
        id="nearSphere_with_equality_other_field",
        filter={
            "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
            "category": "A",
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}, "category": "B"},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "category": "A"},
        ],
        msg="Should combine with equality on another field",
    ),
]

QUERY_BEHAVIOR_TESTS: list[QueryTestCase] = (
    VALID_ARGUMENT_TESTS + LEGACY_VALID_COORD_TESTS + QUERY_INTERACTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(QUERY_BEHAVIOR_TESTS))
def test_nearSphere_query_behavior(collection, test):
    """Verifies $nearSphere query behavior."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_nearSphere_nested_field(collection):
    """Verifies $nearSphere works on nested field path."""
    collection.create_index([("address.location", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "address": {"location": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "address": {"location": {"type": "Point", "coordinates": [5, 5]}}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "address.location": {
                    "$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}
                }
            },
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "address": {"location": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "address": {"location": {"type": "Point", "coordinates": [5, 5]}}},
        ],
        msg="Should work on nested field path",
    )


def test_nearSphere_array_of_geojson_points(collection):
    """Verifies $nearSphere on field containing multiple GeoJSON points via MultiPoint."""
    collection.create_index([("locations", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "locations": {"type": "MultiPoint", "coordinates": [[0, 0], [10, 10]]}},
            {"_id": 2, "locations": {"type": "MultiPoint", "coordinates": [[50, 50], [60, 60]]}},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "locations": {
                    "$nearSphere": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0]},
                        "$maxDistance": 200000,
                    }
                }
            },
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "locations": {"type": "MultiPoint", "coordinates": [[0, 0], [10, 10]]}}],
        msg="Should match document with MultiPoint containing nearby coordinate",
    )
