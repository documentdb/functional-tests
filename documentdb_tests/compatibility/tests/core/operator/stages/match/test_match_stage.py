"""
Aggregation $match stage tests.

Tests for the $match stage in aggregation pipelines.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


@pytest.mark.aggregate
@pytest.mark.smoke
def test_match_simple_filter(collection):
    """Test $match stage with simple equality filter."""
    collection.insert_many(
        [
            {"_id": 0, "a": "A", "b": 30, "c": "active"},
            {"_id": 1, "a": "B", "b": 25, "c": "active"},
            {"_id": 2, "a": "C", "b": 35, "c": "inactive"},
        ]
    )
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$match": {"c": "active"}}], "cursor": {}},
    )

    expected = [
        {"_id": 0, "a": "A", "b": 30, "c": "active"},
        {"_id": 1, "a": "B", "b": 25, "c": "active"},
    ]
    assertSuccess(result, expected, "Should match active documents")


@pytest.mark.aggregate
def test_match_with_comparison_operator(collection):
    """Test $match stage with comparison operators."""
    collection.insert_many(
        [
            {"_id": 0, "a": "A", "b": 30},
            {"_id": 1, "a": "B", "b": 25},
            {"_id": 2, "a": "C", "b": 35},
        ]
    )
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$match": {"b": {"$gt": 25}}}], "cursor": {}},
    )

    expected = [{"_id": 0, "a": "A", "b": 30}, {"_id": 2, "a": "C", "b": 35}]
    assertSuccess(result, expected, "Should match documents with b > 25")


@pytest.mark.aggregate
def test_match_multiple_conditions(collection):
    """Test $match stage with multiple filter conditions."""
    collection.insert_many(
        [
            {"_id": 0, "a": "A", "b": 30, "c": "NYC"},
            {"_id": 1, "a": "B", "b": 25, "c": "SF"},
            {"_id": 2, "a": "C", "b": 35, "c": "SF"},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"c": "NYC", "b": {"$gte": 30}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 0, "a": "A", "b": 30, "c": "NYC"}]
    assertSuccess(result, expected, "Should match multiple conditions")


@pytest.mark.aggregate
def test_match_empty_result(collection):
    """Test $match stage that matches no documents."""
    collection.insert_many(
        [
            {"_id": 0, "a": "A", "b": "active"},
            {"_id": 1, "a": "B", "b": "active"},
        ]
    )
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$match": {"b": "inactive"}}], "cursor": {}},
    )

    assertSuccess(result, [], "Should return empty result when no match")
