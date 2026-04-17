"""
Integration tests for $unsetField with pipeline stages.

Covers $unsetField used within $replaceWith, $project, and $addFields stages:
multi-document pipelines, dotted field non-traversal, non-persistence,
and equivalence with $setField+$$REMOVE.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_unsetField_multiple_docs(collection):
    """Test $unsetField across multiple documents."""
    collection.insert_many(
        [
            {"_id": 1, "obj": {"a": 1, "b": 2}},
            {"_id": 2, "obj": {"a": 3, "b": 4}},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "result": {"$unsetField": {"field": "a", "input": "$obj"}},
                    }
                },
                {"$sort": {"result.b": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"result": {"b": 2}}, {"result": {"b": 4}}])


def test_unsetField_replaceWith_dotted(collection):
    """Test $unsetField non-traversal via $replaceWith with dotted field."""
    collection.insert_one({"_id": 1, "a": {"b": 2}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$replaceWith": {"$setField": {"field": "a.b", "input": "$$ROOT", "value": 99}}},
                {"$replaceWith": {"$unsetField": {"field": "a.b", "input": "$$ROOT"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": 2}}])


def test_unsetField_original_not_modified(collection):
    """Test $unsetField does not modify the original document."""
    collection.insert_one({"_id": 1, "obj": {"a": 1, "b": 2}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"updated": {"$unsetField": {"field": "a", "input": "$obj"}}}},
                {"$project": {"_id": 0, "obj": 1, "updated": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"obj": {"a": 1, "b": 2}, "updated": {"b": 2}}])


def test_unsetField_equivalence_dotted(collection):
    """Test $unsetField and $setField+$$REMOVE equivalence for dotted field."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {
                    "$replaceWith": {
                        "$unsetField": {
                            "field": "a.b",
                            "input": {"$setField": {"field": "a.b", "input": {}, "value": 1}},
                        }
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{}])


def test_unsetField_equivalence_dollar(collection):
    """Test $unsetField and $setField+$$REMOVE equivalence for dollar field."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {
                    "$replaceWith": {
                        "$unsetField": {
                            "field": {"$literal": "$x"},
                            "input": {
                                "$setField": {"field": {"$literal": "$x"}, "input": {}, "value": 1}
                            },
                        }
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{}])
