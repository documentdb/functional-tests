"""
Dot notation (embedded document) tests for $rename update operator.

Tests renaming within, into, out of, and between embedded documents, plus
deep nested paths, intermediate-object creation, nested-target overwrite, and
sibling-field preservation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOT_NOTATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "within_same_embedded",
        setup_docs=[{"_id": 1, "a": {"b": 1, "d": 2}}],
        query={"_id": 1},
        update={"$rename": {"a.b": "a.c"}},
        expected={"_id": 1, "a": {"c": 1, "d": 2}},
        msg="$rename within same embedded doc should work",
    ),
    UpdateTestCase(
        "move_out_of_embedded",
        setup_docs=[{"_id": 1, "a": {"b": 1}}],
        query={"_id": 1},
        update={"$rename": {"a.b": "c"}},
        expected={"_id": 1, "a": {}, "c": 1},
        msg="$rename from embedded to top level should move field out",
    ),
    UpdateTestCase(
        "move_into_embedded",
        setup_docs=[{"_id": 1, "c": 1, "a": {}}],
        query={"_id": 1},
        update={"$rename": {"c": "a.b"}},
        expected={"_id": 1, "a": {"b": 1}},
        msg="$rename from top level into embedded should move field in",
    ),
    UpdateTestCase(
        "between_embedded_docs",
        setup_docs=[{"_id": 1, "a": {"b": 1}, "c": {}}],
        query={"_id": 1},
        update={"$rename": {"a.b": "c.d"}},
        expected={"_id": 1, "a": {}, "c": {"d": 1}},
        msg="$rename between embedded docs should work",
    ),
    UpdateTestCase(
        "deep_rename",
        setup_docs=[{"_id": 1, "a": {"b": {"c": {"d": 1}}}}],
        query={"_id": 1},
        update={"$rename": {"a.b.c.d": "a.b.c.e"}},
        expected={"_id": 1, "a": {"b": {"c": {"e": 1}}}},
        msg="$rename deeply nested field should work",
    ),
    UpdateTestCase(
        "creates_intermediate_objects",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$rename": {"x": "a.b.c.d"}},
        expected={"_id": 1, "a": {"b": {"c": {"d": 1}}}},
        msg="$rename should create intermediate objects",
    ),
    UpdateTestCase(
        "deep_to_top_level",
        setup_docs=[{"_id": 1, "a": {"b": {"c": {"d": 1}}}}],
        query={"_id": 1},
        update={"$rename": {"a.b.c.d": "x"}},
        expected={"_id": 1, "a": {"b": {"c": {}}}, "x": 1},
        msg="$rename from deep nested to top level should work",
    ),
    UpdateTestCase(
        "overwrite_nested_target",
        setup_docs=[{"_id": 1, "a": 1, "b": {"c": 99}}],
        query={"_id": 1},
        update={"$rename": {"a": "b.c"}},
        expected={"_id": 1, "b": {"c": 1}},
        msg="$rename should overwrite existing nested target",
    ),
    UpdateTestCase(
        "intermediate_preserves_siblings",
        setup_docs=[{"_id": 1, "x": 1, "a": {"existing": "keep"}}],
        query={"_id": 1},
        update={"$rename": {"x": "a.new"}},
        expected={"_id": 1, "a": {"existing": "keep", "new": 1}},
        msg="$rename into existing embedded doc should preserve sibling fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOT_NOTATION_TESTS))
def test_rename_dot_notation(collection, test: UpdateTestCase):
    """Test $rename with dot notation (embedded document paths)."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [test.expected], msg=test.msg)
