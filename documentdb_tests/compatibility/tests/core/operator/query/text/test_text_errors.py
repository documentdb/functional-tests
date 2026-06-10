"""
Tests for $text query operator error cases.

Validates invalid arguments, query restrictions, aggregation restrictions,
and missing index errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INDEX_NOT_FOUND_ERROR,
    MATCH_TEXT_NOT_FIRST_STAGE_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
    NO_SUCH_KEY_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TEXT_FILTER_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="invalid_no_search_field",
        filter={"$text": {}},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Should reject $text with no $search field",
    ),
    QueryTestCase(
        id="invalid_unrecognized_field",
        filter={"$text": {"$search": "word", "$unknown": True}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $text with unrecognized fields",
    ),
    QueryTestCase(
        id="invalid_language_string",
        filter={"$text": {"$search": "word", "$language": "invalidlang"}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject invalid language string",
    ),
    QueryTestCase(
        id="invalid_text_twice_in_and",
        filter={"$and": [{"$text": {"$search": "hello"}}, {"$text": {"$search": "world"}}]},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $text appearing twice in query",
    ),
    QueryTestCase(
        id="invalid_text_inside_not",
        filter={"$not": {"$text": {"$search": "hello"}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $text inside $not",
    ),
    QueryTestCase(
        id="invalid_text_inside_nor",
        filter={"$nor": [{"$text": {"$search": "hello"}}]},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $text inside $nor",
    ),
    QueryTestCase(
        id="invalid_text_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$text": {"$search": "hello"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $text inside $elemMatch",
    ),
    QueryTestCase(
        id="invalid_text_as_field_operator",
        filter={"content": {"$text": {"$search": "hello"}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $text used as field-level operator",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEXT_FILTER_ERROR_TESTS))
def test_text_filter_error(collection, test):
    """Test $text rejects invalid arguments and query placements."""
    collection.create_index([("content", "text")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_text_without_text_index(collection):
    """Test $text query without text index returns error."""
    collection.insert_many([{"_id": 1, "content": "hello world"}])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"$text": {"$search": "hello"}}},
    )
    assertFailureCode(result, INDEX_NOT_FOUND_ERROR, msg="Should require text index")


def test_text_with_hint_object(collection):
    """Test $text query with hint using object format returns error."""
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "hello"}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "hello"}},
            "hint": {"content": "text"},
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Should reject hint with text query")


def test_text_with_natural_sort(collection):
    """Test $text with $natural sort returns error."""
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "hello"}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "hello"}},
            "sort": {"$natural": 1},
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Should reject $natural sort with $text")


def test_text_in_match_non_first_stage(collection):
    """Test $text in $match as non-first stage returns error."""
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "hello"}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"content": 1}},
                {"$match": {"$text": {"$search": "hello"}}},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result, MATCH_TEXT_NOT_FIRST_STAGE_ERROR, msg="Should reject $text in non-first $match"
    )


def test_text_inside_not_in_aggregation(collection):
    """Test $text inside $not in aggregation $match returns error."""
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "hello"}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$not": {"$text": {"$search": "hello"}}}}],
            "cursor": {},
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Should reject $text inside $not in aggregate")


def test_text_in_expr(collection):
    """Test $text inside $expr returns error."""
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "hello"}])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"$expr": {"$text": {"$search": "hello"}}}},
    )
    assertFailureCode(result, UNRECOGNIZED_EXPRESSION_ERROR, msg="Should reject $text inside $expr")


def test_text_multiple_times_in_pipeline(collection):
    """Test $text appearing in multiple $match stages in pipeline returns error."""
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "hello"}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$text": {"$search": "hello"}}},
                {"$match": {"$text": {"$search": "world"}}},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        MATCH_TEXT_NOT_FIRST_STAGE_ERROR,
        msg="Should reject $text in multiple pipeline stages",
    )


def test_text_in_or_with_unindexed_clause(collection):
    """Test $text in $or with a non-indexed clause returns error."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "hello", "status": "active"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$or": [{"$text": {"$search": "hello"}}, {"status": "active"}]},
        },
    )
    assertFailureCode(
        result,
        NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should reject $text in $or with unindexed clause",
    )
