"""
Tests for $unset update operator - array element behavior.

Covers null replacement on array elements, positional operators, and arrayFilters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UNSET_ARRAY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="first_element",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.0": ""}},
        expected=[{"_id": 1, "arr": [None, 2, 3]}],
        msg="$unset first element should replace with null",
    ),
    UpdateTestCase(
        id="middle_element",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.1": ""}},
        expected=[{"_id": 1, "arr": [1, None, 3]}],
        msg="$unset middle element should replace with null",
    ),
    UpdateTestCase(
        id="last_element",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.2": ""}},
        expected=[{"_id": 1, "arr": [1, 2, None]}],
        msg="$unset last element should replace with null",
    ),
    UpdateTestCase(
        id="out_of_bounds",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.5": ""}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$unset out-of-bounds index should be no-op",
    ),
    UpdateTestCase(
        id="embedded_field_in_array",
        setup_docs=[{"_id": 1, "arr": [{"field": 1, "other": 2}]}],
        query={"_id": 1},
        update={"$unset": {"arr.0.field": ""}},
        expected=[{"_id": 1, "arr": [{"other": 2}]}],
        msg="$unset embedded field in array element should remove only that field",
    ),
    UpdateTestCase(
        id="positional_operator",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": 2},
        update={"$unset": {"arr.$": ""}},
        expected=[{"_id": 1, "arr": [1, None, 3]}],
        msg="$ positional should set matching element to null",
    ),
    UpdateTestCase(
        id="all_positional_field",
        setup_docs=[{"_id": 1, "arr": [{"field": 1, "keep": "a"}, {"field": 2, "keep": "b"}]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[].field": ""}},
        expected=[{"_id": 1, "arr": [{"keep": "a"}, {"keep": "b"}]}],
        msg="$[] should remove field from all elements",
    ),
    UpdateTestCase(
        id="multiple_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$unset": {"arr.0": "", "arr.2": "", "arr.4": ""}},
        expected=[{"_id": 1, "arr": [None, 2, None, 4, None]}],
        msg="$unset multiple elements in same update should null each",
    ),
    UpdateTestCase(
        id="nested_array_element",
        setup_docs=[{"_id": 1, "arr": [[10, 20, 30], [40, 50]]}],
        query={"_id": 1},
        update={"$unset": {"arr.0.1": ""}},
        expected=[{"_id": 1, "arr": [[10, None, 30], [40, 50]]}],
        msg="$unset on nested array element should null inner element",
    ),
    UpdateTestCase(
        id="negative_index",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.-1": ""}},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$unset with negative index should be no-op",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_ARRAY_TESTS))
def test_unset_array_behavior(collection, test):
    """Test $unset on array elements."""
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


UNSET_ARRAY_FILTER_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="filtered_positional_removes_field",
        setup_docs=[
            {"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 5, "y": "b"}, {"x": 3, "y": "c"}]}
        ],
        query={"_id": 1},
        update={"$unset": {"arr.$[elem].y": ""}},
        expected=[{"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 5}, {"x": 3}]}],
        msg="$unset with arrayFilters should remove field from matching elements only",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_ARRAY_FILTER_TESTS))
def test_unset_with_array_filters(collection, test):
    """Test $unset with arrayFilters."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": test.query,
                    "u": test.update,
                    "arrayFilters": [{"elem.x": {"$gt": 2}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)
