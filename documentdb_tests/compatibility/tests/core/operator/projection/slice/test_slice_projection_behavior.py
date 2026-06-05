"""Tests for $slice projection: inclusion/exclusion, nested paths, and edge cases.

Tests how $slice interacts with projections, nested paths, large arrays, and other operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte

INCLUSION_EXCLUSION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "slice_alone_exclusion",
        projection={"arr": {"$slice": 2}},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5], "title": "test", "count": 10}],
        expected=[{"_id": 1, "arr": [1, 2], "title": "test", "count": 10}],
        msg="$slice alone acts as exclusion — returns all fields with sliced array",
    ),
    ProjectionTestCase(
        "slice_with_inclusion",
        projection={"arr": {"$slice": 2}, "title": 1},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5], "title": "test", "count": 10}],
        expected=[{"_id": 1, "arr": [1, 2], "title": "test"}],
        msg="$slice with field inclusion returns only included fields",
    ),
    ProjectionTestCase(
        "slice_with_exclusion",
        projection={"arr": {"$slice": 2}, "title": 0},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5], "title": "test", "count": 10}],
        expected=[{"_id": 1, "arr": [1, 2], "count": 10}],
        msg="$slice with field exclusion returns all except excluded",
    ),
    ProjectionTestCase(
        "slice_with_id_exclusion",
        projection={"arr": {"$slice": 2}, "_id": 0},
        doc=[{"_id": 1, "arr": [1, 2, 3, 4, 5], "title": "test"}],
        expected=[{"arr": [1, 2], "title": "test"}],
        msg="$slice with _id: 0 should exclude _id",
    ),
    ProjectionTestCase(
        "slice_with_multiple_inclusions",
        projection={"arr": {"$slice": 1}, "a": 1, "b": 1},
        doc=[{"_id": 1, "arr": [1, 2, 3], "a": "x", "b": "y", "c": "z"}],
        expected=[{"_id": 1, "arr": [1], "a": "x", "b": "y"}],
        msg="$slice with multiple inclusions returns only those fields",
    ),
    ProjectionTestCase(
        "slice_multiple_arrays",
        projection={"arr1": {"$slice": 1}, "arr2": {"$slice": -1}},
        doc=[{"_id": 1, "arr1": [1, 2, 3], "arr2": [4, 5, 6], "other": "x"}],
        expected=[{"_id": 1, "arr1": [1], "arr2": [6], "other": "x"}],
        msg="$slice on multiple arrays in same projection should work",
    ),
]

NESTED_PATH_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "nested_array_inclusion",
        projection={"details.colors": {"$slice": 2}, "_id": 1},
        doc=[{"_id": 1, "details": {"colors": ["red", "blue", "green"], "size": "L"}}],
        expected=[{"_id": 1, "details": {"colors": ["red", "blue"]}}],
        msg="$slice on nested array with _id inclusion returns sliced nested field",
    ),
    ProjectionTestCase(
        "nested_array_exclusion",
        projection={"details.colors": {"$slice": 1}},
        doc=[
            {
                "_id": 1,
                "details": {"colors": ["red", "blue", "green"], "size": "L"},
                "x": 1,
            }
        ],
        expected=[{"_id": 1, "details": {"colors": ["red"], "size": "L"}, "x": 1}],
        msg="$slice on nested array alone acts as exclusion, returns all fields",
    ),
    ProjectionTestCase(
        "deeply_nested_path",
        projection={"a.b.c.d.e": {"$slice": 2}},
        doc=[{"_id": 1, "a": {"b": {"c": {"d": {"e": [1, 2, 3, 4, 5]}}}}}],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": {"e": [1, 2]}}}}}],
        msg="$slice on deeply nested path should correctly slice the array",
    ),
    ProjectionTestCase(
        "array_of_arrays_first",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": [[1, 2], [3, 4], [5, 6]]}],
        expected=[{"_id": 1, "arr": [[1, 2]]}],
        msg="$slice: 1 on array of arrays should return first sub-array",
    ),
    ProjectionTestCase(
        "array_of_arrays_last",
        projection={"arr": {"$slice": -1}},
        doc=[{"_id": 1, "arr": [[1, 2], [3, 4], [5, 6]]}],
        expected=[{"_id": 1, "arr": [[5, 6]]}],
        msg="$slice: -1 on array of arrays should return last sub-array",
    ),
    ProjectionTestCase(
        "array_of_arrays_skip_return",
        projection={"arr": {"$slice": [0, 2]}},
        doc=[{"_id": 1, "arr": [[1, 2], [3, 4], [5, 6]]}],
        expected=[{"_id": 1, "arr": [[1, 2], [3, 4]]}],
        msg="$slice: [0, 2] on array of arrays should return first two sub-arrays",
    ),
    ProjectionTestCase(
        "slice_on_array_inside_array_of_documents",
        projection={"items.tags": {"$slice": 1}},
        doc=[
            {
                "_id": 1,
                "items": [
                    {"name": "a", "tags": ["x", "y", "z"]},
                    {"name": "b", "tags": ["p", "q"]},
                ],
            }
        ],
        expected=[
            {
                "_id": 1,
                "items": [
                    {"name": "a", "tags": ["x"]},
                    {"name": "b", "tags": ["p"]},
                ],
            }
        ],
        msg="$slice on nested array in array of documents should slice each",
    ),
    ProjectionTestCase(
        "multiple_slice_shared_prefix",
        projection={"a.b": {"$slice": 1}, "a.c": {"$slice": -1}},
        doc=[{"_id": 1, "a": {"b": [1, 2, 3], "c": [4, 5, 6], "d": "keep"}}],
        expected=[{"_id": 1, "a": {"b": [1], "c": [6], "d": "keep"}}],
        msg="Multiple $slice on nested paths sharing prefix should independently slice each",
    ),
]

EDGE_CASE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "large_array_first_5",
        projection={"arr": {"$slice": 5}},
        doc=[{"_id": 1, "arr": list(range(10000))}],
        expected=[{"_id": 1, "arr": [0, 1, 2, 3, 4]}],
        msg="$slice: 5 on 10000-element array should return first 5",
    ),
    ProjectionTestCase(
        "large_array_last_3",
        projection={"arr": {"$slice": -3}},
        doc=[{"_id": 1, "arr": list(range(10000))}],
        expected=[{"_id": 1, "arr": [9997, 9998, 9999]}],
        msg="$slice: -3 on 10000-element array should return last 3",
    ),
    ProjectionTestCase(
        "large_array_skip_return",
        projection={"arr": {"$slice": [9995, 3]}},
        doc=[{"_id": 1, "arr": list(range(10000))}],
        expected=[{"_id": 1, "arr": [9995, 9996, 9997]}],
        msg="$slice: [9995, 3] on 10000-element array should return elements at end",
    ),
    ProjectionTestCase(
        "multiple_documents",
        projection={"arr": {"$slice": 2}},
        doc=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [4, 5]},
            {"_id": 3, "arr": [6]},
        ],
        expected=[
            {"_id": 1, "arr": [1, 2]},
            {"_id": 2, "arr": [4, 5]},
            {"_id": 3, "arr": [6]},
        ],
        msg="$slice should apply independently to each document",
    ),
    ProjectionTestCase(
        "with_elemMatch_on_different_field",
        projection={"arr1": {"$slice": 1}, "arr2": {"$elemMatch": {"x": 2}}},
        doc=[{"_id": 1, "arr1": [1, 2, 3], "arr2": [{"x": 1}, {"x": 2}, {"x": 3}]}],
        expected=[{"_id": 1, "arr1": [1], "arr2": [{"x": 2}]}],
        msg="$slice with $elemMatch on different field should both work",
    ),
    # When $slice array form contains non-numeric types:
    # - Array as first element triggers expression-form fallthrough
    # - Null in either position yields a null field
    ProjectionTestCase(
        "expression_form_literal_array",
        projection={"arr": {"$slice": [["a", "b", "c"], 2]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": ["a", "b"]}],
        msg="$slice with literal array as first arg falls through to expression form",
    ),
    ProjectionTestCase(
        "expression_form_null_skip",
        projection={"arr": {"$slice": [None, 2]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": None}],
        msg="$slice: [null, 2] returns null — null in array form yields null field",
    ),
    ProjectionTestCase(
        "expression_form_null_limit",
        projection={"arr": {"$slice": [0, None]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        expected=[{"_id": 1, "arr": None}],
        msg="$slice: [0, null] returns null — null in array form yields null field",
    ),
]

ALL_FIND_TESTS = INCLUSION_EXCLUSION_TESTS + NESTED_PATH_TESTS + EDGE_CASE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_FIND_TESTS))
def test_slice_projection_behavior(collection, test: ProjectionTestCase):
    """Test $slice projection behavior with inclusions, nested paths, and edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "projection": test.projection, "sort": {"_id": 1}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


