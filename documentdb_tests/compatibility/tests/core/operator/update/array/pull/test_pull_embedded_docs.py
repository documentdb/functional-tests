"""Tests for $pull with embedded documents, nested arrays, and dot notation.

Covers: embedded doc conditions, $elemMatch, dot notation targeting,
and nested field conditions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

PULL_EMBEDDED_DOC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "embedded_doc_multi_field_condition",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"x": 8, "y": "B"},
                    {"x": 5, "y": "A"},
                    {"x": 8, "y": "C"},
                ],
            }
        ],
        query={"_id": 1},
        update={"$pull": {"arr": {"x": 8, "y": "B"}}},
        expected={"_id": 1, "arr": [{"x": 5, "y": "A"}, {"x": 8, "y": "C"}]},
        msg="Should remove embedded docs matching both fields",
    ),
    UpdateTestCase(
        "embedded_doc_single_field_matches_extra",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"a": 1, "b": 2},
                    {"a": 1, "c": 3},
                    {"a": 2},
                ],
            }
        ],
        query={"_id": 1},
        update={"$pull": {"arr": {"a": 1}}},
        expected={"_id": 1, "arr": [{"a": 2}]},
        msg="Should remove all docs where condition matches (implicit per-element query)",
    ),
    UpdateTestCase(
        "embedded_doc_condition_with_operator",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"x": 3},
                    {"x": 7},
                    {"x": 10},
                ],
            }
        ],
        query={"_id": 1},
        update={"$pull": {"arr": {"x": {"$gte": 7}}}},
        expected={"_id": 1, "arr": [{"x": 3}]},
        msg="Should remove embedded docs where field satisfies operator condition",
    ),
    UpdateTestCase(
        "elemmatch_on_nested_array",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"v": [3, 5, 6, 7]},
                    {"v": [1, 2, 3]},
                ],
            }
        ],
        query={"_id": 1},
        update={"$pull": {"arr": {"v": {"$elemMatch": {"$gte": 6}}}}},
        expected={"_id": 1, "arr": [{"v": [1, 2, 3]}]},
        msg="Should remove embedded docs whose nested array matches $elemMatch",
    ),
    UpdateTestCase(
        "top_level_elemmatch_noop",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"x": 8, "y": "B"},
                    {"x": 5, "y": "A"},
                    {"x": 8, "y": "C"},
                ],
            }
        ],
        query={"_id": 1},
        update={"$pull": {"arr": {"$elemMatch": {"x": 8, "y": "B"}}}},
        expected={
            "_id": 1,
            "arr": [
                {"x": 8, "y": "B"},
                {"x": 5, "y": "A"},
                {"x": 8, "y": "C"},
            ],
        },
        msg="Top-level $elemMatch in $pull condition should be a no-op (documented behavior)",
    ),
    UpdateTestCase(
        "dot_notation_condition_on_nested_field",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"x": {"y": 1}},
                    {"x": {"y": 2}},
                    {"x": {"y": 3}},
                ],
            }
        ],
        query={"_id": 1},
        update={"$pull": {"arr": {"x.y": {"$gte": 2}}}},
        expected={"_id": 1, "arr": [{"x": {"y": 1}}]},
        msg="Should support dot notation for conditions on nested embedded doc fields",
    ),
    UpdateTestCase(
        "dot_notation_target_nested_array",
        setup_docs=[{"_id": 1, "a": {"b": [1, 2, 3, 4]}}],
        query={"_id": 1},
        update={"$pull": {"a.b": 2}},
        expected={"_id": 1, "a": {"b": [1, 3, 4]}},
        msg="Should remove from nested array using dot notation",
    ),
    UpdateTestCase(
        "deep_dot_notation_target",
        setup_docs=[{"_id": 1, "a": {"b": {"c": [10, 20, 30]}}}],
        query={"_id": 1},
        update={"$pull": {"a.b.c": 20}},
        expected={"_id": 1, "a": {"b": {"c": [10, 30]}}},
        msg="Should remove from deeply nested array using dot notation",
    ),
    UpdateTestCase(
        "dot_notation_numeric_path_component",
        setup_docs=[{"_id": 1, "a": [{"b": [10, 20, 30]}, {"b": [40, 50]}]}],
        query={"_id": 1},
        update={"$pull": {"a.0.b": 20}},
        expected={"_id": 1, "a": [{"b": [10, 30]}, {"b": [40, 50]}]},
        msg="Should support numeric path component to index into array",
    ),
    UpdateTestCase(
        "deeply_nested_array_path",
        setup_docs=[{"_id": 1, "arr": [{"sub": {"items": [1, 2, 3]}}]}],
        query={"_id": 1},
        update={"$pull": {"arr.0.sub.items": 2}},
        expected={"_id": 1, "arr": [{"sub": {"items": [1, 3]}}]},
        msg="Should succeed on deeply nested array elements via dot path",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PULL_EMBEDDED_DOC_TESTS))
def test_pull_embedded_docs(collection, test: UpdateTestCase):
    """Test $pull with embedded documents, nested arrays, and dot notation."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
