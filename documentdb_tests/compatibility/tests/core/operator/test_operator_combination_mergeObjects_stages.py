"""
Integration tests for $mergeObjects with pipeline stages.

Covers $mergeObjects used within $replaceWith and $addFields stages:
dotted field names, empty string keys, and non-persistence.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_mergeObjects_dot_disjoint(collection):
    """Test $mergeObjects with dotted field names preserved as literal keys."""
    collection.insert_one({"_id": 1, "obj1": {"a.b": 1}, "obj2": {"c.d": 2}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$replaceWith": {"$mergeObjects": ["$obj1", "$obj2"]}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"a.b": 1, "c.d": 2}])


def test_mergeObjects_dot_overwrite(collection):
    """Test $mergeObjects with dotted field name overwrite."""
    collection.insert_one({"_id": 1, "obj1": {"a.b": 1}, "obj2": {"a.b": 2}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$replaceWith": {"$mergeObjects": ["$obj1", "$obj2"]}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"a.b": 2}])


def test_mergeObjects_empty_string_key(collection):
    """Test $mergeObjects with empty string field name."""
    collection.insert_one({"_id": 1, "obj1": {"": 1}, "obj2": {"a": 2}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$replaceWith": {"$mergeObjects": ["$obj1", "$obj2"]}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"": 1, "a": 2}])


def test_mergeObjects_original_not_modified(collection):
    """Test $mergeObjects does not modify the original document."""
    collection.insert_one({"_id": 1, "obj": {"a": 1, "b": 2}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"merged": {"$mergeObjects": ["$obj", {"b": 99, "c": 3}]}}},
                {"$project": {"_id": 0, "obj": 1, "merged": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"obj": {"a": 1, "b": 2}, "merged": {"a": 1, "b": 99, "c": 3}}])
