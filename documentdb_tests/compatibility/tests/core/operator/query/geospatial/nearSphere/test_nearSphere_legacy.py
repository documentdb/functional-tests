"""Tests for $nearSphere with legacy 2d index."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

LEGACY_2D_INDEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_2d_index",
        filter={"loc": {"$nearSphere": [0, 0]}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Should succeed with 2d index",
    ),
    QueryTestCase(
        id="2d_index_distance_ordering",
        filter={"loc": {"$nearSphere": [0, 0]}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [1, 1]},
        ],
        expected=[
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [1, 1]},
            {"_id": 1, "loc": [5, 5]},
        ],
        msg="Should sort by spherical distance with 2d index",
    ),
    QueryTestCase(
        id="legacy_three_element_array",
        filter={"loc": {"$nearSphere": [-73.9667, 40.78, 0]}},
        doc=[{"_id": 1, "loc": [-73.9667, 40.78]}],
        expected=[{"_id": 1, "loc": [-73.9667, 40.78]}],
        msg="Should accept legacy three-element coordinate array (altitude ignored)",
    ),
    QueryTestCase(
        id="2d_trailing_field_exists",
        filter={"loc": {"$nearSphere": [0, 0]}, "extra": {"$exists": True}},
        doc=[
            {"_id": 1, "loc": [0, 0], "extra": "value"},
            {"_id": 2, "loc": [1, 1]},
        ],
        expected=[{"_id": 1, "loc": [0, 0], "extra": "value"}],
        msg="Should filter by $exists on trailing field",
    ),
    QueryTestCase(
        id="2d_trailing_field_not_exists",
        filter={"loc": {"$nearSphere": [0, 0]}, "extra": {"$exists": False}},
        doc=[
            {"_id": 1, "loc": [0, 0], "extra": "value"},
            {"_id": 2, "loc": [1, 1]},
        ],
        expected=[{"_id": 2, "loc": [1, 1]}],
        msg="Should match documents where trailing field does not exist",
    ),
    QueryTestCase(
        id="2d_trailing_field_null",
        filter={"loc": {"$nearSphere": [0, 0]}, "extra": None},
        doc=[
            {"_id": 1, "loc": [0, 0], "extra": "value"},
            {"_id": 2, "loc": [1, 1]},
        ],
        expected=[{"_id": 2, "loc": [1, 1]}],
        msg="Should match documents where trailing field is null/missing",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LEGACY_2D_INDEX_TESTS))
def test_nearSphere_legacy_2d_index(collection, test):
    """Verifies $nearSphere behavior with legacy 2d index."""
    collection.create_index([("loc", "2d")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
