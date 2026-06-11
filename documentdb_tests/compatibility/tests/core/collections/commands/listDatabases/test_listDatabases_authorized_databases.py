"""Tests for listDatabases authorizedDatabases parameter."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.listDatabases.utils.listDatabases_common import (  # noqa: E501
    basic_success,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO, INT64_ZERO

# Property [authorizedDatabases Success Behavior]: authorizedDatabases
# accepts true and false without changing the result set for a fully
# privileged user.
AUTH_DBS_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": True},
        expected=basic_success,
        msg="authorizedDatabases=true should succeed and include test database",
        id="auth_dbs_true",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": False},
        expected=basic_success,
        msg="authorizedDatabases=false should succeed and include test database",
        id="auth_dbs_false",
    ),
]

# Property [authorizedDatabases Type Strictness]: authorizedDatabases
# rejects all non-bool, non-null types with a TypeMismatch error,
# including numeric types that nameOnly would accept.
AUTH_DBS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with int32 should produce TypeMismatch",
        id="auth_dbs_type_int32",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": INT64_ZERO},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with Int64 should produce TypeMismatch",
        id="auth_dbs_type_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with double should produce TypeMismatch",
        id="auth_dbs_type_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": DECIMAL128_ZERO},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with Decimal128 should produce TypeMismatch",
        id="auth_dbs_type_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": "true"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with string should produce TypeMismatch",
        id="auth_dbs_type_string",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with array should produce TypeMismatch",
        id="auth_dbs_type_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with object should produce TypeMismatch",
        id="auth_dbs_type_object",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with ObjectId should produce TypeMismatch",
        id="auth_dbs_type_objectid",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "authorizedDatabases": datetime.datetime(2024, 1, 1),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with datetime should produce TypeMismatch",
        id="auth_dbs_type_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with Timestamp should produce TypeMismatch",
        id="auth_dbs_type_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with Binary should produce TypeMismatch",
        id="auth_dbs_type_binary",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": Regex("^x")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with Regex should produce TypeMismatch",
        id="auth_dbs_type_regex",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "authorizedDatabases": Code("function(){}"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with Code should produce TypeMismatch",
        id="auth_dbs_type_code",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "authorizedDatabases": Code("function(){}", {"x": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with CodeWithScope should produce TypeMismatch",
        id="auth_dbs_type_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with MinKey should produce TypeMismatch",
        id="auth_dbs_type_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="authorizedDatabases with MaxKey should produce TypeMismatch",
        id="auth_dbs_type_maxkey",
    ),
]

AUTH_DBS_TESTS: list[CommandTestCase] = AUTH_DBS_SUCCESS_TESTS + AUTH_DBS_TYPE_ERROR_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(AUTH_DBS_TESTS))
def test_listDatabases_authorized_databases(collection, test):
    """Test listDatabases authorizedDatabases parameter behavior."""
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
