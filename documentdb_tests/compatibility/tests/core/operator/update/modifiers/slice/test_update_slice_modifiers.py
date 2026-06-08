"""Tests for $slice modifier interactions with $sort and $position.

Covers: $slice + $sort ascending/descending, $slice + $position,
$slice + $sort + $position combined, modifier key order immateriality,
non-document array elements with $sort, and $sort error cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

MODIFIER_TESTS: list[UpdateTestCase] = [
    # --- $slice with $sort ---
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
        id="sort_by_nested_field_then_slice",
        setup_docs=[{"_id": 1, "arr": [{"a": {"b": 3}}, {"a": {"b": 1}}]}],
        query={"_id": 1},
        update={
            "$push": {
                "arr": {
                    "$each": [{"a": {"b": 2}}],
                    "$sort": {"a.b": 1},
                    "$slice": -2,
                }
            }
        },
        expected=[{"_id": 1, "arr": [{"a": {"b": 2}}, {"a": {"b": 3}}]}],
        msg="$sort by nested field path then $slice -2",
    ),
    UpdateTestCase(
        id="sort_larger_slice_keeps_all",
        setup_docs=[{"_id": 1, "arr": [{"x": 3}, {"x": 1}]}],
        query={"_id": 1},
        update={
            "$push": {"arr": {"$each": [{"x": 5}, {"x": 2}], "$sort": {"x": 1}, "$slice": -100}}
        },
        expected=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}, {"x": 3}, {"x": 5}]}],
        msg="$sort then $slice larger than array should keep all sorted",
    ),
    # --- $slice with $position ---
    UpdateTestCase(
        id="position_0_then_slice",
        setup_docs=[{"_id": 1, "arr": [20, 30, 40]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [10], "$position": 0, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="$position 0 inserts at beginning, then $slice 2 keeps first 2",
    ),
    # --- $slice + $sort + $position combined ---
    UpdateTestCase(
        id="position_sort_slice_combined",
        setup_docs=[{"_id": 1, "arr": [30, 10]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [20], "$position": 0, "$sort": 1, "$slice": 2}}},
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="Combined $position, $sort, $slice: position, then sort, then slice",
    ),
    # --- Modifier key order is immaterial ---
    UpdateTestCase(
        id="modifier_order_slice_each_sort",
        setup_docs=[{"_id": 1, "arr": [5, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$slice": -3, "$each": [1, 2], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [2, 3, 5]}],
        msg="Modifier key order should not affect result",
    ),
    # --- Non-document elements with document field $sort ---
    UpdateTestCase(
        id="sort_field_on_non_doc_elements_succeeds",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [4], "$sort": {"x": 1}, "$slice": -3}}},
        expected=[{"_id": 1, "arr": [2, 3, 4]}],
        msg="Document field $sort on non-document array should succeed",
    ),
    UpdateTestCase(
        id="sort_scalar_on_mixed_elements",
        setup_docs=[{"_id": 1, "arr": [{"x": 2}, 5, {"x": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3], "$sort": 1, "$slice": -3}}},
        expected=[{"_id": 1, "arr": [5, {"x": 1}, {"x": 2}]}],
        msg="Scalar $sort on mixed doc/non-doc elements should succeed",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MODIFIER_TESTS))
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


# --- Error cases for $sort with $slice ---

SORT_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="empty_sort_object",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3], "$sort": {}, "$slice": -2}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty $sort object with $slice should fail",
    ),
    UpdateTestCase(
        id="invalid_sort_direction",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3], "$sort": {"x": 2}, "$slice": -2}}},
        error_code=BAD_VALUE_ERROR,
        msg="Invalid $sort direction (not 1 or -1) should fail",
    ),
    UpdateTestCase(
        id="trailing_dot_sort_key",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [{"x": 2}], "$sort": {"x.": 1}, "$slice": -2}}},
        error_code=BAD_VALUE_ERROR,
        msg="Trailing dot in $sort key path should fail",
    ),
    UpdateTestCase(
        id="empty_string_sort_key",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [{"x": 2}], "$sort": {"": 1}, "$slice": -2}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty string $sort key should fail",
    ),
    UpdateTestCase(
        id="unrecognized_modifier",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [3], "$slice": -2, "$xxx": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Unrecognized modifier ($xxx) should fail",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SORT_ERROR_TESTS))
def test_update_slice_sort_errors(collection, test_case):
    """Test error cases for $sort used with $slice."""
    collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
