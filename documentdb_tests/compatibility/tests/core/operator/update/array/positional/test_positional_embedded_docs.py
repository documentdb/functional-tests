"""Tests for $ positional with embedded documents and dot notation.

Covers: updating fields in embedded documents, dot notation paths,
nested fields, and edge cases with numeric path components.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EMBEDDED_DOC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "set_field_in_matched_doc",
        setup_docs=[{"_id": 1, "arr": [{"name": "A", "val": 1}, {"name": "B", "val": 2}]}],
        query={"_id": 1, "arr.name": "B"},
        update={"$set": {"arr.$.val": 99}},
        expected={"_id": 1, "arr": [{"name": "A", "val": 1}, {"name": "B", "val": 99}]},
        msg="$ with dot notation should update field in matched embedded document",
    ),
    UpdateTestCase(
        "elemMatch_set_field",
        setup_docs=[{"_id": 1, "arr": [{"x": 1, "y": 10}, {"x": 2, "y": 20}]}],
        query={"_id": 1, "arr": {"$elemMatch": {"x": 2}}},
        update={"$set": {"arr.$.y": 99}},
        expected={"_id": 1, "arr": [{"x": 1, "y": 10}, {"x": 2, "y": 99}]},
        msg="$ with $elemMatch and $set should update matched embedded doc field",
    ),
    UpdateTestCase(
        "deeply_nested_field",
        setup_docs=[{"_id": 1, "arr": [{"nested": {"field": 1}}, {"nested": {"field": 2}}]}],
        query={"_id": 1, "arr.nested.field": 2},
        update={"$set": {"arr.$.nested.field": 99}},
        expected={"_id": 1, "arr": [{"nested": {"field": 1}}, {"nested": {"field": 99}}]},
        msg="$ updating deeply nested field should work",
    ),
    UpdateTestCase(
        "nested_array_field",
        setup_docs=[{"_id": 1, "outer": {"inner": [1, 2, 3]}}],
        query={"_id": 1, "outer.inner": 2},
        update={"$set": {"outer.inner.$": 99}},
        expected={"_id": 1, "outer": {"inner": [1, 99, 3]}},
        msg="$ on nested array 'outer.inner.$' should update matched element",
    ),
    UpdateTestCase(
        "query_traverses_nested_array",
        setup_docs=[
            {"_id": 1, "arr": [{"nested": [1, 2]}, {"nested": [3, 4]}]},
        ],
        query={"arr.nested": 3},
        update={"$set": {"arr.$.nested": [99]}},
        expected={"_id": 1, "arr": [{"nested": [1, 2]}, {"nested": [99]}]},
        msg="$ should resolve outer array position when query traverses inner array",
    ),
    UpdateTestCase(
        "numeric_path_component",
        setup_docs=[
            {"_id": 1, "arr": [{"vals": [10, 20]}, {"vals": [30, 40]}]},
        ],
        query={"_id": 1, "arr.vals": 30},
        update={"$set": {"arr.$.vals.0": 99}},
        expected={"_id": 1, "arr": [{"vals": [10, 20]}, {"vals": [99, 40]}]},
        msg="$ with numeric path component should update specific index in matched element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMBEDDED_DOC_TESTS))
def test_positional_embedded_docs(collection, test: UpdateTestCase):
    """Test $ positional with embedded documents and dot notation."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection, {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]}
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
