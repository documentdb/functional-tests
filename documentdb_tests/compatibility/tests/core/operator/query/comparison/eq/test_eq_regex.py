"""
Tests for $eq regular expression behavior.

Covers the key difference: explicit $eq matches only stored regex objects,
while implicit regex performs a pattern match against strings.
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="regex_matches_stored_regex",
        filter={"a": {"$eq": Regex("abc")}},
        doc=[{"_id": 1, "a": Regex("abc")}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 1, "a": Regex("abc")}],
        msg="$eq with regex matches stored regex object with same pattern and flags",
    ),
    QueryTestCase(
        id="case_insensitive_matches_stored_with_same_flags",
        filter={"a": {"$eq": Regex("abc", "i")}},
        doc=[{"_id": 1, "a": Regex("abc", "i")}, {"_id": 2, "a": Regex("abc")}],
        expected=[{"_id": 1, "a": Regex("abc", "i")}],
        msg="$eq with case-insensitive regex matches stored regex with same flags",
    ),
    QueryTestCase(
        id="implicit_regex_matches_string_substring",
        filter={"a": Regex("abc")},
        doc=[{"_id": 1, "a": "abcdef"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 1, "a": "abcdef"}],
        msg="Implicit regex matches string containing pattern",
    ),
    QueryTestCase(
        id="implicit_regex_anchored",
        filter={"a": Regex("^abc$")},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "abcdef"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="Implicit regex with anchors matches exact string",
    ),
    QueryTestCase(
        id="regex_does_not_match_string",
        filter={"a": {"$eq": Regex("abc")}},
        doc=[{"_id": 1, "a": "abc"}],
        expected=[],
        msg="$eq with regex does NOT match string value",
    ),
    QueryTestCase(
        id="case_insensitive_does_not_match_string",
        filter={"a": {"$eq": Regex("abc", "i")}},
        doc=[{"_id": 1, "a": "ABC"}],
        expected=[],
        msg="$eq with case-insensitive regex does NOT match string",
    ),
    QueryTestCase(
        id="flag_mismatch_no_match",
        filter={"a": {"$eq": Regex("abc")}},
        doc=[{"_id": 1, "a": Regex("abc", "i")}],
        expected=[],
        msg="$eq with regex does NOT match stored regex with different flags",
    ),
    QueryTestCase(
        id="different_pattern_no_match",
        filter={"a": {"$eq": Regex("abc")}},
        doc=[{"_id": 1, "a": Regex("abcd")}],
        expected=[],
        msg="$eq with regex does NOT match stored regex with different pattern",
    ),
    QueryTestCase(
        id="implicit_regex_matches_string_and_equal_stored_regex",
        filter={"a": Regex("abc")},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": Regex("abc")}],
        expected=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": Regex("abc")}],
        msg="Implicit regex matches a pattern-matching string and an equal stored regex",
    ),
    QueryTestCase(
        id="implicit_regex_does_not_match_number",
        filter={"a": Regex("123")},
        doc=[{"_id": 1, "a": 123}],
        expected=[],
        msg="Implicit regex does NOT match non-string types",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_eq_regex(collection, test):
    """Parametrized test for $eq regex behavior."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
