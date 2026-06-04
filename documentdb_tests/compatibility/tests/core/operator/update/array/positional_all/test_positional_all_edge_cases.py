"""Tests for $[] positional-all edge cases.

Covers: null element handling and BSON type distinction in query filters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NULL_HANDLING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_null_elements_to_value",
        setup_docs=[{"_id": 1, "arr": [None, None, None]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"_id": 1, "arr": ["replaced", "replaced", "replaced"]},
        msg="$[] with $set on null elements should replace all with new value",
    ),
    UpdateTestCase(
        "set_all_to_null",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": None}},
        expected={"_id": 1, "arr": [None, None, None]},
        msg="$[] with $set value of null should update all elements to null",
    ),
]


BSON_TYPE_QUERY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "false_not_matching_zero",
        setup_docs=[{"_id": 1, "arr": [0, 1, 2]}],
        query={"arr": False},
        update={"$set": {"arr.$[]": 99}},
        expected={"_id": 1, "arr": [0, 1, 2]},
        msg="Query {arr: false} should not match doc with 0 in array (BSON type distinction)",
    ),
]


SUCCESS_TESTS = NULL_HANDLING_TESTS + BSON_TYPE_QUERY_TESTS


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_positional_all_edge_case(collection, test: UpdateTestCase):
    """Test $[] positional-all edge cases that succeed."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
