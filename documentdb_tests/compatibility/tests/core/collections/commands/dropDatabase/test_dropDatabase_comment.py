from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Comment Type Acceptance]: the comment parameter accepts every
# BSON type representable by pymongo.
COMMENT_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "comment": "hello"},
        expected={"ok": 1.0},
        msg="String comment should be accepted",
        id="comment_string",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": 42},
        expected={"ok": 1.0},
        msg="int32 comment should be accepted",
        id="comment_int32",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": Int64(42)},
        expected={"ok": 1.0},
        msg="Int64 comment should be accepted",
        id="comment_int64",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": 3.14},
        expected={"ok": 1.0},
        msg="double comment should be accepted",
        id="comment_double",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": Decimal128("3.14")},
        expected={"ok": 1.0},
        msg="Decimal128 comment should be accepted",
        id="comment_decimal128",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": True},
        expected={"ok": 1.0},
        msg="bool comment should be accepted",
        id="comment_bool",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": [1, 2, 3]},
        expected={"ok": 1.0},
        msg="array comment should be accepted",
        id="comment_array",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": {"key": "value"}},
        expected={"ok": 1.0},
        msg="object comment should be accepted",
        id="comment_object",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": ObjectId()},
        expected={"ok": 1.0},
        msg="ObjectId comment should be accepted",
        id="comment_objectid",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": datetime.datetime(2024, 1, 1)},
        expected={"ok": 1.0},
        msg="datetime comment should be accepted",
        id="comment_datetime",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": Timestamp(1, 1)},
        expected={"ok": 1.0},
        msg="Timestamp comment should be accepted",
        id="comment_timestamp",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": Binary(b"hello")},
        expected={"ok": 1.0},
        msg="Binary comment should be accepted",
        id="comment_binary",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": Regex("pattern", "i")},
        expected={"ok": 1.0},
        msg="Regex comment should be accepted",
        id="comment_regex",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": Code("function() {}")},
        expected={"ok": 1.0},
        msg="Code comment should be accepted",
        id="comment_code",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": Code("function() {}", {"x": 1})},
        expected={"ok": 1.0},
        msg="CodeWithScope comment should be accepted",
        id="comment_code_with_scope",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": MinKey()},
        expected={"ok": 1.0},
        msg="MinKey comment should be accepted",
        id="comment_minkey",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "comment": MaxKey()},
        expected={"ok": 1.0},
        msg="MaxKey comment should be accepted",
        id="comment_maxkey",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMMENT_TYPE_ACCEPTANCE_TESTS))
def test_dropDatabase_comment(database_client, collection, register_db_cleanup, test):
    """Test dropDatabase command inputs and error handling."""
    coll = test.prepare(database_client, collection)
    result = execute_command(coll, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
