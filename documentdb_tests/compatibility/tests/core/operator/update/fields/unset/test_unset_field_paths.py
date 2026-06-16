"""
Tests for $unset update operator - field path handling.

Covers dot notation for embedded documents, deeply nested paths, numeric keys
on objects, and no-op behavior on non-existent or unreachable paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UNSET_EMBEDDED_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="remove_nested_field_keep_sibling",
        setup_docs=[{"_id": 1, "a": {"b": 1, "c": 2}}],
        query={"_id": 1},
        update={"$unset": {"a.b": ""}},
        expected=[{"_id": 1, "a": {"c": 2}}],
        msg="Should remove nested field, keep sibling",
    ),
    UpdateTestCase(
        id="remove_only_nested_field",
        setup_docs=[{"_id": 1, "a": {"b": 1}}],
        query={"_id": 1},
        update={"$unset": {"a.b": ""}},
        expected=[{"_id": 1, "a": {}}],
        msg="Should remove nested field, leave empty parent",
    ),
    UpdateTestCase(
        id="remove_entire_embedded_doc",
        setup_docs=[{"_id": 1, "a": {"b": 1}}],
        query={"_id": 1},
        update={"$unset": {"a": ""}},
        expected=[{"_id": 1}],
        msg="Should remove entire embedded document",
    ),
    UpdateTestCase(
        id="remove_deeply_nested",
        setup_docs=[{"_id": 1, "a": {"b": {"c": {"d": 1, "e": 2}}}}],
        query={"_id": 1},
        update={"$unset": {"a.b.c.d": ""}},
        expected=[{"_id": 1, "a": {"b": {"c": {"e": 2}}}}],
        msg="Should remove deeply nested field",
    ),
    UpdateTestCase(
        id="numeric_key_on_object",
        setup_docs=[{"_id": 1, "a": {"0": "val", "1": "other"}}],
        query={"_id": 1},
        update={"$unset": {"a.0": ""}},
        expected=[{"_id": 1, "a": {"1": "other"}}],
        msg="Numeric dot notation should resolve to object key, not array index",
    ),
]


UNSET_NONEXISTENT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="nonexistent_parent",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$unset": {"a.b": ""}},
        expected=[{"_id": 1, "x": 1}],
        msg="Unset on non-existent parent should be no-op",
    ),
    UpdateTestCase(
        id="parent_is_scalar",
        setup_docs=[{"_id": 1, "a": "string"}],
        query={"_id": 1},
        update={"$unset": {"a.b.c": ""}},
        expected=[{"_id": 1, "a": "string"}],
        msg="Unset when parent is scalar should be no-op",
    ),
    UpdateTestCase(
        id="non_numeric_path_into_array",
        setup_docs=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        query={"_id": 1},
        update={"$unset": {"a.b": ""}},
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="Non-numeric path into array should be no-op (no broadcast)",
    ),
]

ALL_FIELD_PATH_TESTS = UNSET_EMBEDDED_TESTS + UNSET_NONEXISTENT_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_FIELD_PATH_TESTS))
def test_unset_field_paths(collection, test):
    """Test $unset field path handling."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)
