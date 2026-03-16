"""
Aggregation $group stage tests.

Tests for the $group stage in aggregation pipelines.
"""

import pytest

from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.assertions import assertSuccess


@pytest.mark.aggregate
@pytest.mark.smoke
def test_group_with_count(collection):
    """Test $group stage with count aggregation."""
    collection.insert_many([
        {"a": "A", "b": 100},
        {"a": "A", "b": 90},
        {"a": "B", "b": 80},
        {"a": "B", "b": 75},
    ])
    result = execute_command(collection, {"aggregate": collection.name, "pipeline": [{"$group": {"_id": "$a", "count": {"$sum": 1}}}], "cursor": {}})
    
    expected = [
        {"_id": "A", "count": 2},
        {"_id": "B", "count": 2}
    ]
    assertSuccess(result, expected, "Should group and count by department", ignore_order=True)


@pytest.mark.aggregate
def test_group_with_sum(collection):
    """Test $group stage with sum aggregation."""
    collection.insert_many([
        {"a": "A", "b": 100},
        {"a": "A", "b": 90},
        {"a": "B", "b": 80},
    ])
    result = execute_command(collection, {"aggregate": collection.name, "pipeline": [{"$group": {"_id": "$a", "total": {"$sum": "$b"}}}], "cursor": {}})
    
    expected = [
        {"_id": "A", "total": 190},
        {"_id": "B", "total": 80}
    ]
    assertSuccess(result, expected, "Should sum by group", ignore_order=True)


@pytest.mark.aggregate
def test_group_with_avg(collection):
    """Test $group stage with average aggregation."""
    collection.insert_many([
        {"a": "A", "b": 100},
        {"a": "A", "b": 90},
        {"a": "B", "b": 80},
    ])
    result = execute_command(collection, {"aggregate": collection.name, "pipeline": [{"$group": {"_id": "$a", "avg": {"$avg": "$b"}}}], "cursor": {}})
    
    expected = [
        {"_id": "A", "avg": 95.0},
        {"_id": "B", "avg": 80.0}
    ]
    assertSuccess(result, expected, "Should calculate average by group", ignore_order=True)


@pytest.mark.aggregate
def test_group_with_min_max(collection):
    """Test $group stage with min and max aggregations."""
    collection.insert_many([
        {"a": "A", "b": 100},
        {"a": "A", "b": 90},
        {"a": "B", "b": 80},
    ])
    result = execute_command(collection, {"aggregate": collection.name, "pipeline": [{"$group": {"_id": "$a", "min": {"$min": "$b"}, "max": {"$max": "$b"}}}], "cursor": {}})
    
    expected = [
        {"_id": "A", "min": 90, "max": 100},
        {"_id": "B", "min": 80, "max": 80}
    ]
    assertSuccess(result, expected, "Should find min and max by group", ignore_order=True)


@pytest.mark.aggregate
def test_group_all_documents(collection):
    """Test $group stage grouping all documents (using null as _id)."""
    collection.insert_many([
        {"a": "A", "b": 5},
        {"a": "B", "b": 10},
        {"a": "A", "b": 3},
    ])
    result = execute_command(collection, {"aggregate": collection.name, "pipeline": [{"$group": {"_id": None, "total": {"$sum": "$b"}}}], "cursor": {}})
    
    expected = [{"_id": None, "total": 18}]
    assertSuccess(result, expected, "Should sum across all documents")
