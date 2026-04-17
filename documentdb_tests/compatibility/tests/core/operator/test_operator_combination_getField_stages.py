"""
Integration tests for $getField with pipeline stages.

Covers $getField used within $project stages: dotted field literal vs nested
path behavior, and multiple $getField expressions in a single stage.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_getField_dotted_field_not_nested(collection):
    """Test $getField with dotted field returns literal key, not nested path."""
    collection.insert_one({"_id": 1, "a.b": 1, "a": {"b": 2}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "literal": {"$getField": "a.b"}, "nested": "$a.b"}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"literal": 1, "nested": 2}],
        msg="$getField should return literal 'a.b', $a.b should traverse",
    )


def test_getField_multiple_in_project(collection):
    """Test multiple $getField expressions in same $project."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2, "c": 3})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "f1": {"$getField": "a"},
                        "f2": {"$getField": "b"},
                        "f3": {"$getField": "c"},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"f1": 1, "f2": 2, "f3": 3}],
        msg="Should support multiple $getField in same $project",
    )