TEXT_INDEX_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "with_meta_textscore",
        projection={"arr": {"$slice": 2}, "score": {"$meta": "textScore"}},
        doc=[{"_id": 1, "text": "hello world", "arr": [1, 2, 3, 4, 5]}],
        expected={"arr": Eq([1, 2]), "score": Gte(0)},
        msg="$slice and $meta textScore should coexist in projection",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEXT_INDEX_TESTS))
def test_slice_with_text_index(collection, test: ProjectionTestCase):
    """Test $slice coexists with $meta textScore in projection."""
    collection.create_index([("text", "text")])
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "hello"}},
            "projection": test.projection,
        },
    )
    assertProperties(result, test.expected, msg=test.msg)


def test_slice_in_findAndModify(collection):
    """Test $slice projection works in findAndModify (not just find)."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3, 4, 5]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"touched": True}},
            "fields": {"arr": {"$slice": 1}},
        },
    )
    assertResult(
        result,
        expected={"value": {"arr": Eq([1])}},
        raw_res=True,
        msg="$slice projection should apply in findAndModify",
    )


def test_slice_in_findAndModify_new_returns_modified(collection):
    """Test $slice applies to the post-update document when new: true."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$push": {"arr": 4}},
            "new": True,
            "fields": {"arr": {"$slice": -2}},
        },
    )
    assertResult(
        result,
        expected={"value": {"arr": Eq([3, 4])}},
        raw_res=True,
        msg="$slice should apply to the modified array when new: true",
    )


def test_slice_in_findAndModify_remove(collection):
    """Test $slice applies to the returned document when remove: true."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3, 4, 5]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "remove": True,
            "fields": {"arr": {"$slice": 2}},
        },
    )
    assertResult(
        result,
        expected={"value": {"arr": Eq([1, 2])}},
        raw_res=True,
        msg="$slice should apply to the removed document when remove: true",
    )
