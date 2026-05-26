"""Tests for connPoolStats command argument validation.

Verifies that connPoolStats accepts all BSON types for the command field
value and ignores unrecognized fields.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


@dataclass(frozen=True)
class ConnPoolArgTest(BaseTestCase):
    value: Any = None


# connPoolStats ignores the command field value — all types should succeed
ARG_TYPE_TESTS: list[ConnPoolArgTest] = [
    ConnPoolArgTest("int_1", value=1, msg="int should succeed"),
    ConnPoolArgTest("int_0", value=0, msg="int 0 should succeed"),
    ConnPoolArgTest("double", value=1.5, msg="double should succeed"),
    ConnPoolArgTest("long", value=Int64(1), msg="long should succeed"),
    ConnPoolArgTest("decimal128", value=Decimal128("1"), msg="decimal128 should succeed"),
    ConnPoolArgTest("string", value="test", msg="string should succeed"),
    ConnPoolArgTest("bool_true", value=True, msg="bool true should succeed"),
    ConnPoolArgTest("bool_false", value=False, msg="bool false should succeed"),
    ConnPoolArgTest(
        "date", value=datetime(2024, 1, 1, tzinfo=timezone.utc), msg="date should succeed"
    ),
    ConnPoolArgTest("null", value=None, msg="null should succeed"),
    ConnPoolArgTest("object", value={}, msg="object should succeed"),
    ConnPoolArgTest("array", value=[], msg="array should succeed"),
    ConnPoolArgTest("binData", value=Binary(b""), msg="binData should succeed"),
    ConnPoolArgTest("objectId", value=ObjectId(), msg="objectId should succeed"),
    ConnPoolArgTest("regex", value=Regex("test"), msg="regex should succeed"),
    ConnPoolArgTest("timestamp", value=Timestamp(0, 0), msg="timestamp should succeed"),
    ConnPoolArgTest("minKey", value=MinKey(), msg="minKey should succeed"),
    ConnPoolArgTest("maxKey", value=MaxKey(), msg="maxKey should succeed"),
    ConnPoolArgTest("code", value=Code("function(){}"), msg="code should succeed"),
]


@pytest.mark.parametrize("test", pytest_params(ARG_TYPE_TESTS))
def test_connPoolStats_accepts_any_type(collection, test):
    """Test connPoolStats accepts all BSON types for command field value."""
    result = execute_admin_command(collection, {"connPoolStats": test.value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=test.msg)


def test_connPoolStats_unrecognized_field(collection):
    """Test connPoolStats with unrecognized extra field succeeds."""
    result = execute_admin_command(collection, {"connPoolStats": 1, "foo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Unrecognized field should be ignored")


def test_connPoolStats_multiple_unrecognized_fields(collection):
    """Test connPoolStats with multiple unrecognized fields succeeds."""
    result = execute_admin_command(
        collection, {"connPoolStats": 1, "foo": 1, "bar": "baz", "qux": []}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Multiple unrecognized fields should be ignored")
