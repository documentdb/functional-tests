"""Tests for $pullAll with dot notation and nested fields.

Covers: deeply nested dot notation paths, intermediate path behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NESTED_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "dot_notation_deep",
        setup_docs=[{"_id": 1, "a": {"b": {"c": [10, 20, 30]}}}],
        query={"_id": 1},
        update={"$pullAll": {"a.b.c": [20]}},
        expected={"_id": 1, "a": {"b": {"c": [10, 30]}}},
        msg="Should remove from deeply nested array",
    ),
    UpdateTestCase(
        "intermediate_does_not_exist_noop",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$pullAll": {"a.b": [1]}},
        expected={"_id": 1, "x": 1},
        msg="Should be no-op when intermediate path does not exist",
    ),
    UpdateTestCase(
        "dot_notation_array_index",
        setup_docs=[{"_id": 1, "a": [{"b": [1, 2, 3]}, {"b": [4, 5, 6]}]}],
        query={"_id": 1},
        update={"$pullAll": {"a.0.b": [2, 3]}},
        expected={"_id": 1, "a": [{"b": [1]}, {"b": [4, 5, 6]}]},
        msg="Should pull from specific array element via numeric index in dot notation",
    ),
    UpdateTestCase(
        "array_intermediate_no_traversal",
        setup_docs=[{"_id": 1, "a": [{"b": [1, 2, 3]}, {"b": [2, 3, 4]}]}],
        query={"_id": 1},
        update={"$pullAll": {"a.b": [2]}},
        expected={"_id": 1, "a": [{"b": [1, 2, 3]}, {"b": [2, 3, 4]}]},
        msg="Should be no-op when intermediate is an array without explicit index",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_FIELD_TESTS))
def test_pullAll_nested_fields(collection, test: UpdateTestCase):
    """Test $pullAll with dot notation and nested fields."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
