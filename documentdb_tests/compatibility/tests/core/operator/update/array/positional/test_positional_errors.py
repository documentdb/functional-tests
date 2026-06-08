"""Tests for $ positional update operator error cases.

Covers: missing array field in query, upsert restriction, negation operators,
and multiple positional operators in update path.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "no_array_field_in_query",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$ without array field in query should fail with BadValue",
    ),
    UpdateTestCase(
        "upsert_no_match_fails",
        setup_docs=None,
        query={"arr": 5},
        update={"$set": {"arr.$": 99}},
        upsert=True,
        error_code=BAD_VALUE_ERROR,
        msg="$ in upsert when no document exists should fail (cannot determine position)",
    ),
    UpdateTestCase(
        "ne_on_array_field",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": {"$ne": 5}},
        update={"$set": {"arr.$": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$ with $ne on array field should fail",
    ),
    UpdateTestCase(
        "not_on_array_field",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": {"$not": {"$eq": 5}}},
        update={"$set": {"arr.$": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$ with $not on array field should fail",
    ),
    UpdateTestCase(
        "nin_on_array_field",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": {"$nin": [5, 6]}},
        update={"$set": {"arr.$": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$ with $nin on array field should fail",
    ),
    UpdateTestCase(
        "multiple_positional_in_path",
        setup_docs=[
            {"_id": 1, "arr": [{"items": [1, 2]}, {"items": [3, 4]}]},
        ],
        query={"arr.items": 3},
        update={"$set": {"arr.$.items.$": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$ used twice in update path should fail (cannot traverse multiple arrays)",
    ),
    UpdateTestCase(
        "field_exists_but_not_array",
        setup_docs=[{"_id": 1, "arr": 5}],
        query={"_id": 1, "arr": 5},
        update={"$set": {"arr.$": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$ on scalar field should fail even when query matches",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_positional_errors(collection, test):
    """Test $ positional update operator error cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.upsert:
        update_doc["upsert"] = True
    command = {"update": collection.name, "updates": [update_doc]}
    result = execute_command(collection, command)
    assertFailureCode(result, test.error_code, msg=test.msg)
