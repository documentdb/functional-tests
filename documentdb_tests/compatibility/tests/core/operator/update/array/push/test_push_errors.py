"""Tests for $push error handling.

Covers: path traversal errors specific to $push.
"""

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import PATH_NOT_VIABLE_ERROR
from documentdb_tests.framework.executor import execute_command


def test_push_scalar_intermediate_path_error(collection):
    """Test $push through scalar intermediate field should error."""
    collection.insert_one({"_id": 1, "a": 5})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"a.b": 1}}}],
        },
    )
    assertFailureCode(
        result, PATH_NOT_VIABLE_ERROR, msg="$push through scalar intermediate field should error"
    )
