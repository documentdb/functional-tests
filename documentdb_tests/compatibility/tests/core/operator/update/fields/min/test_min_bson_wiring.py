"""
Representative BSON comparison engine wiring tests for $min.

A small sample of cross-type comparisons to confirm $min delegates to the BSON
comparison engine correctly. Not an exhaustive matrix — full BSON ordering
coverage lives in /core/data_types/bson_types/.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_DATE = datetime(2023, 6, 15, tzinfo=timezone.utc)

# Property [BSON Wiring]: $min delegates to the BSON comparison engine for cross-type ordering.
TESTS: list[UpdateTestCase] = [
    # Downward transition: Boolean < Date in BSON order (should update for $min).
    UpdateTestCase(
        "boolean_less_than_date_updates",
        setup_docs=[{"_id": 1, "val": _DATE}],
        query={"_id": 1},
        update={"$min": {"val": True}},
        expected={"_id": 1, "val": True},
        msg="$min should update when Boolean < Date in BSON order",
    ),
    # Upward transition: String > Number in BSON order (should NOT update for $min).
    UpdateTestCase(
        "string_vs_number_unchanged",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$min": {"val": "hello"}},
        expected={"_id": 1, "val": 5},
        msg="$min should not update when String > Number in BSON order",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_min_bson_wiring(collection, test: UpdateTestCase):
    """Smoke test: confirm $min is wired to the BSON comparison engine."""
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
