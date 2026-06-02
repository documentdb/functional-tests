"""Tests for $[] positional-all with null handling and operator interaction.

Covers: null element handling and interaction with other update operators
in the same update document.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Null/Missing Field Handling ---

NULL_HANDLING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_null_elements_to_value",
        setup_docs=[{"_id": 1, "arr": [None, None, None]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $set on null elements should replace all with new value",
    ),
    UpdateTestCase(
        "set_all_to_null",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": None}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $set value of null should update all elements to null",
    ),
]


# --- Interaction with Other Update Operators ---

INTERACTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "positional_all_and_set_different_fields",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": 10}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0, "x": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] on one field and $set on another should both succeed",
    ),
    UpdateTestCase(
        "positional_all_and_positional_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        query={"_id": 1, "b": 20},
        update={"$set": {"a.$[]": 0, "b.$": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] and $ on different fields in same update should both work",
    ),
]


ALL_TESTS = NULL_HANDLING_TESTS + INTERACTION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_all_update_operators(collection, test: UpdateTestCase):
    """Test $[] with update operators - success cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
