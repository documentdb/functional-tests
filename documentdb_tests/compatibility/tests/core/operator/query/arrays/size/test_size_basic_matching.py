"""
Tests for $size basic matching behavior.

Covers empty arrays, array content independence, nested arrays, arrays of objects,
arrays of empty arrays, mixed types, and multiple document size discrimination.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EMPTY_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="size_0_matches_empty",
        filter={"a": {"$size": 0}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": []}],
        msg="$size 0 matches empty arrays",
    ),
    QueryTestCase(
        id="size_1_no_match_empty",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": []}],
        expected=[],
        msg="$size 1 does not match empty array",
    ),
]

CONTENT_INDEPENDENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_array",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$size 2 matches [1, 2]",
    ),
    QueryTestCase(
        id="string_array",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": ["a", "b"]}],
        expected=[{"_id": 1, "a": ["a", "b"]}],
        msg="$size 2 matches ['a', 'b']",
    ),
    QueryTestCase(
        id="null_array",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": [None, None]}],
        expected=[{"_id": 1, "a": [None, None]}],
        msg="$size 2 matches [null, null]",
    ),
    QueryTestCase(
        id="mixed_obj_array",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": [{}, []]}],
        expected=[{"_id": 1, "a": [{}, []]}],
        msg="$size 2 matches [{}, []]",
    ),
    QueryTestCase(
        id="mixed_types_4",
        filter={"a": {"$size": 4}},
        doc=[{"_id": 1, "a": [1, "a", True, None]}],
        expected=[{"_id": 1, "a": [1, "a", True, None]}],
        msg="$size 4 matches mixed-type array",
    ),
    QueryTestCase(
        id="false_and_zero_distinct",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": [False, 0]}],
        expected=[{"_id": 1, "a": [False, 0]}],
        msg="$size counts false and 0 as distinct elements",
    ),
    QueryTestCase(
        id="duplicate_elements",
        filter={"a": {"$size": 3}},
        doc=[{"_id": 1, "a": [1, 1, 1]}],
        expected=[{"_id": 1, "a": [1, 1, 1]}],
        msg="$size 3 matches [1, 1, 1] with duplicate elements",
    ),
    QueryTestCase(
        id="null_single_element",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": [None]}],
        expected=[{"_id": 1, "a": [None]}],
        msg="$size 1 matches [null]",
    ),
]

NESTED_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nested_2_top_level",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        expected=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        msg="$size 2 matches [[1,2],[3,4]] (2 top-level elements)",
    ),
    QueryTestCase(
        id="nested_1_top_level",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": [[1, 2, 3]]}],
        expected=[{"_id": 1, "a": [[1, 2, 3]]}],
        msg="$size 1 matches [[1,2,3]] (1 top-level element)",
    ),
    QueryTestCase(
        id="mixed_nested_3",
        filter={"a": {"$size": 3}},
        doc=[{"_id": 1, "a": [1, [2, 3], 4]}],
        expected=[{"_id": 1, "a": [1, [2, 3], 4]}],
        msg="$size 3 matches [1, [2,3], 4]",
    ),
]

ARRAY_OF_OBJECTS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="two_objects",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": [{"x": 1}, {"y": 2}]}],
        expected=[{"_id": 1, "a": [{"x": 1}, {"y": 2}]}],
        msg="$size 2 matches [{x:1},{y:2}]",
    ),
    QueryTestCase(
        id="one_large_object",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": [{"x": 1, "y": 2, "z": 3}]}],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2, "z": 3}]}],
        msg="$size 1 matches single object regardless of object size",
    ),
]

ARRAY_OF_EMPTY_ARRAYS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="two_empty_arrays",
        filter={"a": {"$size": 2}},
        doc=[{"_id": 1, "a": [[], []]}],
        expected=[{"_id": 1, "a": [[], []]}],
        msg="$size 2 matches [[], []]",
    ),
    QueryTestCase(
        id="one_empty_array",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": [[]]}],
        expected=[{"_id": 1, "a": [[]]}],
        msg="$size 1 matches [[]]",
    ),
]

MULTI_DOC_DISCRIMINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="size_no_match_4",
        filter={"a": {"$size": 4}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [1]},
        ],
        expected=[],
        msg="$size 4 returns no matches when no array has 4 elements",
    ),
    QueryTestCase(
        id="size_10000_large_array",
        filter={"a": {"$size": 10000}},
        doc=[{"_id": 1, "a": list(range(10000))}],
        expected=[{"_id": 1, "a": list(range(10000))}],
        msg="$size 10000 matches large array",
    ),
]

ALL_TESTS = (
    EMPTY_ARRAY_TESTS
    + CONTENT_INDEPENDENCE_TESTS
    + NESTED_ARRAY_TESTS
    + ARRAY_OF_OBJECTS_TESTS
    + ARRAY_OF_EMPTY_ARRAYS_TESTS
    + MULTI_DOC_DISCRIMINATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_size_basic_matching(collection, test):
    """Parametrized test for $size basic matching behavior."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
