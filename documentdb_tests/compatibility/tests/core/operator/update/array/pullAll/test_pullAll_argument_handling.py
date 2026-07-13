"""Tests for $pullAll argument handling.

Covers: null/missing field handling, empty operand, multiple fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SUCCESS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "null_in_values_removes_null",
        setup_docs=[{"_id": 1, "a": [1, None, 2, None, 3]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [None]}},
        expected={"_id": 1, "a": [1, 2, 3]},
        msg="Should remove null elements from array",
    ),
    UpdateTestCase(
        "nonexistent_field_noop",
        setup_docs=[{"_id": 1, "b": "other"}],
        query={"_id": 1},
        update={"$pullAll": {"a": [1, 2]}},
        expected={"_id": 1, "b": "other"},
        msg="Should be no-op when field does not exist",
    ),
    UpdateTestCase(
        "multiple_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": ["x", "y", "z"]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [2], "b": ["y"]}},
        expected={"_id": 1, "a": [1, 3], "b": ["x", "z"]},
        msg="Should process multiple fields independently",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUCCESS_TESTS))
def test_pullAll_argument_handling(collection, test: UpdateTestCase):
    """Test $pullAll null values, missing fields, and multiple fields handling."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)


def test_pullAll_empty_operand_noop(collection):
    """Test $pullAll with empty operand expression {} is a no-op."""
    collection.insert_one({"_id": 1, "a": [1, 2, 3]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {}}}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "a": [1, 2, 3]}], msg="Empty $pullAll should be no-op")
