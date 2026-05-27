"""Tests for geospatial index creation, data validation, and sparse behavior.

Validates 2dsphere/2d creation, compound indexes, GeoJSON types (including
Multi* and GeometryCollection), coordinate boundaries, null/missing handling,
always-sparse behavior, duplicate/conflicting index handling, and legacy formats.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import INDEX_KEY_SPECS_CONFLICT_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


CREATION_SUCCESS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="creation_2dsphere",
        indexes=({"key": {"location": "2dsphere"}, "name": "loc_2dsphere"},),
        msg="2dsphere creation succeeds",
    ),
    IndexTestCase(
        id="creation_2d",
        indexes=({"key": {"location": "2d"}, "name": "loc_2d"},),
        msg="2d creation succeeds",
    ),
    IndexTestCase(
        id="creation_compound_2dsphere",
        indexes=({"key": {"location": "2dsphere", "name": 1}, "name": "loc_name"},),
        msg="Compound 2dsphere succeeds",
    ),
    IndexTestCase(
        id="creation_compound_2dsphere_second",
        indexes=({"key": {"name": 1, "location": "2dsphere"}, "name": "name_loc"},),
        msg="Compound 2dsphere in second position succeeds",
    ),
    IndexTestCase(
        id="creation_compound_2d",
        indexes=({"key": {"location": "2d", "category": 1}, "name": "loc_cat"},),
        msg="Compound 2d succeeds",
    ),
    IndexTestCase(
        id="creation_multiple_2dsphere_fields",
        indexes=({"key": {"loc1": "2dsphere", "loc2": "2dsphere"}, "name": "multi_2ds"},),
        msg="Multiple 2dsphere fields succeed",
    ),
    IndexTestCase(
        id="creation_2d_custom_min_max",
        indexes=(
            {"key": {"loc": "2d"}, "name": "loc_custom", "min": -500, "max": 500},
        ),  # custom coordinate range
        msg="2d with custom range succeeds",
    ),
    IndexTestCase(
        id="creation_hidden",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_hidden", "hidden": True},),
        msg="Hidden geospatial succeeds",
    ),
    IndexTestCase(
        id="creation_custom_name",
        indexes=({"key": {"loc": "2dsphere"}, "name": "my_geo_idx"},),
        msg="Custom name succeeds",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CREATION_SUCCESS_TESTS))
def test_geospatial_creation_success(collection, test):
    """Test geospatial index creation success cases."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


VALID_GEOJSON_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="data_point",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=({"_id": 1, "loc": {"type": "Point", "coordinates": [-73.97, 40.77]}},),
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-73.97, 40.77]}}],
        msg="Point document inserted and queryable",
    ),
    IndexTestCase(
        id="data_linestring",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=({"_id": 1, "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}},),
        expected=[{"_id": 1, "loc": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}}],
        msg="LineString document inserted",
    ),
    IndexTestCase(
        id="data_polygon",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=(
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            },
        ),
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            }
        ],
        msg="Polygon document inserted",
    ),
    IndexTestCase(
        id="data_polygon_with_hole",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=(
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
                        [[2, 2], [8, 2], [8, 8], [2, 8], [2, 2]],
                    ],
                },
            },
        ),
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
                        [[2, 2], [8, 2], [8, 8], [2, 8], [2, 2]],
                    ],
                },
            }
        ],
        msg="Polygon with hole document inserted",
    ),
    IndexTestCase(
        id="data_legacy_pair",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=({"_id": 1, "loc": [10, 20]},),
        expected=[{"_id": 1, "loc": [10, 20]}],
        msg="Legacy pair with 2dsphere works",
    ),
    IndexTestCase(
        id="data_geojson_extra_fields",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0], "extra": "ignored"}},),
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0], "extra": "ignored"}}],
        msg="GeoJSON with extra fields accepted",
    ),
    IndexTestCase(
        id="data_point_with_altitude",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0, 100]}},),
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0, 100]}}],
        msg="Point with 3 coordinates (altitude) accepted",
    ),
    IndexTestCase(
        id="data_multipoint",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=({"_id": 1, "loc": {"type": "MultiPoint", "coordinates": [[0, 0], [1, 1]]}},),
        expected=[{"_id": 1, "loc": {"type": "MultiPoint", "coordinates": [[0, 0], [1, 1]]}}],
        msg="MultiPoint document inserted",
    ),
    IndexTestCase(
        id="data_multilinestring",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=(
            {
                "_id": 1,
                "loc": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 0], [1, 1]], [[2, 2], [3, 3]]],
                },
            },
        ),
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 0], [1, 1]], [[2, 2], [3, 3]]],
                },
            }
        ],
        msg="MultiLineString document inserted",
    ),
    IndexTestCase(
        id="data_multipolygon",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=(
            {
                "_id": 1,
                "loc": {
                    "type": "MultiPolygon",
                    "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]],
                },
            },
        ),
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "MultiPolygon",
                    "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]],
                },
            }
        ],
        msg="MultiPolygon document inserted",
    ),
    IndexTestCase(
        id="data_geometrycollection",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=(
            {
                "_id": 1,
                "loc": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
                    ],
                },
            },
        ),
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
                    ],
                },
            }
        ],
        msg="GeometryCollection document inserted",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_GEOJSON_TESTS))
