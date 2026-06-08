"""
Array positional operator wiring tests for $min update field operator.

One representative case per positional operator ($, $[], $[elem]) to confirm
$min accepts them. Exhaustive positional operator coverage lives in
update/array/positional*/.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Positional Wiring]: $min accepts $, $[], and $[elem] positional operators.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "positional_dollar_updates_matched",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1, "grades": 85},
        update={"$min": {"grades.$": 70}},
        expected={"_id": 1, "grades": [80, 70, 90]},
        msg="$min with $ positional should update matched element 85 to 70",
    ),
    UpdateTestCase(
        "positional_all_updates_all_greater",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1},
        update={"$min": {"grades.$[]": 83}},
        expected={"_id": 1, "grades": [80, 83, 83]},
        msg="$min with $[] should update all elements > 83",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_min_array_positional(collection, test: UpdateTestCase):
    """Test $min accepts positional operators."""
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


def test_min_filtered_positional(collection):
    """Test $min with $[elem] filtered positional."""
    collection.insert_many([{"_id": 1, "grades": [80, 85, 90, 70]}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$min": {"grades.$[elem]": 80}},
                    "arrayFilters": [{"elem": {"$gt": 80}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "grades": [80, 80, 80, 70]}],
        msg="$min with $[elem] should update elements > 80 to 80",
    )
