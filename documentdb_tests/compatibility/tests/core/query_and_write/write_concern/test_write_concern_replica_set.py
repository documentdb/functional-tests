"""writeConcern w values > 1 (up to 50), accepted only on a replica set.
Deselected on standalone targets.
"""

from typing import Any, Dict, cast

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.requires(quorum_write_concern=True)


W_REPLICA_SET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_2",
        command={"updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": 2}},
        expected={"ok": Eq(1.0)},
        msg="w:2 should be accepted on a replica set.",
    ),
    CommandTestCase(
        "w_50_max",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 50},
        },
        expected={"ok": Eq(1.0)},
        msg="w:50 (max) should be accepted on a replica set.",
    ),
    CommandTestCase(
        "w_int64_50",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": Int64(50)},
        },
        expected={"ok": Eq(1.0)},
        msg="w as Int64(50) should be accepted on a replica set.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(W_REPLICA_SET_TESTS))
def test_write_concern_w_replica_set(collection, test: CommandTestCase):
    """Test writeConcern accepts w values requiring a replica set."""
    collection.insert_one({"_id": 1, "a": 0})
    update_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"update": collection.name, **update_body})
    assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)
