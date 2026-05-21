"""
Tests for $box valid argument handling.

Validates accepted coordinate types, argument structures,
and document location type matching behavior.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARGUMENT_HANDLING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [100, 100]]}}},
        doc=[{"_id": 1, "loc": [50, 50]}, {"_id": 2, "loc": [150, 150]}],
        expected=[{"_id": 1, "loc": [50, 50]}],
        msg="$box should accept int coordinates",
    ),
    QueryTestCase(
        id="double_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[0.5, 0.5], [99.5, 99.5]]}}},
        doc=[{"_id": 1, "loc": [50.0, 50.0]}, {"_id": 2, "loc": [100.0, 100.0]}],
        expected=[{"_id": 1, "loc": [50.0, 50.0]}],
        msg="$box should accept double coordinates",
    ),
    QueryTestCase(
        id="long_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[Int64(0), Int64(0)], [Int64(100), Int64(100)]]}}},
        doc=[{"_id": 1, "loc": [50, 50]}, {"_id": 2, "loc": [150, 150]}],
        expected=[{"_id": 1, "loc": [50, 50]}],
        msg="$box should accept long coordinates",
    ),
    QueryTestCase(
        id="decimal128_coordinates",
        filter={
            "loc": {
                "$geoWithin": {
                    "$box": [
                        [Decimal128("0"), Decimal128("0")],
                        [Decimal128("100"), Decimal128("100")],
                    ]
                }
            }
        },
        doc=[{"_id": 1, "loc": [50, 50]}, {"_id": 2, "loc": [150, 150]}],
        expected=[{"_id": 1, "loc": [50, 50]}],
        msg="$box should accept decimal128 coordinates",
    ),
    QueryTestCase(
        id="mixed_numeric_types",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0.5], [Int64(100), Decimal128("100")]]}}},
        doc=[{"_id": 1, "loc": [50, 50]}, {"_id": 2, "loc": [150, 150]}],
        expected=[{"_id": 1, "loc": [50, 50]}],
        msg="$box should accept mixed numeric types",
    ),
    QueryTestCase(
        id="three_points_accepted",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [50, 50], [100, 100]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [150, 150]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Three points should be accepted; only the first two define the box",
    ),
    QueryTestCase(
        id="legacy_pair_matches",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Legacy coordinate pair should match",
    ),
    QueryTestCase(
        id="object_with_xy_matches",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": {"x": 5, "y": 5}}],
        expected=[{"_id": 1, "loc": {"x": 5, "y": 5}}],
        msg="Object with x/y fields is treated as legacy coordinate pair",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_HANDLING_TESTS))
def test_box_argument_handling(collection, test):
    """Test $box argument handling — see per-case msg for details."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, ignore_doc_order=True, msg=test.msg)
