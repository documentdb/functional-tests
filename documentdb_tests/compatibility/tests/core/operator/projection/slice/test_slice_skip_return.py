"""Tests for $slice projection operator: skip/return [skip, limit] form.

Tests $slice projection with two-element array argument [skip, limit].
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SLICE_SKIP_RETURN_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "skip_0_limit_2",
        projection={"arr": {"$slice": [0, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["a", "b"]}],
        msg="$slice: [0, 2] should return first 2 elements",
    ),
    ProjectionTestCase(
        "skip_1_limit_2",
        projection={"arr": {"$slice": [1, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["b", "c"]}],
        msg="$slice: [1, 2] should skip 1 and return next 2",
    ),
    ProjectionTestCase(
        "skip_2_limit_2",
        projection={"arr": {"$slice": [2, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["c", "d"]}],
        msg="$slice: [2, 2] should skip 2 and return next 2",
    ),
    ProjectionTestCase(
        "skip_3_limit_2",
        projection={"arr": {"$slice": [3, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["d"]}],
        msg="$slice: [3, 2] should skip 3 and return remaining 1",
    ),
    ProjectionTestCase(
        "skip_4_limit_2_empty",
        projection={"arr": {"$slice": [4, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: [4, 2] should return empty when skip equals array length",
    ),
    ProjectionTestCase(
        "skip_exceeds_length",
        projection={"arr": {"$slice": [10, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: [10, 2] should return empty when skip exceeds array length",
    ),
    ProjectionTestCase(
        "negative_skip_1_limit_1",
        projection={"arr": {"$slice": [-1, 1]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["d"]}],
        msg="$slice: [-1, 1] should start from last element and return 1",
    ),
    ProjectionTestCase(
        "negative_skip_2_limit_1",
        projection={"arr": {"$slice": [-2, 1]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["c"]}],
        msg="$slice: [-2, 1] should start from second-to-last and return 1",
    ),
    ProjectionTestCase(
        "negative_skip_3_limit_2",
        projection={"arr": {"$slice": [-3, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["b", "c"]}],
        msg="$slice: [-3, 2] should start from 3rd-to-last and return 2",
    ),
    ProjectionTestCase(
        "negative_skip_exceeds_length",
        projection={"arr": {"$slice": [-5, 2]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        expected=[{"_id": 1, "arr": ["a", "b"]}],
        msg="$slice: [-5, 2] should start from beginning when abs(skip) exceeds length",
    ),
    ProjectionTestCase(
        "skip_2_limit_3_from_11",
        projection={"arr": {"$slice": [2, 3]}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}],
        expected=[{"_id": 1, "arr": [3, 4, 5]}],
        msg="$slice: [2, 3] should skip 2 and return elements at index 2, 3, 4",
    ),
    ProjectionTestCase(
        "negative_skip_5_limit_4",
        projection={"arr": {"$slice": [-5, 4]}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}],
        expected=[{"_id": 1, "arr": [7, 8, 9, 10]}],
        msg="$slice: [-5, 4] should start from 5th-to-last and return 4",
    ),
    ProjectionTestCase(
        "negative_skip_5_limit_exceeds",
        projection={"arr": {"$slice": [-5, 10]}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}],
        expected=[{"_id": 1, "arr": [7, 8, 9, 10, 11]}],
        msg="$slice: [-5, 10] should return all from 5th-to-last when limit exceeds remaining",
    ),
    ProjectionTestCase(
        "skip_0_limit_exceeds",
        projection={"arr": {"$slice": [0, 100]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c"]}],
        expected=[{"_id": 1, "arr": ["a", "b", "c"]}],
        msg="$slice: [0, 100] should return all elements when limit exceeds length",
    ),
    ProjectionTestCase(
        "single_element_skip_0_limit_1",
        projection={"arr": {"$slice": [0, 1]}},
        doc=[{"_id": 1, "arr": ["x"]}],
        expected=[{"_id": 1, "arr": ["x"]}],
        msg="$slice: [0, 1] on single-element array should return that element",
    ),
    ProjectionTestCase(
        "single_element_skip_1_limit_1",
        projection={"arr": {"$slice": [1, 1]}},
        doc=[{"_id": 1, "arr": ["x"]}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: [1, 1] on single-element array should return empty",
    ),
    ProjectionTestCase(
        "empty_array_skip_return",
        projection={"arr": {"$slice": [0, 2]}},
        doc=[{"_id": 1, "arr": []}],
        expected=[{"_id": 1, "arr": []}],
        msg="$slice: [0, 2] on empty array should return empty array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SLICE_SKIP_RETURN_TESTS))
def test_slice_skip_return(collection, test: ProjectionTestCase):
    """Test $slice projection with [skip, limit] form."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "projection": test.projection},
    )
    assertSuccess(result, test.expected, msg=test.msg)
