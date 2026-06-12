"""Tests for listDatabases command field value acceptance."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.listDatabases.utils.listDatabases_common import (  # noqa: E501
    basic_success,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    API_VERSION_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Null and Missing Behavior]: null literal and omitted
# parameters are accepted and produce a successful response.
NULL_MISSING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": None},
        expected=basic_success,
        msg="Null command field value should be accepted",
        id="command_value_null",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": None},
        expected=basic_success,
        msg="Null filter should be accepted",
        id="filter_null",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": None},
        expected=basic_success,
        msg="Null nameOnly should be accepted",
        id="name_only_null",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "authorizedDatabases": None},
        expected=basic_success,
        msg="Null authorizedDatabases should be accepted",
        id="authorized_databases_null",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": None},
        expected=basic_success,
        msg="Null comment should be accepted",
        id="comment_null",
    ),
    CommandTestCase(
        command={"listDatabases": 1},
        expected=basic_success,
        msg="Omitting all optional parameters should be accepted",
        id="all_omitted",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": None,
            "nameOnly": None,
            "authorizedDatabases": None,
            "comment": None,
        },
        expected=basic_success,
        msg="All parameters set to null should be accepted",
        id="param_all_null",
    ),
]

# Property [Command Field Value Acceptance]: the listDatabases command
# field accepts any BSON type as its value and the value is completely
# ignored.
COMMAND_FIELD_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 0},
        expected=basic_success,
        msg="int32 zero should be accepted as command field value",
        id="cmd_val_int32_zero",
    ),
    CommandTestCase(
        command={"listDatabases": -1},
        expected=basic_success,
        msg="int32 negative should be accepted as command field value",
        id="cmd_val_int32_neg",
    ),
    CommandTestCase(
        command={"listDatabases": INT32_MAX},
        expected=basic_success,
        msg="max 32-bit integer should be accepted as command field value",
        id="cmd_val_int32_max",
    ),
    CommandTestCase(
        command={"listDatabases": INT32_MIN},
        expected=basic_success,
        msg="min 32-bit integer should be accepted as command field value",
        id="cmd_val_int32_min",
    ),
    CommandTestCase(
        command={"listDatabases": INT64_MAX},
        expected=basic_success,
        msg="max 64-bit integer should be accepted as command field value",
        id="cmd_val_int64_max",
    ),
    CommandTestCase(
        command={"listDatabases": INT64_MIN},
        expected=basic_success,
        msg="min 64-bit integer should be accepted as command field value",
        id="cmd_val_int64_min",
    ),
    CommandTestCase(
        command={"listDatabases": FLOAT_NAN},
        expected=basic_success,
        msg="double NaN should be accepted as command field value",
        id="cmd_val_double_nan",
    ),
    CommandTestCase(
        command={"listDatabases": FLOAT_INFINITY},
        expected=basic_success,
        msg="double Infinity should be accepted as command field value",
        id="cmd_val_double_inf",
    ),
    CommandTestCase(
        command={"listDatabases": FLOAT_NEGATIVE_INFINITY},
        expected=basic_success,
        msg="double -Infinity should be accepted as command field value",
        id="cmd_val_double_neg_inf",
    ),
    CommandTestCase(
        command={"listDatabases": DOUBLE_NEGATIVE_ZERO},
        expected=basic_success,
        msg="double -0.0 should be accepted as command field value",
        id="cmd_val_double_neg_zero",
    ),
    CommandTestCase(
        command={"listDatabases": DOUBLE_MAX},
        expected=basic_success,
        msg="max double should be accepted as command field value",
        id="cmd_val_double_max",
    ),
    CommandTestCase(
        command={"listDatabases": DOUBLE_MIN_SUBNORMAL},
        expected=basic_success,
        msg="min subnormal double should be accepted as command field value",
        id="cmd_val_double_min_subnormal",
    ),
    CommandTestCase(
        command={"listDatabases": DECIMAL128_NAN},
        expected=basic_success,
        msg="Decimal128 NaN should be accepted as command field value",
        id="cmd_val_decimal128_nan",
    ),
    CommandTestCase(
        command={"listDatabases": DECIMAL128_INFINITY},
        expected=basic_success,
        msg="Decimal128 Infinity should be accepted as command field value",
        id="cmd_val_decimal128_inf",
    ),
    CommandTestCase(
        command={"listDatabases": DECIMAL128_NEGATIVE_INFINITY},
        expected=basic_success,
        msg="Decimal128 -Infinity should be accepted as command field value",
        id="cmd_val_decimal128_neg_inf",
    ),
    CommandTestCase(
        command={"listDatabases": DECIMAL128_NEGATIVE_ZERO},
        expected=basic_success,
        msg="Decimal128 -0 should be accepted as command field value",
        id="cmd_val_decimal128_neg_zero",
    ),
    CommandTestCase(
        command={"listDatabases": DECIMAL128_MAX},
        expected=basic_success,
        msg="Decimal128 max value should be accepted as command field value",
        id="cmd_val_decimal128_max",
    ),
    CommandTestCase(
        command={"listDatabases": Decimal128("1234567890123456789012345678901234")},
        expected=basic_success,
        msg="Decimal128 max precision should be accepted as command field value",
        id="cmd_val_decimal128_max_precision",
    ),
    CommandTestCase(
        command={"listDatabases": True},
        expected=basic_success,
        msg="bool true should be accepted as command field value",
        id="cmd_val_bool_true",
    ),
    CommandTestCase(
        command={"listDatabases": False},
        expected=basic_success,
        msg="bool false should be accepted as command field value",
        id="cmd_val_bool_false",
    ),
    CommandTestCase(
        command={"listDatabases": ""},
        expected=basic_success,
        msg="empty string should be accepted as command field value",
        id="cmd_val_string_empty",
    ),
    CommandTestCase(
        command={"listDatabases": "\u00e9\u00e0\u00fc"},
        expected=basic_success,
        msg="unicode string should be accepted as command field value",
        id="cmd_val_string_unicode",
    ),
    CommandTestCase(
        command={"listDatabases": "x" * 10_000},
        expected=basic_success,
        msg="10K character string should be accepted as command field value",
        id="cmd_val_string_10k",
    ),
    CommandTestCase(
        command={"listDatabases": []},
        expected=basic_success,
        msg="empty array should be accepted as command field value",
        id="cmd_val_array_empty",
    ),
    CommandTestCase(
        command={"listDatabases": [[1, [2, [3]]]]},
        expected=basic_success,
        msg="nested array should be accepted as command field value",
        id="cmd_val_array_nested",
    ),
    CommandTestCase(
        command={"listDatabases": {}},
        expected=basic_success,
        msg="empty object should be accepted as command field value",
        id="cmd_val_object_empty",
    ),
    CommandTestCase(
        command={"listDatabases": {"$x": 1}},
        expected=basic_success,
        msg="object with dollar-prefixed key should be accepted",
        id="cmd_val_object_dollar_key",
    ),
    CommandTestCase(
        command={"listDatabases": {"a": {"b": {"c": 1}}}},
        expected=basic_success,
        msg="nested object should be accepted as command field value",
        id="cmd_val_object_nested",
    ),
    CommandTestCase(
        command={"listDatabases": ObjectId()},
        expected=basic_success,
        msg="ObjectId should be accepted as command field value",
        id="cmd_val_objectid",
    ),
    CommandTestCase(
        command={"listDatabases": datetime.datetime(2024, 1, 1)},
        expected=basic_success,
        msg="datetime should be accepted as command field value",
        id="cmd_val_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": Timestamp(0, 0)},
        expected=basic_success,
        msg="Timestamp should be accepted as command field value",
        id="cmd_val_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": Binary(b"\x01\x02")},
        expected=basic_success,
        msg="Binary should be accepted as command field value",
        id="cmd_val_binary",
    ),
    CommandTestCase(
        command={"listDatabases": Regex("^abc")},
        expected=basic_success,
        msg="Regex should be accepted as command field value",
        id="cmd_val_regex",
    ),
    CommandTestCase(
        command={"listDatabases": Code("function(){}")},
        expected=basic_success,
        msg="Code should be accepted as command field value",
        id="cmd_val_code",
    ),
    CommandTestCase(
        command={"listDatabases": Code("function(){}", {"x": 1})},
        expected=basic_success,
        msg="CodeWithScope should be accepted as command field value",
        id="cmd_val_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": MinKey()},
        expected=basic_success,
        msg="MinKey should be accepted as command field value",
        id="cmd_val_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": MaxKey()},
        expected=basic_success,
        msg="MaxKey should be accepted as command field value",
        id="cmd_val_maxkey",
    ),
]

# Property [Unrecognized Field Errors]: unrecognized fields in the
# command document produce an IDLUnknownField error.
UNRECOGNIZED_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "unknownField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should produce IDLUnknownField error",
        id="unrecognized_field_simple",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "$badField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Dollar-prefixed unknown field should produce IDLUnknownField error",
        id="unrecognized_field_dollar_prefix",
    ),
]

# Property [API Version Acceptance]: API version 1 with apiStrict and
# apiDeprecationErrors is accepted.
API_VERSION_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={
            "listDatabases": 1,
            "apiVersion": "1",
            "apiStrict": True,
            "apiDeprecationErrors": True,
        },
        expected=basic_success,
        msg="API version 1 with apiStrict and apiDeprecationErrors should be accepted",
        id="api_version_1_strict",
    ),
]

# Property [API Version Errors]: API version "2" produces an
# APIVersionError because only version "1" is accepted.
API_VERSION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "apiVersion": "2"},
        error_code=API_VERSION_ERROR,
        msg="API version 2 should produce APIVersionError",
        id="api_version_2",
    ),
]

# Property [All Parameters Simultaneously]: all parameters (filter,
# nameOnly, authorizedDatabases, comment) can be set at the same time
# without conflict.
PARAM_INTERACTION_ALL_PARAMS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": "admin"},
            "nameOnly": True,
            "authorizedDatabases": True,
            "comment": "test",
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="All parameters set simultaneously should not conflict",
        id="param_all_params_simultaneously",
    ),
]

COMMAND_ACCEPTANCE_TESTS: list[CommandTestCase] = (
    NULL_MISSING_TESTS
    + COMMAND_FIELD_VALUE_TESTS
    + UNRECOGNIZED_FIELD_ERROR_TESTS
    + API_VERSION_ACCEPTED_TESTS
    + API_VERSION_ERROR_TESTS
    + PARAM_INTERACTION_ALL_PARAMS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMMAND_ACCEPTANCE_TESTS))
def test_listDatabases_command_acceptance(collection, test):
    """Test listDatabases command field value acceptance."""
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
