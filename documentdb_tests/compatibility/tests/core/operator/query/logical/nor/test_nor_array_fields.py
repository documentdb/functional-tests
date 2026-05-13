"""
Tests for $nor query operator with array fields.

Covers element matching in arrays, nested array paths, empty arrays,
arrays of objects with dot notation, and $elemMatch on arrays of objects.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="element_matches_in_array",
        filter={"$nor": [{"val": 1}]},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": [4, 5, 6]}],
        expected=[{"_id": 2, "val": [4, 5, 6]}],
        msg="$nor should exclude docs where array contains matching element",
    ),
    QueryTestCase(
        id="no_element_matches_in_array",
        filter={"$nor": [{"val": 1}]},
        doc=[{"_id": 1, "val": [4, 5, 6]}, {"_id": 2, "val": [7, 8]}],
        expected=[{"_id": 1, "val": [4, 5, 6]}, {"_id": 2, "val": [7, 8]}],
        msg="$nor should return docs where array does not contain matching element",
    ),
    QueryTestCase(
        id="empty_array_with_size",
        filter={"$nor": [{"val": {"$size": 0}}]},
        doc=[{"_id": 1, "val": []}, {"_id": 2, "val": [1]}],
        expected=[{"_id": 2, "val": [1]}],
        msg="$nor with $size:0 should exclude docs with empty array",
    ),
    QueryTestCase(
        id="nested_arrays",
        filter={"$nor": [{"val": [1, 2]}]},
        doc=[{"_id": 1, "val": [[1, 2], [3, 4]]}, {"_id": 2, "val": [[5, 6]]}],
        expected=[{"_id": 2, "val": [[5, 6]]}],
        msg="$nor should exclude docs where nested array contains matching sub-array",
    ),
    QueryTestCase(
        id="array_of_objects_dot_notation",
        filter={"$nor": [{"items.x": 1}]},
        doc=[
            {"_id": 1, "items": [{"x": 1}, {"x": 2}]},
            {"_id": 2, "items": [{"x": 3}, {"x": 4}]},
        ],
        expected=[{"_id": 2, "items": [{"x": 3}, {"x": 4}]}],
        msg="$nor with dot notation on array of objects should exclude matching docs",
    ),
    QueryTestCase(
        id="nested_array_path",
        filter={"$nor": [{"arr.field": "value"}]},
        doc=[
            {"_id": 1, "arr": [{"field": "value"}, {"field": "other"}]},
            {"_id": 2, "arr": [{"field": "other"}]},
        ],
        expected=[{"_id": 2, "arr": [{"field": "other"}]}],
        msg="$nor with nested array path should exclude docs with matching element",
    ),
    QueryTestCase(
        id="elemMatch_on_array_of_objects",
        filter={"$nor": [{"items": {"$elemMatch": {"qty": {"$gt": 5}, "price": {"$lt": 10}}}}]},
        doc=[
            {"_id": 1, "items": [{"qty": 10, "price": 5}]},
            {"_id": 2, "items": [{"qty": 3, "price": 5}]},
        ],
        expected=[{"_id": 2, "items": [{"qty": 3, "price": 5}]}],
        msg="$nor with $elemMatch on array of objects should exclude matching docs",
    ),
    QueryTestCase(
        id="all_on_array",
        filter={"$nor": [{"tags": {"$all": ["a", "b"]}}]},
        doc=[
            {"_id": 1, "tags": ["a", "b", "c"]},
            {"_id": 2, "tags": ["a", "c"]},
        ],
        expected=[{"_id": 2, "tags": ["a", "c"]}],
        msg="$nor with $all should exclude docs where array contains all specified elements",
    ),
]

ALL_TESTS = ARRAY_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_array_fields(collection, test):
    """Test $nor query operator with array fields."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
