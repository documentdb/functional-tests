"""Tests for update modifier integration: $sort, $slice, and $position with $each."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

MODIFIER_INTEGRATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="slice_trims",
        setup_docs=[{"_id": 1, "arr": [0]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2, 3], "$slice": -2}}},
        expected=[{"_id": 1, "arr": [2, 3]}],
        msg="$push $each with $slice -2 should keep last 2 elements",
    ),
    UpdateTestCase(
        id="slice_empty_each_trims",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$slice": 2}}},
        expected=[{"_id": 1, "arr": [1, 2]}],
        msg="$push $each: [] with $slice should trim existing array",
    ),
    UpdateTestCase(
        id="sort_ascending",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        msg="$push $each with $sort: 1 should sort all elements ascending",
    ),
    UpdateTestCase(
        id="sort_descending",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": -1}}},
        expected=[{"_id": 1, "arr": [5, 4, 3, 2, 1]}],
        msg="$push $each with $sort: -1 should sort all elements descending",
    ),
    UpdateTestCase(
        id="sort_empty_each",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$push $each: [] with $sort should sort existing array",
    ),
    UpdateTestCase(
        id="sort_by_field",
        setup_docs=[{"_id": 1, "arr": [{"x": 3}, {"x": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [{"x": 2}], "$sort": {"x": 1}}}},
        expected=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}, {"x": 3}]}],
        msg="$push $each with $sort by field should sort documents by that field",
    ),
    UpdateTestCase(
        id="position_beginning",
        setup_docs=[{"_id": 1, "arr": [3, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2], "$position": 0}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        msg="$push $each with $position: 0 should insert at beginning",
    ),
    UpdateTestCase(
        id="position_middle",
        setup_docs=[{"_id": 1, "arr": [1, 4]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2, 3], "$position": 1}}},
        expected=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        msg="$push $each with $position: 1 should insert at index 1",
    ),
    UpdateTestCase(
        id="all_combined",
        setup_docs=[{"_id": 1, "arr": [{"x": 5}, {"x": 3}]}],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {
                    "$each": [{"x": 1}, {"x": 4}],
                    "$sort": {"x": 1},
                    "$slice": -3,
                }
            }
        },
        expected=[{"_id": 1, "arr": [{"x": 3}, {"x": 4}, {"x": 5}]}],
        msg="$push with $each, $sort, $slice should sort then trim",
    ),
    UpdateTestCase(
        id="sort_then_slice",
        setup_docs=[{"_id": 1, "arr": [{"x": 10}]}],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {
                    "$each": [{"x": 5}, {"x": 20}],
                    "$sort": {"x": 1},
                    "$slice": -2,
                }
            }
        },
        expected=[{"_id": 1, "arr": [{"x": 10}, {"x": 20}]}],
        msg="$push $each with $sort and $slice -2 should keep last 2 after sorting",
    ),
    UpdateTestCase(
        id="sort_scalar_on_non_documents",
        setup_docs=[{"_id": 1, "arr": [3, 1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [2], "$sort": 1, "$slice": -3}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$push $each with scalar $sort should sort non-document elements",
    ),
    UpdateTestCase(
        id="sort_nested_field",
        setup_docs=[{"_id": 1, "arr": [{"a": {"b": 3}}, {"a": {"b": 1}}]}],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {
                    "$each": [{"a": {"b": 2}}],
                    "$sort": {"a.b": 1},
                    "$slice": 10,
                }
            }
        },
        expected=[
            {
                "_id": 1,
                "arr": [{"a": {"b": 1}}, {"a": {"b": 2}}, {"a": {"b": 3}}],
            }
        ],
        msg="$push $each with nested field $sort should sort by nested path",
    ),
    UpdateTestCase(
        id="set_treats_each_as_literal",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr": {"$each": [1]}}},
        expected=[{"_id": 1, "arr": {"$each": [1]}}],
        msg="$set should treat $each as a literal document value",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MODIFIER_INTEGRATION_TESTS))
def test_update_modifier_integration(collection, test_case):
    """Test update modifier integration: $sort, $slice, and $position with $each."""
    collection.insert_many(test_case.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test_case.query})
    assertSuccess(result, test_case.expected, msg=test_case.msg)
