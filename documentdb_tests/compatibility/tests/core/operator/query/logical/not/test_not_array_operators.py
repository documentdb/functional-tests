"""
Tests for $not query operator with array fields and array operators.

Covers $not with $elemMatch, $all, $in on arrays, element-wise matching
behavior on array fields, and dot notation access to array elements.
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
        id="array_element_matches_not_returned",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": [1, 15, 20]}],
        expected=[],
        msg="$not $gt:10 on array with elements > 10 should NOT return doc",
    ),
    QueryTestCase(
        id="array_no_element_matches_returned",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": [1, 2, 3]}],
        expected=[{"_id": 1, "val": [1, 2, 3]}],
        msg="$not $gt:10 on array with no elements > 10 should return doc",
    ),
    QueryTestCase(
        id="array_eq_element_match",
        filter={"val": {"$not": {"$eq": 2}}},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": [4, 5, 6]}],
        expected=[{"_id": 2, "val": [4, 5, 6]}],
        msg="$not $eq:2 on array should NOT return doc containing 2",
    ),
    QueryTestCase(
        id="empty_array_not_gt",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=[{"_id": 1, "val": []}],
        expected=[{"_id": 1, "val": []}],
        msg="$not $gt:10 on empty array should return doc (no element matches)",
    ),
    QueryTestCase(
        id="nested_array_eq",
        filter={"val": {"$not": {"$eq": [1, 2]}}},
        doc=[{"_id": 1, "val": [[1, 2], [3, 4]]}, {"_id": 2, "val": [[5, 6]]}],
        expected=[{"_id": 2, "val": [[5, 6]]}],
        msg="$not $eq:[1,2] on nested array should NOT return doc with [1,2] element",
    ),
]

ARRAY_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_in_on_array_field",
        filter={"val": {"$not": {"$in": [2, 4]}}},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": [5, 6, 7]}],
        expected=[{"_id": 2, "val": [5, 6, 7]}],
        msg="$not $in on array field should exclude docs with any matching element",
    ),
    QueryTestCase(
        id="not_all_on_array_field",
        filter={"tags": {"$not": {"$all": ["a", "b"]}}},
        doc=[
            {"_id": 1, "tags": ["a", "b", "c"]},
            {"_id": 2, "tags": ["a", "d"]},
            {"_id": 3, "tags": ["x", "y"]},
        ],
        expected=[{"_id": 2, "tags": ["a", "d"]}, {"_id": 3, "tags": ["x", "y"]}],
        msg="$not $all should return docs that do NOT contain all specified elements",
    ),
    QueryTestCase(
        id="not_elemMatch_compound",
        filter={"val": {"$not": {"$elemMatch": {"$gt": 5, "$lt": 10}}}},
        doc=[
            {"_id": 1, "val": [1, 7, 20]},
            {"_id": 2, "val": [1, 2, 3]},
            {"_id": 3, "val": [10, 20]},
        ],
        expected=[{"_id": 2, "val": [1, 2, 3]}, {"_id": 3, "val": [10, 20]}],
        msg="$not $elemMatch should return docs where no element satisfies both conditions",
    ),
]

DOT_NOTATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_on_array_element_by_index",
        filter={"arr.0": {"$not": {"$eq": 1}}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [4, 5, 6]}],
        expected=[{"_id": 2, "arr": [4, 5, 6]}],
        msg="$not on array element by index should check specific position",
    ),
    QueryTestCase(
        id="not_on_field_within_array_of_objects",
        filter={"items.qty": {"$not": {"$gt": 10}}},
        doc=[
            {"_id": 1, "items": [{"qty": 5}, {"qty": 15}]},
            {"_id": 2, "items": [{"qty": 3}, {"qty": 7}]},
        ],
        expected=[{"_id": 2, "items": [{"qty": 3}, {"qty": 7}]}],
        msg="$not on nested array path should check element-wise",
    ),
]

ALL_TESTS = ARRAY_FIELD_TESTS + ARRAY_OPERATOR_TESTS + DOT_NOTATION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_array_operators(collection, test):
    """Test $not query operator with array fields and array operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
