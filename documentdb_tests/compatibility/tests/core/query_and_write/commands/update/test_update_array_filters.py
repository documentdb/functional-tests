"""
Tests for update command arrayFilters option.

Validates array element filtering with identifiers, nested arrays,
and error cases for invalid filter configurations.
"""

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    NEAR_NOT_ALLOWED_ERROR,
)
from documentdb_tests.framework.executor import execute_command


def test_update_array_filter_basic(collection):
    """Test basic arrayFilter with $[elem] updates matching elements."""
    collection.insert_one({"_id": 1, "grades": [85, 92, 45, 78]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"grades.$[elem]": 100}},
                    "arrayFilters": [{"elem": {"$gte": 90}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "grades": [85, 100, 45, 78]}])


def test_update_array_filter_multiple_identifiers(collection):
    """Test multiple $[identifier] references with corresponding filters."""
    collection.insert_one({"_id": 1, "arr": [{"x": 1, "y": 10}, {"x": 5, "y": 20}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"arr.$[a].y": 99}},
                    "arrayFilters": [{"a.x": {"$gte": 5}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "arr": [{"x": 1, "y": 10}, {"x": 5, "y": 99}]}])


def test_update_array_filter_nested(collection):
    """Test nested array filter a.$[x].b.$[y]."""
    collection.insert_one(
        {
            "_id": 1,
            "a": [
                {"b": [1, 2, 3]},
                {"b": [4, 5, 6]},
            ],
        }
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"a.$[x].b.$[y]": 0}},
                    "arrayFilters": [{"x.b": {"$gte": 4}}, {"y": {"$gte": 5}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "a": [{"b": [1, 2, 3]}, {"b": [4, 0, 0]}]}])


def test_update_array_filter_identifier_not_in_update_errors(collection):
    """Test arrayFilter for identifier not used in update document errors."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"arr.$[a]": 0}},
                    "arrayFilters": [{"a": {"$gt": 1}}, {"b": {"$gt": 2}}],
                }
            ],
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR)


def test_update_array_filter_identifier_in_update_without_filter_errors(collection):
    """Test $[identifier] used but no corresponding arrayFilter errors."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"arr.$[elem]": 0}},
                    "arrayFilters": [],
                }
            ],
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR)


def test_update_array_filter_disallowed_near_operator(collection):
    """Test $near in arrayFilters returns error."""
    collection.insert_one({"_id": 1, "arr": [{"loc": [0, 0]}]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"arr.$[elem].x": 1}},
                    "arrayFilters": [{"elem.loc": {"$near": [0, 0]}}],
                }
            ],
        },
    )
    assertFailureCode(result, NEAR_NOT_ALLOWED_ERROR)


def test_update_array_filter_disallowed_text_operator(collection):
    """Test $text in arrayFilters returns error."""
    collection.insert_one({"_id": 1, "arr": [{"t": "hello"}]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"arr.$[elem].x": 1}},
                    "arrayFilters": [{"$text": {"$search": "hello"}}],
                }
            ],
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR)
