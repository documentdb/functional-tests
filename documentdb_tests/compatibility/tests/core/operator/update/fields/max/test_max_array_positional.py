"""
Array positional operator tests for $max update field operator.

Tests $max with $, $[], and $[<identifier>] positional operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CHANGED_DOC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "positional_operator_updates_matched",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1, "grades": 85},
        update={"$max": {"grades.$": 95}},
        expected={"_id": 1, "grades": [80, 95, 90]},
        msg="$max with $ positional should update matched element 85 to 95",
    ),
    UpdateTestCase(
        "all_positional_updates_all",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1},
        update={"$max": {"grades.$[]": 88}},
        expected={"_id": 1, "grades": [88, 88, 90]},
        msg="$max with $[] should update all elements < 88",
    ),
]

UPDATE_RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "positional_operator_no_update_when_less",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1, "grades": 85},
        update={"$max": {"grades.$": 70}},
        expected={"n": 1, "nModified": 0},
        msg="$max with $ positional where 70 < 85 should not update",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CHANGED_DOC_TESTS))
def test_max_positional_changed_doc(collection, test: UpdateTestCase):
    """Test $max with positional operators produces expected document."""
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


@pytest.mark.parametrize("test", pytest_params(UPDATE_RESULT_TESTS))
def test_max_positional_update_result(collection, test: UpdateTestCase):
    """Test $max with positional operators returns expected update result."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_max_filtered_positional(collection):
    """Test $max with $[elem] filtered positional targeting elements < 85."""
    collection.insert_many([{"_id": 1, "grades": [80, 85, 90, 70]}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$max": {"grades.$[elem]": 85}},
                    "arrayFilters": [{"elem": {"$lt": 85}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "grades": [85, 85, 90, 85]}],
        msg="$max with $[elem] should update elements < 85 to 85",
    )


def test_max_filtered_positional_nested(collection):
    """Test $max with arrayFilters targeting nested array elements."""
    collection.insert_many(
        [{"_id": 1, "items": [{"name": "a", "score": 10}, {"name": "b", "score": 50}]}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$max": {"items.$[elem].score": 30}},
                    "arrayFilters": [{"elem.name": "a"}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "items": [{"name": "a", "score": 30}, {"name": "b", "score": 50}]}],
        msg="$max with arrayFilters targeting nested elements should update matched element",
    )
