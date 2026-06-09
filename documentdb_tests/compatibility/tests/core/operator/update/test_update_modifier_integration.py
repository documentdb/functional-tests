"""Integration tests for update modifier operators.

Tests that verify interactions between modifier operators ($position, $slice,
$sort) and other update operators, ensuring correct combined behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SLICE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_asc_then_slice_positive",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$sort asc then $slice 3 should keep first 3 of sorted",
    ),
    UpdateTestCase(
        id="sort_asc_then_slice_negative",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": 1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [4, 5]}],
        msg="$sort asc then $slice -2 should keep last 2 of sorted",
    ),
    UpdateTestCase(
        id="sort_desc_then_slice_positive",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": -1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [5, 4, 3]}],
        msg="$sort desc then $slice 3 should keep first 3 of desc sorted",
    ),
    UpdateTestCase(
        id="sort_desc_then_slice_negative",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 4, 2], "$sort": -1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [2, 1]}],
        msg="$sort desc then $slice -2 should keep last 2 of desc sorted",
    ),
    UpdateTestCase(
        id="sort_by_field_then_slice",
        setup_docs=[{"_id": 1, "arr": [{"x": 3}, {"x": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [{"x": 5}, {"x": 2}], "$sort": {"x": 1}, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [{"x": 3}, {"x": 5}]}],
        msg="$sort by field then $slice -2 should keep last 2 sorted by field",
    ),
    UpdateTestCase(
        id="position_0_then_slice",
        setup_docs=[{"_id": 1, "arr": [20, 30, 40]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [10], "$position": 0, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="$position 0 inserts at beginning, then $slice 2 keeps first 2",
    ),
    UpdateTestCase(
        id="slice_position_sort_combined",
        setup_docs=[{"_id": 1, "arr": [30, 10]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20], "$position": 0, "$sort": 1, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="Combined $position, $sort, $slice: position, then sort, then slice",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SLICE_TESTS))
def test_update_slice_modifiers(collection, test_case):
    """Test $slice modifier interactions with $sort and $position."""
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


POSITION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="position_with_positive_slice",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2], "$position": 0, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [1, 2, 10]}],
        msg="$position 0 + $slice 3 should insert then keep first 3",
    ),
    UpdateTestCase(
        id="position_with_negative_slice",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [1, 2], "$position": 0, "$slice": -3}}},
        expected=[{"_id": 1, "arr": [10, 20, 30]}],
        msg="$position 0 + $slice -3 should insert then keep last 3",
    ),
    UpdateTestCase(
        id="position_with_sort_ascending",
        setup_docs=[{"_id": 1, "arr": [30, 10, 20]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5], "$position": 0, "$sort": 1}}},
        expected=[{"_id": 1, "arr": [5, 10, 20, 30]}],
        msg="$sort should override $position — array sorted ascending",
    ),
    UpdateTestCase(
        id="position_with_sort_descending",
        setup_docs=[{"_id": 1, "arr": [10, 30, 20]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [5], "$position": 0, "$sort": -1}}},
        expected=[{"_id": 1, "arr": [30, 20, 10, 5]}],
        msg="$sort descending should override $position",
    ),
    UpdateTestCase(
        id="position_sort_slice_combined",
        setup_docs=[{"_id": 1, "arr": [30, 10]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20, 5], "$position": 0, "$sort": 1, "$slice": 3}}},
        expected=[{"_id": 1, "arr": [5, 10, 20]}],
        msg="All modifiers: insert, sort ascending, then slice first 3",
    ),
    UpdateTestCase(
        id="position_sort_negative_slice_combined",
        setup_docs=[{"_id": 1, "arr": [30, 10]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20, 5], "$position": 0, "$sort": 1, "$slice": -2}}},
        expected=[{"_id": 1, "arr": [20, 30]}],
        msg="All modifiers: insert, sort ascending, then slice last 2",
    ),
    UpdateTestCase(
        id="set_treats_position_as_literal",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1, "arr": {"$each": [3], "$position": 0}}],
        msg="$set should treat $position doc as a literal value",
    ),
    UpdateTestCase(
        id="unset_ignores_position_doc",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1}],
        msg="$unset should ignore $position doc and remove the field",
    ),
    UpdateTestCase(
        id="min_treats_position_as_literal",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$min": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1, "arr": {"$each": [3], "$position": 0}}],
        msg="$min should treat $position doc as a literal value",
    ),
    UpdateTestCase(
        id="max_keeps_original_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$max": {"arr": {"$each": [3], "$position": 0}}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$max should keep original array (array > document in BSON comparison)",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(POSITION_TESTS))
def test_position_update_modifier_integration(collection, test_case):
    """Test $position interaction with modifiers and non-$push operators."""
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


EACH_INTEGRATION_TESTS: list[UpdateTestCase] = [
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


@pytest.mark.parametrize("test_case", pytest_params(EACH_INTEGRATION_TESTS))
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
