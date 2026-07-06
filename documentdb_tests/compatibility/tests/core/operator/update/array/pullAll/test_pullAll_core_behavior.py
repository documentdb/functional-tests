"""Tests for $pullAll core behavior.

Covers: removal of all instances, empty values list, all elements removed,
empty array target, duplicate values in values list, values not present.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

PULLALL_CORE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "removes_all_instances",
        setup_docs=[{"_id": 1, "a": [1, 2, 3, 1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [1, 3]}},
        expected={"_id": 1, "a": [2, 2]},
        msg="Should remove all instances of each specified value",
    ),
    UpdateTestCase(
        "removes_multiple_occurrences",
        setup_docs=[{"_id": 1, "a": [5, 5, 5, 6, 5]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [5]}},
        expected={"_id": 1, "a": [6]},
        msg="Should remove multiple occurrences of same value",
    ),
    UpdateTestCase(
        "values_not_present_noop",
        setup_docs=[{"_id": 1, "a": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [99, 100]}},
        expected={"_id": 1, "a": [1, 2, 3]},
        msg="Should be no-op when values not present",
    ),
    UpdateTestCase(
        "some_values_present_some_not",
        setup_docs=[{"_id": 1, "a": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [2, 4, 99]}},
        expected={"_id": 1, "a": [1, 3]},
        msg="Should remove only matching values",
    ),
    UpdateTestCase(
        "empty_values_list_noop",
        setup_docs=[{"_id": 1, "a": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"a": []}},
        expected={"_id": 1, "a": [1, 2, 3]},
        msg="Should be no-op with empty values list",
    ),
    UpdateTestCase(
        "removes_all_leaves_empty_array",
        setup_docs=[{"_id": 1, "a": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [1, 2, 3]}},
        expected={"_id": 1, "a": []},
        msg="Should leave empty array when all elements removed",
    ),
    UpdateTestCase(
        "empty_array_noop",
        setup_docs=[{"_id": 1, "a": []}],
        query={"_id": 1},
        update={"$pullAll": {"a": [1, 2]}},
        expected={"_id": 1, "a": []},
        msg="Should be no-op on empty array",
    ),
    UpdateTestCase(
        "duplicate_values_in_values_list",
        setup_docs=[{"_id": 1, "a": [1, 2, 3, 1]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [1, 1, 1]}},
        expected={"_id": 1, "a": [2, 3]},
        msg="Duplicate values in values list should behave same as single",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PULLALL_CORE_TESTS))
def test_pullAll_core_behavior(collection, test: UpdateTestCase):
    """Test $pullAll core removal behavior."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
