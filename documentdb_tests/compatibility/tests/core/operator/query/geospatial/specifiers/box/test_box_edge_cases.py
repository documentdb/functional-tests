"""
Tests for $box edge cases.

Validates boundary coordinates, coordinate inversion, negative zero,
null/missing fields, boundary inclusion, and floating-point precision.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="zero_area_same_point",
        filter={"loc": {"$geoWithin": {"$box": [[5, 5], [5, 5]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [6, 6]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Zero area box (same point) should match exact point",
    ),
    QueryTestCase(
        id="zero_width",
        filter={"loc": {"$geoWithin": {"$box": [[5, 0], [5, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [6, 5]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Zero width box should match points on the line",
    ),
    QueryTestCase(
        id="zero_height",
        filter={"loc": {"$geoWithin": {"$box": [[0, 5], [10, 5]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [5, 6]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Zero height box should match points on the line",
    ),
    QueryTestCase(
        id="negative_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[-100, -100], [100, 100]]}}},
        doc=[{"_id": 1, "loc": [-50, -50]}, {"_id": 2, "loc": [200, 200]}],
        expected=[{"_id": 1, "loc": [-50, -50]}],
        msg="$box should work with negative coordinates",
    ),
    QueryTestCase(
        id="very_large_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [1000000, 1000000]]}}},
        doc=[{"_id": 1, "loc": [500000, 500000]}, {"_id": 2, "loc": [2000000, 2000000]}],
        expected=[{"_id": 1, "loc": [500000, 500000]}],
        msg="$box should work with very large coordinates",
    ),
    QueryTestCase(
        id="very_small_area",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [0.0001, 0.0001]]}}},
        doc=[{"_id": 1, "loc": [0.00005, 0.00005]}, {"_id": 2, "loc": [1, 1]}],
        expected=[{"_id": 1, "loc": [0.00005, 0.00005]}],
        msg="$box should work with very small area",
    ),
    QueryTestCase(
        id="fully_inverted",
        filter={"loc": {"$geoWithin": {"$box": [[10, 10], [0, 0]]}}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [10, 10]},
        ],
        expected=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [10, 10]},
        ],
        msg="Inverted box returns same results as normal order",
    ),
    QueryTestCase(
        id="x_inverted",
        filter={"loc": {"$geoWithin": {"$box": [[10, 0], [0, 10]]}}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [10, 10]},
        ],
        expected=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [10, 10]},
        ],
        msg="X-inverted box returns same results as normal order",
    ),
    QueryTestCase(
        id="y_inverted",
        filter={"loc": {"$geoWithin": {"$box": [[0, 10], [10, 0]]}}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [10, 10]},
        ],
        expected=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [10, 10]},
        ],
        msg="Y-inverted box returns same results as normal order",
    ),
    QueryTestCase(
        id="negative_zero_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[-0.0, -0.0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}, {"_id": 2, "loc": [15, 15]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="Negative zero coordinates should work normally",
    ),
    QueryTestCase(
        id="string_field_no_match",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": "not a coordinate"}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="String location field should not match",
    ),
    QueryTestCase(
        id="null_field",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": None}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Null location field should not match",
    ),
    QueryTestCase(
        id="missing_field",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "other": "value"}, {"_id": 2, "loc": [5, 5]}],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="Missing location field should not match",
    ),
    QueryTestCase(
        id="bottom_left_corner_included",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        expected=[{"_id": 1, "loc": [0, 0]}],
        msg="Bottom-left corner should be included",
    ),
    QueryTestCase(
        id="upper_right_corner_included",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [10, 10]}],
        expected=[{"_id": 1, "loc": [10, 10]}],
        msg="Upper-right corner should be included",
    ),
    QueryTestCase(
        id="left_edge_included",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [0, 5]}],
        expected=[{"_id": 1, "loc": [0, 5]}],
        msg="Left edge should be included",
    ),
    QueryTestCase(
        id="right_edge_included",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [10, 5]}],
        expected=[{"_id": 1, "loc": [10, 5]}],
        msg="Right edge should be included",
    ),
    QueryTestCase(
        id="top_edge_included",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 10]}],
        expected=[{"_id": 1, "loc": [5, 10]}],
        msg="Top edge should be included",
    ),
    QueryTestCase(
        id="bottom_edge_included",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 0]}],
        expected=[{"_id": 1, "loc": [5, 0]}],
        msg="Bottom edge should be included",
    ),
    QueryTestCase(
        id="just_outside_excluded",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": [-0.001, 5]},
            {"_id": 2, "loc": [10.001, 5]},
            {"_id": 3, "loc": [5, 10.001]},
            {"_id": 4, "loc": [5, -0.001]},
        ],
        expected=[],
        msg="Points just outside each edge should not match",
    ),
    QueryTestCase(
        id="just_inside_included",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [0.001, 0.001]}],
        expected=[{"_id": 1, "loc": [0.001, 0.001]}],
        msg="Point just inside should match",
    ),
    QueryTestCase(
        id="double_near_max_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [1e308, 1e308]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}],
        expected=[{"_id": 1, "loc": [5, 5]}],
        msg="$box with DOUBLE_NEAR_MAX coordinates should work",
    ),
    QueryTestCase(
        id="double_min_subnormal_coordinates",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [5e-324, 5e-324]]}}},
        doc=[{"_id": 1, "loc": [5, 5]}],
        expected=[],
        msg="$box with DOUBLE_MIN_SUBNORMAL area should not match distant points",
    ),
    QueryTestCase(
        id="coordinates_differ_by_1e_minus_10",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [0.0000000001, 0.0000000001]]}}},
        doc=[{"_id": 1, "loc": [0.00000000005, 0.00000000005]}],
        expected=[{"_id": 1, "loc": [0.00000000005, 0.00000000005]}],
        msg="$box with coordinates differing by 1e-10 should match point within",
    ),
    QueryTestCase(
        id="doc_with_3_element_array",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[{"_id": 1, "loc": [5, 5, 99]}, {"_id": 2, "loc": [15, 15, 1]}],
        expected=[{"_id": 1, "loc": [5, 5, 99]}],
        msg="Doc with 3-element array should match using first 2 elements",
    ),
    QueryTestCase(
        id="linestring_not_matched",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {"_id": 1, "loc": {"type": "LineString", "coordinates": [[1, 1], [5, 5]]}},
            {"_id": 2, "loc": [5, 5]},
        ],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="$box should not match LineString geometry documents",
    ),
    QueryTestCase(
        id="polygon_not_matched",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0], [10, 10]]}}},
        doc=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]],
                },
            },
            {"_id": 2, "loc": [5, 5]},
        ],
        expected=[{"_id": 2, "loc": [5, 5]}],
        msg="$box should not match Polygon geometry documents",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_box_edge_cases(collection, test):
    """Test $box edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, ignore_doc_order=True, msg=test.msg)
