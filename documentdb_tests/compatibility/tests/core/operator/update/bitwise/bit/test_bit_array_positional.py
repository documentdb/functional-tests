"""Tests for $bit update operator with positional array operators."""

from __future__ import annotations

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_bit_positional_dollar(collection):
    """Test $bit with $ positional operator on matched array element."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1, "arr": 2}, "u": {"$bit": {"arr.$": {"xor": 7}}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "arr": [1, 5, 3]}],
        msg="$bit should update matched array element via $ positional.",
    )


def test_bit_positional_all(collection):
    """Test $bit with $[] all positional operator."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$bit": {"arr.$[]": {"or": 8}}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "arr": [9, 10, 11]}],
        msg="$bit should update all array elements via $[] positional.",
    )


def test_bit_positional_filtered(collection):
    """Test $bit with $[elem] filtered positional operator."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3, 4, 5]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$bit": {"arr.$[elem]": {"or": 16}}},
                    "arrayFilters": [{"elem": {"$gte": 3}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "arr": [1, 2, 19, 20, 21]}],
        msg="$bit should update filtered array elements via $[elem] positional.",
    )
