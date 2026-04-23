from __future__ import annotations

import pytest
from bson import MaxKey, MinKey

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Array Sort Key Extraction]: in ascending sort the sort key for an
# array field is the minimum element by BSON comparison order, and in
# descending sort it is the maximum element.
SORT_ARRAY_KEY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "array_key_asc_min_element",
        docs=[
            {"_id": 1, "v": [10, 30]},
            {"_id": 2, "v": 5},
            {"_id": 3, "v": [25, 20, 15]},
            {"_id": 4, "v": 12},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 2, "v": 5},
            {"_id": 1, "v": [10, 30]},
            {"_id": 4, "v": 12},
            {"_id": 3, "v": [25, 20, 15]},
        ],
        msg="$sort ascending should use the minimum array element as the sort key",
    ),
    StageTestCase(
        "array_key_desc_max_element",
        docs=[
            {"_id": 1, "v": [10, 30]},
            {"_id": 2, "v": 5},
            {"_id": 3, "v": [25, 20, 15]},
            {"_id": 4, "v": 12},
        ],
        pipeline=[{"$sort": {"v": -1, "_id": 1}}],
        expected=[
            {"_id": 1, "v": [10, 30]},
            {"_id": 3, "v": [25, 20, 15]},
            {"_id": 4, "v": 12},
            {"_id": 2, "v": 5},
        ],
        msg="$sort descending should use the maximum array element as the sort key",
    ),
    StageTestCase(
        "array_key_singleton_equiv_scalar",
        docs=[
            {"_id": 1, "v": [5]},
            {"_id": 2, "v": 5},
            {"_id": 3, "v": 3},
            {"_id": 4, "v": [3]},
            {"_id": 5, "v": 8},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 3, "v": 3},
            {"_id": 4, "v": [3]},
            {"_id": 1, "v": [5]},
            {"_id": 2, "v": 5},
            {"_id": 5, "v": 8},
        ],
        msg="$sort should sort singleton arrays equivalently to their scalar value",
    ),
    StageTestCase(
        "array_key_heterogeneous_asc",
        docs=[
            # Min element is None (null < number < string < boolean).
            {"_id": 5, "v": [1, "hello", None, True]},
            {"_id": 4, "v": None},
            {"_id": 3, "v": 0},
            {"_id": 2, "v": "abc"},
            {"_id": 1, "v": True},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 4, "v": None},
            {"_id": 5, "v": [1, "hello", None, True]},
            {"_id": 3, "v": 0},
            {"_id": 2, "v": "abc"},
            {"_id": 1, "v": True},
        ],
        msg=(
            "$sort ascending should extract null as min from a heterogeneous"
            " array using BSON type ordering"
        ),
    ),
    StageTestCase(
        "array_key_heterogeneous_desc",
        docs=[
            # Max element is True (boolean > string > number > null).
            {"_id": 5, "v": [1, "hello", None, True]},
            {"_id": 4, "v": None},
            {"_id": 3, "v": 0},
            {"_id": 2, "v": "abc"},
            {"_id": 1, "v": True},
        ],
        pipeline=[{"$sort": {"v": -1, "_id": 1}}],
        expected=[
            {"_id": 1, "v": True},
            {"_id": 5, "v": [1, "hello", None, True]},
            {"_id": 2, "v": "abc"},
            {"_id": 3, "v": 0},
            {"_id": 4, "v": None},
        ],
        msg=(
            "$sort descending should extract True as max from a heterogeneous"
            " array using BSON type ordering"
        ),
    ),
    StageTestCase(
        "array_key_large_array_asc",
        docs=[
            {"_id": 1, "v": list(range(50, 150))},
            {"_id": 2, "v": 49},
            {"_id": 3, "v": 51},
            {"_id": 4, "v": 150},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 2, "v": 49},
            {"_id": 1, "v": list(range(50, 150))},
            {"_id": 3, "v": 51},
            {"_id": 4, "v": 150},
        ],
        msg="$sort ascending should correctly extract min from a 100-element array",
    ),
    StageTestCase(
        "array_key_large_array_desc",
        docs=[
            {"_id": 1, "v": list(range(50, 150))},
            {"_id": 2, "v": 49},
            {"_id": 3, "v": 51},
            {"_id": 4, "v": 150},
        ],
        pipeline=[{"$sort": {"v": -1, "_id": 1}}],
        expected=[
            {"_id": 4, "v": 150},
            {"_id": 1, "v": list(range(50, 150))},
            {"_id": 3, "v": 51},
            {"_id": 2, "v": 49},
        ],
        msg="$sort descending should correctly extract max from a 100-element array",
    ),
    StageTestCase(
        "array_key_nested_array_not_unwrapped",
        docs=[
            {"_id": 1, "v": [[1, 2]]},
            {"_id": 2, "v": {"a": 1}},
            {"_id": 3, "v": MaxKey()},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 2, "v": {"a": 1}},
            {"_id": 1, "v": [[1, 2]]},
            {"_id": 3, "v": MaxKey()},
        ],
        msg=(
            "$sort should compare nested arrays as array type rather than"
            " unwrapping to scalar elements"
        ),
    ),
    StageTestCase(
        "array_key_single_bool_true",
        docs=[
            {"_id": 1, "v": [True]},
            {"_id": 2, "v": "abc"},
            {"_id": 3, "v": 5},
            {"_id": 4, "v": True},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 3, "v": 5},
            {"_id": 2, "v": "abc"},
            {"_id": 1, "v": [True]},
            {"_id": 4, "v": True},
        ],
        msg="$sort should place [true] at the boolean BSON type position",
    ),
    StageTestCase(
        "array_key_empty_array_before_null",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2, "v": []},
            {"_id": 3},
            {"_id": 4, "v": MinKey()},
            {"_id": 5, "v": 1},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 4, "v": MinKey()},
            {"_id": 2, "v": []},
            {"_id": 1, "v": None},
            {"_id": 3},
            {"_id": 5, "v": 1},
        ],
        msg="$sort should place empty array before null and missing in ascending order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SORT_ARRAY_KEY_TESTS))
def test_sort_arrays(collection, test_case: StageTestCase):
    """Test $sort array key extraction."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
