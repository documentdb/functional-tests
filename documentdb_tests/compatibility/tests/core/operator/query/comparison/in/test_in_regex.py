"""
Tests for $in query operator with regular expressions.

Covers basic regex matching, case-insensitive flag, multiline flag,
no-flag default behavior, multiple regexes, mixed regex/literal,
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
        id="regex_basic_match",
        filter={"x": {"$in": [Regex("^abc")]}},
        doc=[{"_id": 1, "x": "abcdef"}, {"_id": 2, "x": "xyz"}],
        expected=[{"_id": 1, "x": "abcdef"}],
        msg="$in with regex matches string",
    ),
    QueryTestCase(
        id="regex_basic_no_match",
        filter={"x": {"$in": [Regex("^abc")]}},
        doc=[{"_id": 1, "x": "defabc"}],
        expected=[],
        msg="$in with regex does NOT match non-matching string",
    ),
    QueryTestCase(
        id="regex_case_insensitive_flag",
        filter={"x": {"$in": [Regex("^abc", "i")]}},
        doc=[{"_id": 1, "x": "ABCdef"}, {"_id": 2, "x": "xyz"}],
        expected=[{"_id": 1, "x": "ABCdef"}],
        msg="$in with case-insensitive regex matches",
    ),
    QueryTestCase(
        id="regex_no_flag_is_case_sensitive",
        filter={"x": {"$in": [Regex("^abc")]}},
        doc=[{"_id": 1, "x": "abcdef"}, {"_id": 2, "x": "ABCdef"}],
        expected=[{"_id": 1, "x": "abcdef"}],
        msg="$in with regex without flags is case-sensitive by default",
    ),
    QueryTestCase(
        id="regex_multiline_flag",
        filter={"x": {"$in": [Regex("^abc", "m")]}},
        doc=[{"_id": 1, "x": "hello\nabcdef"}, {"_id": 2, "x": "hello\nxyz"}],
        expected=[{"_id": 1, "x": "hello\nabcdef"}],
        msg="$in with regex using multiline flag matches after newline",
    ),
    QueryTestCase(
        id="regex_multiple_patterns",
        filter={"x": {"$in": [Regex("^a"), Regex("^b")]}},
        doc=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
            {"_id": 3, "x": "cherry"},
        ],
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "banana"}],
        msg="$in with multiple regexes",
    ),
    QueryTestCase(
        id="regex_mixed_with_literal",
        filter={"x": {"$in": [Regex("^a"), "banana"]}},
        doc=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
            {"_id": 3, "x": "cherry"},
        ],
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "banana"}],
        msg="$in with mix of regex and literal",
    ),
    QueryTestCase(
        id="regex_matches_array_element",
        filter={"x": {"$in": [Regex("^abc")]}},
        doc=[{"_id": 1, "x": ["abcdef", "xyz"]}, {"_id": 2, "x": ["xyz"]}],
        expected=[{"_id": 1, "x": ["abcdef", "xyz"]}],
        msg="$in with regex matches element in array field",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUCCESS_TESTS))
def test_in_regex(collection, test_case):
    """Parametrized test for $in operator regex matching."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)


ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="dollar_regex_expression_rejected",
        filter={"x": {"$in": [{"$regex": "^abc"}]}},
        doc=[{"_id": 1, "x": "abcdef"}],
        error_code=BAD_VALUE_ERROR,
        msg="$in with $regex expression inside array returns error",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ERROR_TESTS))
def test_in_regex_errors(collection, test_case):
    """Parametrized test for $in operator regex error cases."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertFailureCode(result, test_case.error_code, test_case.msg)
