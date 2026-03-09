"""
Aggregation $group stage tests.

Tests for the $group stage in aggregation pipelines.
"""

import pytest


@pytest.mark.aggregate
@pytest.mark.smoke
def test_group_with_count(collection):
    """Test $group stage with count aggregation."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "department": "Engineering", "salary": 100000},
        {"name": "Bob", "department": "Engineering", "salary": 90000},
        {"name": "Charlie", "department": "Sales", "salary": 80000},
        {"name": "David", "department": "Sales", "salary": 75000},
    ])

    # Act - Execute aggregation to count documents by department
    pipeline = [{"$group": {"_id": "$department", "count": {"$sum": 1}}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 departments"

    # Convert to dict for easier verification
    dept_counts = {doc["_id"]: doc["count"] for doc in result}
    assert dept_counts["Engineering"] == 2, "Expected 2 employees in Engineering"
    assert dept_counts["Sales"] == 2, "Expected 2 employees in Sales"


@pytest.mark.aggregate
def test_group_with_sum(collection):
    """Test $group stage with sum aggregation."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "department": "Engineering", "salary": 100000},
        {"name": "Bob", "department": "Engineering", "salary": 90000},
        {"name": "Charlie", "department": "Sales", "salary": 80000},
    ])

    # Act - Execute aggregation to sum salaries by department
    pipeline = [{"$group": {"_id": "$department", "totalSalary": {"$sum": "$salary"}}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 departments"

    # Convert to dict for easier verification
    dept_salaries = {doc["_id"]: doc["totalSalary"] for doc in result}
    assert dept_salaries["Engineering"] == 190000, "Expected total Engineering salary of 190000"
    assert dept_salaries["Sales"] == 80000, "Expected total Sales salary of 80000"


@pytest.mark.aggregate
def test_group_with_avg(collection):
    """Test $group stage with average aggregation."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "department": "Engineering", "salary": 100000},
        {"name": "Bob", "department": "Engineering", "salary": 90000},
        {"name": "Charlie", "department": "Sales", "salary": 80000},
    ])

    # Act - Execute aggregation to calculate average salary by department
    pipeline = [{"$group": {"_id": "$department", "avgSalary": {"$avg": "$salary"}}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 departments"

    # Convert to dict for easier verification
    dept_avg = {doc["_id"]: doc["avgSalary"] for doc in result}
    assert dept_avg["Engineering"] == 95000, "Expected average Engineering salary of 95000"
    assert dept_avg["Sales"] == 80000, "Expected average Sales salary of 80000"


@pytest.mark.aggregate
def test_group_with_min_max(collection):
    """Test $group stage with min and max aggregations."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "department": "Engineering", "salary": 100000},
        {"name": "Bob", "department": "Engineering", "salary": 90000},
        {"name": "Charlie", "department": "Sales", "salary": 80000},
    ])

    # Act - Execute aggregation to find min and max salary by department
    pipeline = [
        {
            "$group": {
                "_id": "$department",
                "minSalary": {"$min": "$salary"},
                "maxSalary": {"$max": "$salary"},
            }
        }
    ]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 2, "Expected 2 departments"

    # Verify Engineering department
    eng_dept = next(doc for doc in result if doc["_id"] == "Engineering")
    assert eng_dept["minSalary"] == 90000, "Expected min Engineering salary of 90000"
    assert eng_dept["maxSalary"] == 100000, "Expected max Engineering salary of 100000"


@pytest.mark.aggregate
def test_group_all_documents(collection):
    """Test $group stage grouping all documents (using null as _id)."""
    # Arrange - Insert test data
    collection.insert_many([
        {"item": "A", "quantity": 5},
        {"item": "B", "quantity": 10},
        {"item": "A", "quantity": 3},
    ])

    # Act - Execute aggregation to sum quantities across all documents
    pipeline = [{"$group": {"_id": None, "totalQuantity": {"$sum": "$quantity"}}}]
    result = list(collection.aggregate(pipeline))

    # Assert - Verify results
    assert len(result) == 1, "Expected single result grouping all documents"
    assert result[0]["totalQuantity"] == 18, "Expected total quantity of 18"
