"""
Embedded document and field path tests for the $pop update array operator.

Tests $pop targeting via dot notation, a numeric index path, an array field
inside an embedded document, a missing intermediate path, and independent
evaluation of multiple fields in one operation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Paths]: $pop targets array fields through dot notation, numeric index paths,
# and embedded documents, and evaluates multiple fields independently.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "dot_notation_nested_array",
        setup_docs=[{"_id": 1, "a": {"b": [1, 2, 3]}}],
        query={"_id": 1},
        update={"$pop": {"a.b": 1}},
        expected={"_id": 1, "a": {"b": [1, 2]}},
        msg="$pop on 'a.b' should remove the last element of the nested array",
    ),
    UpdateTestCase(
        "deeply_nested_dot_path",
        setup_docs=[{"_id": 1, "a": {"b": {"c": {"d": [1, 2, 3]}}}}],
        query={"_id": 1},
        update={"$pop": {"a.b.c.d": 1}},
        expected={"_id": 1, "a": {"b": {"c": {"d": [1, 2]}}}},
        msg="$pop on 'a.b.c.d' should remove the last element of the deeply nested array",
    ),
    UpdateTestCase(
        "numeric_index_path",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [4, 5, 6]]}],
        query={"_id": 1},
        update={"$pop": {"arr.1": 1}},
        expected={"_id": 1, "arr": [[1, 2, 3], [4, 5]]},
        msg="$pop on 'arr.1' should target the inner array at index 1",
    ),
    UpdateTestCase(
        "embedded_doc_array_field",
        setup_docs=[{"_id": 1, "arr": [{"x": [10, 20, 30]}, {"x": [40, 50]}]}],
        query={"_id": 1},
        update={"$pop": {"arr.0.x": -1}},
        expected={"_id": 1, "arr": [{"x": [20, 30]}, {"x": [40, 50]}]},
        msg="$pop on 'arr.0.x' should target the array field inside the first embedded document",
    ),
    UpdateTestCase(
        "missing_intermediate_path_noop",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$pop": {"x.y": 1}},
        expected={"_id": 1, "a": 1},
        msg="$pop on a path with a missing intermediate field should be a no-op",
    ),
    UpdateTestCase(
        "multiple_fields_independent",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [4, 5, 6]}],
        query={"_id": 1},
        update={"$pop": {"a": 1, "b": -1}},
        expected={"_id": 1, "a": [1, 2], "b": [5, 6]},
        msg="$pop on multiple fields should remove from each according to its own value",
    ),
    UpdateTestCase(
        "multiple_fields_one_empty",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": []}],
        query={"_id": 1},
        update={"$pop": {"a": 1, "b": 1}},
        expected={"_id": 1, "a": [1, 2], "b": []},
        msg="$pop on multiple fields should modify the non-empty one and leave the empty one",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_pop_embedded_docs(collection, test: UpdateTestCase):
    """Test $pop with embedded documents and various field paths."""
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
