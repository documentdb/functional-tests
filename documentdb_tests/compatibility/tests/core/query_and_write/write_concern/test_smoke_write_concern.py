"""writeConcern smoke test: a basic insert with w:1 succeeds."""

from typing import Any, Dict, cast

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.smoke

SMOKE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "insert_w1",
        command={
            "documents": [{"_id": 1, "name": "test"}],
            "writeConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0), "n": Eq(1)},
        msg="Should support writeConcern",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SMOKE_TESTS))
def test_smoke_write_concern(collection, test: CommandTestCase):
    """Test basic writeConcern behavior."""
    insert_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"insert": collection.name, **insert_body})
    assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)
