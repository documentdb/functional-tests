"""Tests for connectionStatus command argument validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


@dataclass(frozen=True)
class ConnStatusArgTest(BaseTestCase):
    value: Any = None


# connectionStatus ignores the command field value — all types should succeed
ARG_TYPE_TESTS: list[ConnStatusArgTest] = [
    ConnStatusArgTest("int_1", value=1, msg="int should succeed"),
    ConnStatusArgTest("int_0", value=0, msg="int 0 should succeed"),
    ConnStatusArgTest("double", value=1.5, msg="double should succeed"),
    ConnStatusArgTest("long", value=Int64(1), msg="long should succeed"),
    ConnStatusArgTest("decimal128", value=Decimal128("1"), msg="decimal128 should succeed"),
    ConnStatusArgTest("string", value="test", msg="string should succeed"),
    ConnStatusArgTest("bool_true", value=True, msg="bool true should succeed"),
    ConnStatusArgTest("bool_false", value=False, msg="bool false should succeed"),
    ConnStatusArgTest(
        "date", value=datetime(2024, 1, 1, tzinfo=timezone.utc), msg="date should succeed"
    ),
    ConnStatusArgTest("null", value=None, msg="null should succeed"),
    ConnStatusArgTest("object", value={}, msg="object should succeed"),
    ConnStatusArgTest("array", value=[], msg="array should succeed"),
    ConnStatusArgTest("binData", value=Binary(b""), msg="binData should succeed"),
    ConnStatusArgTest("objectId", value=ObjectId(), msg="objectId should succeed"),
    ConnStatusArgTest("regex", value=Regex("test"), msg="regex should succeed"),
    ConnStatusArgTest("timestamp", value=Timestamp(0, 0), msg="timestamp should succeed"),
    ConnStatusArgTest("minKey", value=MinKey(), msg="minKey should succeed"),
    ConnStatusArgTest("maxKey", value=MaxKey(), msg="maxKey should succeed"),
]


@pytest.mark.parametrize("test", pytest_params(ARG_TYPE_TESTS))
def test_connectionStatus_accepts_any_type(collection, test):
    """Test connectionStatus accepts all BSON types for command field value."""
    result = execute_admin_command(collection, {"connectionStatus": test.value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=test.msg)


def test_connectionStatus_unrecognized_field(collection):
    """Test connectionStatus with unrecognized extra field returns error."""
    result = execute_admin_command(collection, {"connectionStatus": 1, "foo": 1})
    assertFailureCode(
        result, UNRECOGNIZED_COMMAND_FIELD_ERROR, msg="Unrecognized field should error"
    )
