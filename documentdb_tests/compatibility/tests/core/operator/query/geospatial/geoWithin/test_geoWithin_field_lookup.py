"""
Tests for $geoWithin field lookup patterns.

Covers dotted paths through embedded documents, arrays of embedded documents
with dotted paths, deeply nested paths, and non-existent / null intermediate paths.
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

POINT_INSIDE = {"type": "Point", "coordinates": [0, 0]}
POINT_OUTSIDE = {"type": "Point", "coordinates": [50, 50]}


DOTTED_PATH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_field_inside",
        filter={"geo.loc": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "geo": {"loc": POINT_INSIDE}}, {"_id": 2, "geo": {"loc": POINT_OUTSIDE}}],
        expected=[{"_id": 1, "geo": {"loc": POINT_INSIDE}}],
        msg="Dotted path to nested geo field should match point inside",
    ),
    QueryTestCase(
        id="nested_field_outside",
        filter={"geo.loc": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "geo": {"loc": POINT_OUTSIDE}}],
        expected=[],
        msg="Dotted path to nested geo field outside polygon should not match",
    ),
    QueryTestCase(
        id="deeply_nested_geojson_feature",
        filter={"feature.properties.geometry.location": {"$geoWithin": POLYGON}},
        doc=[
            {"_id": 1, "feature": {"properties": {"geometry": {"location": POINT_INSIDE}}}},
            {"_id": 2, "feature": {"properties": {"geometry": {"location": POINT_OUTSIDE}}}},
        ],
        expected=[{"_id": 1, "feature": {"properties": {"geometry": {"location": POINT_INSIDE}}}}],
        msg="Deeply nested dotted path through GeoJSON-Feature-like schema should match",
    ),
    QueryTestCase(
        id="null_parent_no_match",
        filter={"geo.loc": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "geo": None}, {"_id": 2, "geo": {"loc": POINT_INSIDE}}],
        expected=[{"_id": 2, "geo": {"loc": POINT_INSIDE}}],
        msg="Null parent field should not match",
    ),
    QueryTestCase(
        id="missing_intermediate_field",
        filter={"geo.loc": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "geo": {"other": "value"}}, {"_id": 2, "geo": {"loc": POINT_INSIDE}}],
        expected=[{"_id": 2, "geo": {"loc": POINT_INSIDE}}],
        msg="Missing intermediate field (parent has no child) should not match",
    ),
    QueryTestCase(
        id="non_object_intermediate",
        filter={"address.geocode.location": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "address": {"geocode": "not_an_object"}}],
        expected=[],
        msg="Dotted path through non-object intermediate should not match",
    ),
    QueryTestCase(
        id="nonexistent_top_field",
        filter={"missing.loc": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "geo": {"loc": POINT_INSIDE}}],
        expected=[],
        msg="Dotted path with non-existent top-level field should not match",
    ),
    QueryTestCase(
        id="dotted_path_intermediate_null",
        filter={"address.geocode.location": {"$geoWithin": POLYGON}},
        doc=[{"_id": 1, "address": {"geocode": None}}],
        expected=[],
        msg="Dotted path where intermediate field is null should not match",
    ),
]


ARRAY_OF_EMBEDDED_DOCS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_of_objects_any_inside",
        filter={"addresses.location": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "addresses": [
                    {"label": "home", "location": POINT_INSIDE},
                    {"label": "work", "location": POINT_OUTSIDE},
                ],
            },
            {
                "_id": 2,
                "addresses": [
                    {"label": "home", "location": {"type": "Point", "coordinates": [60, 60]}},
                    {"label": "work", "location": POINT_OUTSIDE},
                ],
            },
        ],
        expected=[
            {
                "_id": 1,
                "addresses": [
                    {"label": "home", "location": POINT_INSIDE},
                    {"label": "work", "location": POINT_OUTSIDE},
                ],
            }
        ],
        msg="Dotted path through array of objects matches if ANY element's geo is inside",
    ),
    QueryTestCase(
        id="array_of_objects_none_inside",
        filter={"addresses.location": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "addresses": [
                    {"label": "home", "location": POINT_OUTSIDE},
                    {"label": "work", "location": {"type": "Point", "coordinates": [60, 60]}},
                ],
            }
        ],
        expected=[],
        msg="Dotted path through array of objects with no inside element should not match",
    ),
    QueryTestCase(
        id="trips_waypoints_location",
        filter={"trips.start.location": {"$geoWithin": POLYGON}},
        doc=[
            {
                "_id": 1,
                "trips": [
                    {"start": {"location": POINT_INSIDE}},
                    {"start": {"location": POINT_OUTSIDE}},
                ],
            }
        ],
        expected=[
            {
                "_id": 1,
                "trips": [
                    {"start": {"location": POINT_INSIDE}},
                    {"start": {"location": POINT_OUTSIDE}},
                ],
            }
        ],
        msg="Dotted path traverses array then nested object correctly",
    ),
]


ALL_TESTS = DOTTED_PATH_TESTS + ARRAY_OF_EMBEDDED_DOCS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geoWithin_field_lookup(collection, test):
    """Parametrized test for $geoWithin field lookup patterns."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