def test_geospatial_2dsphere_valid_data(collection, test):
    """Test 2dsphere index with valid GeoJSON types."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection, {"find": collection.name, "hint": "loc_2ds", "sort": {"_id": 1}}
    )
    assertSuccess(result, test.expected, msg=test.msg)


NULL_MISSING_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="null_field_succeeds",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": None},
        msg="Null in 2dsphere field should succeed",
    ),
    IndexTestCase(
        id="missing_field_succeeds",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "other": "x"},
        msg="Missing 2dsphere field should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_MISSING_TESTS))
def test_geospatial_2dsphere_null_missing(collection, test):
    """Test 2dsphere index allows null/missing field documents."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(result, {"n": 1}, msg=test.msg)


SPARSE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="sparse_2dsphere",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        doc=(
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "other": "no geo field"},
        ),
        command_options={"hint": "loc_2ds"},
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Sparse 2dsphere index excludes doc without geo field",
    ),
    IndexTestCase(
        id="sparse_2d",
        indexes=({"key": {"loc": "2d"}, "name": "loc_2d"},),
        doc=(
            {"_id": 1, "loc": [10, 20]},
            {"_id": 2, "other": "no geo field"},
        ),
        command_options={"hint": "loc_2d"},
        expected=[{"_id": 1, "loc": [10, 20]}],
        msg="Sparse 2d index excludes doc without geo field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_TESTS))
def test_geospatial_sparse(collection, test):
    """Test geospatial indexes are always sparse."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"find": collection.name, "hint": test.command_options["hint"], "sort": {"_id": 1}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


def test_geospatial_invalid_data_without_index_succeeds(collection):
    """Test inserting invalid geo data succeeds when no geo index exists."""
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "loc": "not valid geo"}]},
    )
    assertSuccessPartial(result, {"n": 1}, msg="Invalid geo data without index should succeed")


def test_geospatial_2dsphere_boundary_coordinates(collection):
    """Test coordinates at valid boundaries succeed."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2ds"}],
        },
    )
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [0, 90]}},
        ]
    )
    result = execute_command(collection, {"find": collection.name, "sort": {"_id": 1}})
    assertSuccess(
        result,
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [0, 90]}},
        ],
        msg="Boundary coordinates should all succeed",
    )


def test_geospatial_duplicate_index_noop(collection):
    """Test creating the same index twice is a no-op."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "geo"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "geo"}],
        },
    )
    assertSuccessPartial(
        result,
        {"numIndexesBefore": 2, "numIndexesAfter": 2, "ok": 1.0},
        msg="Duplicate index creation should be a no-op",
    )


def test_geospatial_conflicting_index_name_fails(collection):
    """Test creating an index with same name but different key fails."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "geo"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2d"}, "name": "geo"}],
        },
    )
    assertFailureCode(
        result, INDEX_KEY_SPECS_CONFLICT_ERROR, msg="Conflicting index name should fail"
    )


def test_geospatial_2d_null_field_succeeds(collection):
    """Test 2d index allows null field (sparse behavior)."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2d"}, "name": "loc_2d"}],
        },
    )
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": 1, "loc": None}]}
    )
    assertSuccessPartial(result, {"n": 1}, msg="Null in 2d field should succeed")


def test_geospatial_2d_missing_field_succeeds(collection):
    """Test 2d index allows missing field (sparse behavior)."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2d"}, "name": "loc_2d"}],
        },
    )
    result = execute_command(
        collection, {"insert": collection.name, "documents": [{"_id": 1, "other": "x"}]}
    )
    assertSuccessPartial(result, {"n": 1}, msg="Missing 2d field should succeed")


def test_geospatial_2d_legacy_embedded_doc(collection):
    """Test 2d index accepts legacy embedded document format {lng, lat}."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2d"}, "name": "loc_2d"}],
        },
    )
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "loc": {"lng": 10, "lat": 20}}]},
    )
    assertSuccessPartial(result, {"n": 1}, msg="Legacy {lng, lat} format accepted by 2d index")
