"""
readConcern snapshot outside transaction tests.

Verifies that readConcern level 'snapshot' is rejected when used outside
a multi-document transaction.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    NOT_A_REPLICA_SET_ERROR,
)
from documentdb_tests.framework.executor import execute_command

_SNAPSHOT_REPL_SET_PARAMS = [
    pytest.param(
        lambda coll: {"find": coll, "filter": {}, "readConcern": {"level": "snapshot"}},
        id="find_snapshot_outside_transaction",
    ),
    pytest.param(
        lambda coll: {
            "aggregate": coll,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "snapshot"},
        },
        id="aggregate_snapshot_outside_transaction",
    ),
    pytest.param(
        lambda coll: {"distinct": coll, "key": "_id", "readConcern": {"level": "snapshot"}},
        id="distinct_snapshot_outside_transaction",
    ),
]


@pytest.mark.parametrize("build_command", _SNAPSHOT_REPL_SET_PARAMS)
def test_read_concern_snapshot_outside_transaction(collection, build_command):
    """Test readConcern 'snapshot' outside a transaction is rejected."""
    collection.insert_many([{"_id": 1}])
    command = build_command(collection.name)
    result = execute_command(collection, command)
    assertFailureCode(
        result,
        NOT_A_REPLICA_SET_ERROR,
        msg="readConcern 'snapshot' should be rejected outside a transaction.",
    )


def test_count_snapshot_outside_transaction(collection):
    """Test count with readConcern 'snapshot' outside a transaction is rejected."""
    collection.insert_many([{"_id": 1}])
    result = execute_command(
        collection,
        {"count": collection.name, "query": {}, "readConcern": {"level": "snapshot"}},
    )
    assertFailureCode(
        result,
        INVALID_OPTIONS_ERROR,
        msg="count with readConcern 'snapshot' should be rejected outside a transaction.",
    )
