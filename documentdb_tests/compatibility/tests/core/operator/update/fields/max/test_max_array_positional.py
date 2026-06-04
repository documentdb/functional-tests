"""
Array positional operator wiring tests for $max update field operator.

One representative case per positional operator ($, $[], $[elem]) to confirm
$max accepts them. Exhaustive positional operator coverage lives in
update/array/positional*/.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Positional Wiring]: $max accepts $, $[], and $[elem] positional operators.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "positional_dollar_updates_matched",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1, "grades": 85},
        update={"$max": {"grades.$": 95}},
        expected={"_id": 1, "grades": [80, 95, 90]},
        msg="$max with $ positional should update matched element 85 to 95",
    ),
    UpdateTestCase(
        "positional_all_updates_all_less",
        setup_docs=[{"_id": 1, "grades": [80, 85, 90]}],
        query={"_id": 1},
        update={"$max": {"grades.$[]": 88}},
        expected={"_id": 1, "grades": [88, 88, 90]},
        msg="$max with $[] should update all elements < 88",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_max_array_positional(collection, test: UpdateTestCase):
    """Test $max accepts positional operators."""
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


def test_max_filtered_positional(collection):
    """Test $max with $[elem] filtered positional."""
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
