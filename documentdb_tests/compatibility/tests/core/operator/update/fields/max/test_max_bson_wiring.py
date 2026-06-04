"""
Representative BSON comparison engine wiring tests for $max.

A small sample of cross-type comparisons to confirm $max delegates to the BSON
comparison engine correctly. Not an exhaustive matrix — full BSON ordering
coverage lives in /core/data_types/bson_types/.
"""

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TESTS: list[UpdateTestCase] = [
    # Upward transition in BSON order (should update)
    UpdateTestCase(
        "null_to_number_updates",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": 1}},
        expected={"_id": 1, "val": 1},
        msg="Number > Null in BSON order, should update",
    ),
    # Downward transition in BSON order (should NOT update)
    UpdateTestCase(
        "string_vs_objectid_unchanged",
        setup_docs=[{"_id": 1, "val": ObjectId("000000000000000000000001")}],
        query={"_id": 1},
        update={"$max": {"val": "zzz"}},
        expected={"_id": 1, "val": ObjectId("000000000000000000000001")},
        msg="String < ObjectId in BSON order, should not update",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_max_bson_wiring(collection, test: UpdateTestCase):
    """Smoke test: confirm $max is wired to the BSON comparison engine."""
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
