"""Tests for $addToSet error handling.

Covers: invalid modifiers ($sort, $slice, $position, unknown), $each with non-array
argument, immutable _id field.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INVALID_MODIFIER_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "each_with_sort_modifier",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [3], "$sort": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error with $sort modifier in $addToSet",
    ),
    UpdateTestCase(
        "each_with_slice_modifier",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [3], "$slice": 2}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error with $slice modifier in $addToSet",
    ),
    UpdateTestCase(
        "each_with_position_modifier",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [3], "$position": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error with $position modifier in $addToSet",
    ),
    UpdateTestCase(
        "each_with_unknown_modifier",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [3], "$unknown": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should error with unknown modifier in $addToSet",
    ),
    UpdateTestCase(
        "each_value_not_array",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": "not_array"}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should error when $each value is not an array",
    ),
    UpdateTestCase(
        "each_value_null",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": None}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should error when $each value is null",
    ),
    UpdateTestCase(
        "each_value_object",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": {"a": 1}}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should error when $each value is an object",
    ),
    UpdateTestCase(
        "immutable_id_field",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"_id": 2}},
        error_code=BAD_VALUE_ERROR,
        msg="$addToSet on _id should error",
    ),
]


ALL_TESTS = INVALID_MODIFIER_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_addToSet_error(collection, test: UpdateTestCase):
    """Test $addToSet error handling."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]
