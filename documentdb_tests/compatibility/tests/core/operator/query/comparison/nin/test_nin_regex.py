"""
Tests for $nin with regex values.

Covers regex exclusion on scalar strings, case-insensitive flag, multiline flag,
no-flag default behavior, multiple regexes, mixed regex/literal values,
regex on array fields, and $regex expression rejection.
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SUCCESS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="regex_excludes_matching_string",
        filter={"a": {"$nin": [Regex("^a")]}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 2, "a": "xyz"}],
        msg="$nin with regex excludes doc where string matches pattern",
    ),
    QueryTestCase(
        id="regex_includes_non_matching_string",
        filter={"a": {"$nin": [Regex("^a")]}},
        doc=[{"_id": 1, "a": "xyz"}],
        expected=[{"_id": 1, "a": "xyz"}],
        msg="$nin with regex includes doc where string does not match pattern",
    ),
    QueryTestCase(
        id="regex_case_insensitive_excludes",
        filter={"a": {"$nin": [Regex("abc", "i")]}},
        doc=[{"_id": 1, "a": "ABC"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 2, "a": "xyz"}],
        msg="$nin with case-insensitive regex excludes matching doc",
    ),
    QueryTestCase(
        id="regex_no_flag_is_case_sensitive",
        filter={"a": {"$nin": [Regex("^abc")]}},
        doc=[{"_id": 1, "a": "abcdef"}, {"_id": 2, "a": "ABCdef"}],
        expected=[{"_id": 2, "a": "ABCdef"}],
        msg="$nin with regex without flags is case-sensitive by default",
    ),
    QueryTestCase(
        id="regex_multiline_flag",
        filter={"a": {"$nin": [Regex("^abc", "m")]}},
        doc=[{"_id": 1, "a": "hello\nabcdef"}, {"_id": 2, "a": "hello\nxyz"}],
        expected=[{"_id": 2, "a": "hello\nxyz"}],
        msg="$nin with regex using multiline flag excludes match after newline",
    ),
    QueryTestCase(
        id="regex_multiple_patterns",
        filter={"a": {"$nin": [Regex("^a"), Regex("^b")]}},
        doc=[
            {"_id": 1, "a": "apple"},
            {"_id": 2, "a": "banana"},
            {"_id": 3, "a": "cherry"},
        ],
        expected=[{"_id": 3, "a": "cherry"}],
        msg="$nin with multiple regexes excludes all matching",
    ),
    QueryTestCase(
        id="regex_and_literal_mixed",
        filter={"a": {"$nin": [Regex("^a"), "xyz"]}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "xyz"}, {"_id": 3, "a": "def"}],
        expected=[{"_id": 3, "a": "def"}],
        msg="$nin with regex and literal excludes both regex and literal matches",
    ),
    QueryTestCase(
        id="regex_array_element_matches_excludes",
        filter={"a": {"$nin": [Regex("^a")]}},
        doc=[{"_id": 1, "a": ["abc", "def"]}, {"_id": 2, "a": ["xyz", "def"]}],
        expected=[{"_id": 2, "a": ["xyz", "def"]}],
        msg="$nin with regex excludes doc when array element matches",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUCCESS_TESTS))
def test_nin_regex(collection, test_case):
    """Parametrized test for $nin with regex values."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)


ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="dollar_regex_expression_rejected",
        filter={"a": {"$nin": [{"$regex": "^abc"}]}},
        doc=[{"_id": 1, "a": "abcdef"}],
        error_code=BAD_VALUE_ERROR,
        msg="$nin with $regex expression inside array returns error",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ERROR_TESTS))
def test_nin_regex_errors(collection, test_case):
    """Parametrized test for $nin regex error cases."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertFailureCode(result, test_case.error_code, test_case.msg)
