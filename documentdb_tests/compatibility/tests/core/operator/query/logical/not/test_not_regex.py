"""
Tests for $not query operator with regex patterns.

Covers $not with regex literals, $regex operator, $options,
missing field behavior with regex, and regex in logical combinations.
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

REGEX_BASIC_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_regex_operator_excludes_match",
        filter={"title": {"$not": {"$regex": "^T"}}},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}],
        expected=[{"_id": 2, "title": "Hello"}],
        msg="$not with $regex should exclude documents matching the pattern",
    ),
    QueryTestCase(
        id="not_regex_literal",
        filter={"title": {"$not": Regex("^T")}},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}],
        expected=[{"_id": 2, "title": "Hello"}],
        msg="$not with regex literal should exclude documents matching the pattern",
    ),
    QueryTestCase(
        id="not_regex_with_options_case_insensitive",
        filter={"title": {"$not": {"$regex": "^t", "$options": "i"}}},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}],
        expected=[{"_id": 2, "title": "Hello"}],
        msg="$not with $regex and $options:i should exclude case-insensitive matches",
    ),
    QueryTestCase(
        id="not_regex_includes_missing_field",
        filter={"title": {"$not": {"$regex": "^T"}}},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "title": "Hello"}, {"_id": 3, "other": 1}],
        msg="$not with regex should include documents where field is missing",
    ),
    QueryTestCase(
        id="not_regex_non_string_field",
        filter={"val": {"$not": {"$regex": "^h"}}},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": 123}, {"_id": 3, "val": "world"}],
        expected=[{"_id": 2, "val": 123}, {"_id": 3, "val": "world"}],
        msg="$not with regex on non-string field should include non-string docs",
    ),
    QueryTestCase(
        id="not_regex_no_match_returns_all",
        filter={"title": {"$not": {"$regex": "^Z"}}},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}],
        expected=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}],
        msg="$not with non-matching regex should return all documents",
    ),
]

REGEX_LOGICAL_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_regex_inside_and",
        filter={"$and": [{"title": {"$not": {"$regex": "^T"}}}, {"title": {"$exists": True}}]},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "title": "Hello"}],
        msg="$not regex inside $and with $exists should filter correctly",
    ),
    QueryTestCase(
        id="not_regex_inside_or",
        filter={"$or": [{"title": {"$not": {"$regex": "^T"}}}, {"val": 1}]},
        doc=[
            {"_id": 1, "title": "Test"},
            {"_id": 2, "title": "Hello"},
            {"_id": 3, "val": 1},
        ],
        expected=[{"_id": 2, "title": "Hello"}, {"_id": 3, "val": 1}],
        msg="$not regex inside $or should combine with other conditions",
    ),
    QueryTestCase(
        id="nor_regex_equivalent_to_not",
        filter={"$nor": [{"title": {"$regex": "^T"}}]},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}, {"_id": 3, "other": 1}],
        expected=[{"_id": 2, "title": "Hello"}, {"_id": 3, "other": 1}],
        msg="$nor with regex should produce same results as $not with regex",
    ),
]

REGEX_TYPED_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_regex_on_regex_typed_field",
        filter={"val": {"$not": {"$regex": "abc"}}},
        doc=[{"_id": 1, "val": Regex("abc")}, {"_id": 2, "val": Regex("xyz")}],
        expected=[{"_id": 2, "val": Regex("xyz")}],
        msg="$not regex on regex-typed field should exclude matching regex values",
    ),
]

ALL_TESTS = REGEX_BASIC_TESTS + REGEX_LOGICAL_COMBINATION_TESTS + REGEX_TYPED_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_regex(collection, test):
    """Test $not query operator with regex patterns."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
