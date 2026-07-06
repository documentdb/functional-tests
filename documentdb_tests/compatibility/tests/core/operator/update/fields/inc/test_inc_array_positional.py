"""
Array positional operator wiring tests for $inc update field operator.

One representative case per positional operator ($, $[], $[elem]) to confirm
$inc accepts them. Exhaustive positional operator coverage lives in
update/array/positional*/.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Positional Wiring]: $inc accepts $, $[], and $[elem] positional operators.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "positional_dollar_increments_matched",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1, "grades": 85},
        update={"$inc": {"grades.$": 5}},
        expected={"_id": 1, "grades": [80, 90, 90]},
        msg="$inc with $ positional should increment matched element 85 to 90",
    ),
    UpdateTestCase(
        "positional_all_increments_all",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1},
        update={"$inc": {"grades.$[]": 10}},
        expected={"_id": 1, "grades": [90, 95, 100]},
        msg="$inc with $[] should increment all elements by 10",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_inc_array_positional(collection, test: UpdateTestCase):
    """Test $inc accepts positional operators."""
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


def test_inc_filtered_positional(collection):
    """Test $inc with $[elem] filtered positional."""
    collection.insert_many([{"_id": 1, "grades": [80, 85, 90, 70]}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$inc": {"grades.$[elem]": 100}},
                    "arrayFilters": [{"elem": {"$gt": 80}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "grades": [80, 185, 190, 70]}],
        msg="$inc with $[elem] should increment elements > 80 by 100",
    )
