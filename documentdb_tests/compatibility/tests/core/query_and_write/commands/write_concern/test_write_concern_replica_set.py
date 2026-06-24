"""
writeConcern replica set tests.

Tests writeConcern behaviors that require a replica set topology, such as
w values greater than 1.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.query_and_write.commands.write_concern.utils import (
    WRITE_COMMANDS,
    build_cmd,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertNotError
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(quorum_write_concern=True)

_W_REPLICA_VALUES = [
    ("w_50_max", {"w": 50}),
    ("w_int64_50", {"w": Int64(50)}),
]

# Property [w Large Values]: w up to 50 is accepted on a replica set.
W_REPLICA_SET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_{val_name}",
        docs=[{"_id": 1}],
        command=lambda ctx, _wc=value, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        msg=f"{cmd} should accept {val_name} on replica set.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value in _W_REPLICA_VALUES
]


@pytest.mark.parametrize("test", pytest_params(W_REPLICA_SET_TESTS))
def test_write_concern_w_replica_set(collection, test: CommandTestCase):
    """Test w values requiring replica set are accepted."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertNotError(result, msg=test.msg)
