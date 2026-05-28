"""Tests for dbHash command argument validation."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


@dataclass(frozen=True)
class DbHashArgTest(BaseTestCase):
    value: Any = None


# dbHash ignores the command field value — all types should succeed
ARG_TYPE_TESTS: list[DbHashArgTest] = [
    DbHashArgTest("int_1", value=1, msg="int should succeed"),
    DbHashArgTest("int_0", value=0, msg="int 0 should succeed"),
    DbHashArgTest("double", value=1.5, msg="double should succeed"),
    DbHashArgTest("long", value=Int64(1), msg="long should succeed"),
    DbHashArgTest("decimal128", value=Decimal128("1"), msg="decimal128 should succeed"),
    DbHashArgTest("string", value="test", msg="string should succeed"),
    DbHashArgTest("bool_true", value=True, msg="bool true should succeed"),
    DbHashArgTest("bool_false", value=False, msg="bool false should succeed"),
    DbHashArgTest(
        "date", value=datetime(2024, 1, 1, tzinfo=timezone.utc), msg="date should succeed"
    ),
    DbHashArgTest("null", value=None, msg="null should succeed"),
    DbHashArgTest("object", value={}, msg="object should succeed"),
    DbHashArgTest("array", value=[], msg="array should succeed"),
    DbHashArgTest("binData", value=Binary(b""), msg="binData should succeed"),
    DbHashArgTest("objectId", value=ObjectId(), msg="objectId should succeed"),
    DbHashArgTest("regex", value=Regex("test"), msg="regex should succeed"),
    DbHashArgTest("timestamp", value=Timestamp(0, 0), msg="timestamp should succeed"),
    DbHashArgTest("minKey", value=MinKey(), msg="minKey should succeed"),
    DbHashArgTest("maxKey", value=MaxKey(), msg="maxKey should succeed"),
]


@pytest.mark.parametrize("test", pytest_params(ARG_TYPE_TESTS))
def test_dbHash_accepts_any_type(collection, test):
    """Test dbHash accepts all BSON types for command field value."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": test.value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=test.msg)


def test_dbHash_unrecognized_field(collection):
    """Test dbHash with unrecognized extra field succeeds."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1, "foo": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Unrecognized field should be ignored")
