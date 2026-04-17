"""
Tests for $nin array matching behavior.

Covers element match exclusion, nested arrays, empty arrays,
array element order, mixed scalar/array fields, null in arrays,
and embedded document matching in arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_no_element_match_includes",
        filter={"a": {"$nin": [4, 5]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$nin includes doc when array has no matching element",
    ),
    QueryTestCase(
        id="array_partial_overlap_excludes",
        filter={"a": {"$nin": [3, 4, 5]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[],
        msg="$nin excludes doc when array has partial overlap with $nin values",
    ),
    QueryTestCase(
        id="array_multiple_values_one_matches",
        filter={"a": {"$nin": [1, 4]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[],
        msg="$nin excludes doc when any $nin value matches array element",
    ),
    QueryTestCase(
        id="nested_array_scalar_no_match",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        expected=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        msg="$nin scalar against nested array — no top-level element equals scalar",
    ),
    QueryTestCase(
        id="array_order_matters_different_order_matches",
        filter={"a": {"$nin": [[2, 1]]}},
        doc=[{"_id": 1, "a": [[1, 2]]}],
        expected=[{"_id": 1, "a": [[1, 2]]}],
        msg="$nin: [1,2] != [2,1] — different order matches",
    ),
    QueryTestCase(
        id="array_order_matters_same_order_excluded",
        filter={"a": {"$nin": [[1, 2]]}},
        doc=[{"_id": 1, "a": [[1, 2]]}],
        expected=[],
        msg="$nin: [1,2] == [1,2] — same order excluded",
    ),
    QueryTestCase(
        id="array_without_null_matches_null_nin",
        filter={"a": {"$nin": [None]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$nin [null] matches doc when array does not contain null",
    ),
    QueryTestCase(
        id="array_element_match_excludes",
        filter={"a": {"$nin": [2]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [4, 5]}],
        expected=[{"_id": 2, "a": [4, 5]}],
        msg="$nin excludes doc when array contains matching element",
    ),
    QueryTestCase(
        id="empty_array_field_matches",
        filter={"a": {"$nin": [1, 2]}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": []}],
        msg="$nin matches doc with empty array field (no elements to match)",
    ),
    QueryTestCase(
        id="empty_array_in_nin_list_excludes_empty_array",
        filter={"a": {"$nin": [[]]}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 2, "a": [1]}],
        msg="$nin with empty array in list excludes doc with empty array field",
    ),
    QueryTestCase(
        id="nested_array_element_match",
        filter={"a": {"$nin": [[1, 2]]}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}, {"_id": 2, "a": [[5, 6]]}],
        expected=[{"_id": 2, "a": [[5, 6]]}],
        msg="$nin with nested array — excludes when top-level element matches",
    ),
    QueryTestCase(
        id="array_with_null_element_excluded_by_null",
        filter={"a": {"$nin": [None]}},
        doc=[{"_id": 1, "a": [1, None, 3]}, {"_id": 2, "a": [1, 2, 3]}],
        expected=[{"_id": 2, "a": [1, 2, 3]}],
        msg="$nin [null] excludes doc when array contains null",
    ),
    QueryTestCase(
        id="array_of_objects_element_match",
        filter={"a": {"$nin": [{"x": 1}]}},
        doc=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}, {"_id": 2, "a": [{"x": 3}]}],
        expected=[{"_id": 2, "a": [{"x": 3}]}],
        msg="$nin excludes doc when array contains matching object element",
    ),
    QueryTestCase(
        id="duplicate_values_with_array_field",
        filter={"a": {"$nin": [1, 1, 1]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [4, 5]}],
        expected=[{"_id": 2, "a": [4, 5]}],
        msg="$nin with duplicate values against array field behaves same as single",
    ),
    QueryTestCase(
        id="mixed_scalar_and_array",
        filter={"a": {"$nin": [1]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [3, 4]},
            {"_id": 4, "a": 5},
        ],
        expected=[{"_id": 3, "a": [3, 4]}, {"_id": 4, "a": 5}],
        msg="$nin with mixed scalar and array fields",
    ),
    QueryTestCase(
        id="array_of_objects_no_match_includes",
        filter={"a": {"$nin": [{"x": 3}]}},
        doc=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}],
        expected=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}],
        msg="$nin includes doc when array has no matching object element",
    ),
    QueryTestCase(
        id="object_key_order_no_exclude",
        filter={"a": {"$nin": [{"b": 2, "a": 1}]}},
        doc=[{"_id": 1, "a": [{"a": 1, "b": 2}]}],
        expected=[{"_id": 1, "a": [{"a": 1, "b": 2}]}],
        msg="$nin with object different key order does NOT exclude (BSON key order matters)",
    ),
    QueryTestCase(
        id="object_extra_keys_no_exclude",
        filter={"a": {"$nin": [{"a": 1}]}},
        doc=[{"_id": 1, "a": [{"a": 1, "b": 2}]}],
        expected=[{"_id": 1, "a": [{"a": 1, "b": 2}]}],
        msg="$nin with object does NOT exclude object with extra keys",
    ),
    QueryTestCase(
        id="empty_object_excludes",
        filter={"a": {"$nin": [{}]}},
        doc=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"a": 1}}],
        expected=[{"_id": 2, "a": {"a": 1}}],
        msg="$nin with empty object excludes empty object",
    ),
    QueryTestCase(
        id="object_key_order_scalar_no_exclude",
        filter={"a": {"$nin": [{"b": 2, "a": 1}]}},
        doc=[{"_id": 1, "a": {"a": 1, "b": 2}}],
        expected=[{"_id": 1, "a": {"a": 1, "b": 2}}],
        msg="$nin with object different key order on scalar field does NOT exclude",
    ),
    QueryTestCase(
        id="array_partial_value_no_exclude",
        filter={"a": {"$nin": [[1]]}},
        doc=[{"_id": 1, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$nin with partial array value does NOT exclude",
    ),
    QueryTestCase(
        id="array_exact_value_excludes",
        filter={"a": {"$nin": [[1, 2]]}},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [3, 4]}],
        expected=[{"_id": 2, "a": [3, 4]}],
        msg="$nin with array value excludes exact array field",
    ),
    QueryTestCase(
        id="nin_array_order_independence",
        filter={"a": {"$nin": [3, 1]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        expected=[{"_id": 2, "a": 2}],
        msg="$nin excludes regardless of value order in the array",
    ),
    QueryTestCase(
        id="dotted_path_array_of_objects",
        filter={"a.b": {"$nin": [1]}},
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}],
        expected=[{"_id": 2, "a": [{"b": 3}]}],
        msg="$nin on dotted path into array of objects excludes matching",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_nin_array_matching(collection, test_case):
    """Parametrized test for $nin array matching behavior."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, ignore_doc_order=True)
