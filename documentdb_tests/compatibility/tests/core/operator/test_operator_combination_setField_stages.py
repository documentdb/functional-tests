"""
Integration tests for $setField with pipeline stages.

Covers $setField used within $replaceWith and $addFields stages:
dotted/dollar field handling via $replaceWith and non-persistence.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_setField_dotted_remove(collection):
    """Test removing a dotted field name."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {
                    "$replaceWith": {
                        "$setField": {
                            "field": "a.b",
                            "input": {"$setField": {"field": "a.b", "input": {}, "value": 5}},
                            "value": "$$REMOVE",
                        }
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{}], raw_res=False, msg="Dotted field should be removed")


def test_setField_dollar_remove(collection):
    """Test removing a dollar-prefixed field name."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {
                    "$replaceWith": {
                        "$setField": {
                            "field": {"$literal": "$x"},
                            "input": {
                                "$setField": {"field": {"$literal": "$x"}, "input": {}, "value": 5}
                            },
                            "value": "$$REMOVE",
                        }
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{}], raw_res=False, msg="Dollar-prefixed field should be removed")


def test_setField_does_not_modify_original(collection):
    """Test $setField does not modify original document in pipeline."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$addFields": {
                        "modified": {"$setField": {"field": "x", "input": "$$ROOT", "value": 1}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "original_has_x": {"$ifNull": ["$x", "missing"]},
                        "modified_has_x": "$modified.x",
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"original_has_x": "missing", "modified_has_x": 1}],
        msg="Original document should not be modified by $setField",
    )


def test_setField_insert_many_addFields(collection):
    """Test $setField in $addFields applies correctly to each document."""
    collection.insert_many(
        [
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
            {"_id": 3},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$addFields": {"b": {"$setField": {"field": "x", "input": {}, "value": 1}}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "a": 10, "b": {"x": 1}},
            {"_id": 2, "a": 20, "b": {"x": 1}},
            {"_id": 3, "b": {"x": 1}},
        ],
        msg="$setField in $addFields should apply per document",
    )


def test_setField_insert_many_replaceWith(collection):
    """Test $setField in $replaceWith applies correctly to each document."""
    collection.insert_many(
        [
            {"_id": 1, "a": 10, "b": 1},
            {"_id": 2, "a": 20},
            {"_id": 3, "b": 3},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$replaceWith": {
                        "$setField": {
                            "field": "b",
                            "input": "$$ROOT",
                            "value": 99,
                        }
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "a": 10, "b": 99},
            {"_id": 2, "a": 20, "b": 99},
            {"_id": 3, "b": 99},
        ],
        msg="$setField in $replaceWith should apply per document",
    )
