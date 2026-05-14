"""
Tests for $regex query operator on array fields.

Covers $regex matching on arrays of strings, mixed-type arrays, empty arrays,
arrays with no string elements, and arrays with multiple matching elements
(document returned once).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_of_strings_matches_element",
        filter={"a": {"$regex": "^abc"}},
        doc=[
            {"_id": 1, "a": ["abc123", "def456"]},
            {"_id": 2, "a": ["xyz"]},
        ],
        expected=[{"_id": 1, "a": ["abc123", "def456"]}],
        msg="$regex should match if any array element matches",
    ),
    QueryTestCase(
        id="array_mixed_types_matches_string",
        filter={"a": {"$regex": "abc"}},
        doc=[{"_id": 1, "a": ["abc", 1, None]}, {"_id": 2, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": ["abc", 1, None]}],
        msg="$regex on mixed-type array should match string element",
    ),
    QueryTestCase(
        id="array_no_strings_no_match",
        filter={"a": {"$regex": "1"}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": "1"}],
        expected=[{"_id": 2, "a": "1"}],
        msg="$regex on array with no string elements should not match",
    ),
    QueryTestCase(
        id="empty_array_no_match",
        filter={"a": {"$regex": ".*"}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex on empty array should not match",
    ),
    QueryTestCase(
        id="multiple_matching_elements_returned_once",
        filter={"a": {"$regex": "^abc"}},
        doc=[{"_id": 1, "a": ["abc1", "abc2"]}, {"_id": 2, "a": ["xyz"]}],
        expected=[{"_id": 1, "a": ["abc1", "abc2"]}],
        msg="$regex with multiple matching array elements should return doc once",
    ),
    QueryTestCase(
        id="nested_array_no_match",
        filter={"a": {"$regex": "abc"}},
        doc=[{"_id": 1, "a": [["abc"]]}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex on nested array [[abc]] should not match (no string element at top level)",
    ),
]

ALL_TESTS = ARRAY_MATCHING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_regex_arrays(collection, test):
    """Parametrized test for $regex on array fields."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
