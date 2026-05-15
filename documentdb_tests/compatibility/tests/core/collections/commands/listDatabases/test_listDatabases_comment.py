"""Tests for listDatabases comment parameter."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.listDatabases.utils.listDatabases_common import (  # noqa: E501
    basic_success,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [comment BSON Type Acceptance]: the comment parameter
# accepts every BSON type without affecting the response.
COMMENT_BSON_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "comment": 42},
        expected=basic_success,
        msg="int32 comment should be accepted",
        id="comment_int32",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": INT64_ZERO},
        expected=basic_success,
        msg="Int64 comment should be accepted",
        id="comment_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": 3.14},
        expected=basic_success,
        msg="double comment should be accepted",
        id="comment_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": Decimal128("1")},
        expected=basic_success,
        msg="Decimal128 comment should be accepted",
        id="comment_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "hello"},
        expected=basic_success,
        msg="string comment should be accepted",
        id="comment_string",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": True},
        expected=basic_success,
        msg="bool comment should be accepted",
        id="comment_bool",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": None},
        expected=basic_success,
        msg="null comment should be accepted",
        id="comment_null",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": [1, 2, 3]},
        expected=basic_success,
        msg="array comment should be accepted",
        id="comment_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": {"key": "value"}},
        expected=basic_success,
        msg="object comment should be accepted",
        id="comment_object",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": ObjectId()},
        expected=basic_success,
        msg="ObjectId comment should be accepted",
        id="comment_objectid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": datetime.datetime(2024, 1, 1)},
        expected=basic_success,
        msg="datetime comment should be accepted",
        id="comment_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": Timestamp(1, 1)},
        expected=basic_success,
        msg="Timestamp comment should be accepted",
        id="comment_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": Binary(b"\x01\x02")},
        expected=basic_success,
        msg="Binary comment should be accepted",
        id="comment_binary",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": Regex("^abc")},
        expected=basic_success,
        msg="Regex comment should be accepted",
        id="comment_regex",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": Code("function(){}")},
        expected=basic_success,
        msg="Code comment should be accepted",
        id="comment_code",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "comment": Code("function(){}", {"x": 1}),
        },
        expected=basic_success,
        msg="CodeWithScope comment should be accepted",
        id="comment_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": MinKey()},
        expected=basic_success,
        msg="MinKey comment should be accepted",
        id="comment_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": MaxKey()},
        expected=basic_success,
        msg="MaxKey comment should be accepted",
        id="comment_maxkey",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMMENT_BSON_TYPE_ACCEPTANCE_TESTS))
def test_listDatabases_comment(collection, test):
    """Test listDatabases comment parameter acceptance."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
