"""Tests for abortTransaction comment parameter type acceptance in a real transaction.

Validates that the comment parameter accepts any BSON type when
abortTransaction is issued inside an active transaction on a replica set.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]

# Property [comment Type Acceptance]: comment accepts any BSON type.
COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_string",
        command={"abortTransaction": 1, "comment": "test comment"},
        msg="abortTransaction should accept comment:string",
    ),
    CommandTestCase(
        "comment_string_empty",
        command={"abortTransaction": 1, "comment": ""},
        msg="abortTransaction should accept comment:empty string",
    ),
    CommandTestCase(
        "comment_int32",
        command={"abortTransaction": 1, "comment": 42},
        msg="abortTransaction should accept comment:int32",
    ),
    CommandTestCase(
        "comment_int64",
        command={"abortTransaction": 1, "comment": Int64(42)},
        msg="abortTransaction should accept comment:Int64",
    ),
    CommandTestCase(
        "comment_double",
        command={"abortTransaction": 1, "comment": 3.14},
        msg="abortTransaction should accept comment:double",
    ),
    CommandTestCase(
        "comment_decimal128",
        command={"abortTransaction": 1, "comment": Decimal128("1.5")},
        msg="abortTransaction should accept comment:Decimal128",
    ),
    CommandTestCase(
        "comment_bool_true",
        command={"abortTransaction": 1, "comment": True},
        msg="abortTransaction should accept comment:true",
    ),
    CommandTestCase(
        "comment_bool_false",
        command={"abortTransaction": 1, "comment": False},
        msg="abortTransaction should accept comment:false",
    ),
    CommandTestCase(
        "comment_null",
        command={"abortTransaction": 1, "comment": None},
        msg="abortTransaction should accept comment:null",
    ),
    CommandTestCase(
        "comment_object",
        command={"abortTransaction": 1, "comment": {"key": "value"}},
        msg="abortTransaction should accept comment:object",
    ),
    CommandTestCase(
        "comment_object_empty",
        command={"abortTransaction": 1, "comment": {}},
        msg="abortTransaction should accept comment:empty object",
    ),
    CommandTestCase(
        "comment_array",
        command={"abortTransaction": 1, "comment": [1, 2, 3]},
        msg="abortTransaction should accept comment:array",
    ),
    CommandTestCase(
        "comment_array_empty",
        command={"abortTransaction": 1, "comment": []},
        msg="abortTransaction should accept comment:empty array",
    ),
    CommandTestCase(
        "comment_objectid",
        command={"abortTransaction": 1, "comment": ObjectId()},
        msg="abortTransaction should accept comment:ObjectId",
    ),
    CommandTestCase(
        "comment_datetime",
        command={
            "abortTransaction": 1,
            "comment": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        msg="abortTransaction should accept comment:datetime",
    ),
    CommandTestCase(
        "comment_binary",
        command={"abortTransaction": 1, "comment": Binary(b"\x00")},
        msg="abortTransaction should accept comment:Binary",
    ),
    CommandTestCase(
        "comment_regex",
        command={"abortTransaction": 1, "comment": Regex(".*")},
        msg="abortTransaction should accept comment:Regex",
    ),
    CommandTestCase(
        "comment_timestamp",
        command={"abortTransaction": 1, "comment": Timestamp(0, 0)},
        msg="abortTransaction should accept comment:Timestamp",
    ),
    CommandTestCase(
        "comment_minkey",
        command={"abortTransaction": 1, "comment": MinKey()},
        msg="abortTransaction should accept comment:MinKey",
    ),
    CommandTestCase(
        "comment_maxkey",
        command={"abortTransaction": 1, "comment": MaxKey()},
        msg="abortTransaction should accept comment:MaxKey",
    ),
    CommandTestCase(
        "comment_code",
        command={"abortTransaction": 1, "comment": Code("function(){}")},
        msg="abortTransaction should accept comment:Code",
    ),
]


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(COMMENT_TYPE_TESTS))
def test_abortTransaction_comment(collection, test):
    """Test abortTransaction comment parameter type acceptance in a transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = execute_admin_command(collection, test.command, session=session)
    assertSuccessPartial(result, {"ok": 1.0}, msg=test.msg)
