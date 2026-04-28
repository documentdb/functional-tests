"""Tests for listDatabases comment parameter."""

from __future__ import annotations

import datetime
import functools
from typing import Any

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

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

# Property [comment BSON Type Acceptance]: the comment parameter
# accepts every BSON type without affecting the response.
COMMENT_BSON_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "comment": 0},
        expected=basic_success,
        msg="int32 zero comment should be accepted",
        id="comment_int32_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": INT32_MAX},
        expected=basic_success,
        msg="max 32-bit integer comment should be accepted",
        id="comment_int32_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": INT32_MIN},
        expected=basic_success,
        msg="min 32-bit integer comment should be accepted",
        id="comment_int32_min",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": INT64_MAX},
        expected=basic_success,
        msg="max 64-bit integer comment should be accepted",
        id="comment_int64_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": INT64_MIN},
        expected=basic_success,
        msg="min 64-bit integer comment should be accepted",
        id="comment_int64_min",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": FLOAT_NAN},
        expected=basic_success,
        msg="double NaN comment should be accepted",
        id="comment_double_nan",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": FLOAT_INFINITY},
        expected=basic_success,
        msg="double Infinity comment should be accepted",
        id="comment_double_inf",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": FLOAT_NEGATIVE_INFINITY},
        expected=basic_success,
        msg="double -Infinity comment should be accepted",
        id="comment_double_neg_inf",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DOUBLE_NEGATIVE_ZERO},
        expected=basic_success,
        msg="double -0.0 comment should be accepted",
        id="comment_double_neg_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DOUBLE_MAX},
        expected=basic_success,
        msg="max double comment should be accepted",
        id="comment_double_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DOUBLE_MIN_SUBNORMAL},
        expected=basic_success,
        msg="min subnormal double comment should be accepted",
        id="comment_double_min_subnormal",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DECIMAL128_NAN},
        expected=basic_success,
        msg="Decimal128 NaN comment should be accepted",
        id="comment_decimal128_nan",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DECIMAL128_INFINITY},
        expected=basic_success,
        msg="Decimal128 Infinity comment should be accepted",
        id="comment_decimal128_inf",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DECIMAL128_NEGATIVE_INFINITY},
        expected=basic_success,
        msg="Decimal128 -Infinity comment should be accepted",
        id="comment_decimal128_neg_inf",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DECIMAL128_NEGATIVE_ZERO},
        expected=basic_success,
        msg="Decimal128 -0 comment should be accepted",
        id="comment_decimal128_neg_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": DECIMAL128_MAX},
        expected=basic_success,
        msg="Decimal128 max comment should be accepted",
        id="comment_decimal128_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": ""},
        expected=basic_success,
        msg="empty string comment should be accepted",
        id="comment_string_empty",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "hello\x00world"},
        expected=basic_success,
        msg="null-byte string comment should be accepted",
        id="comment_string_null_byte",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "$expr"},
        expected=basic_success,
        msg="dollar-prefixed string comment should be accepted",
        id="comment_string_dollar_prefixed",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "x" * 15 * 1_024 * 1_024},
        expected=basic_success,
        msg="15MB string comment should be accepted",
        id="comment_string_15mb",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "\u4e16\u754c"},
        expected=basic_success,
        msg="CJK string comment should be accepted",
        id="comment_string_cjk",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "\U0001f600"},
        expected=basic_success,
        msg="emoji string comment should be accepted",
        id="comment_string_emoji",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "comment": "\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466",
        },
        expected=basic_success,
        msg="ZWJ sequence string comment should be accepted",
        id="comment_string_zwj",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "\ufeff"},
        expected=basic_success,
        msg="BOM string comment should be accepted",
        id="comment_string_bom",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": "\x01\x02\x03"},
        expected=basic_success,
        msg="control chars string comment should be accepted",
        id="comment_string_control_chars",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": []},
        expected=basic_success,
        msg="empty array comment should be accepted",
        id="comment_array_empty",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": list(range(10_000))},
        expected=basic_success,
        msg="large array comment should be accepted",
        id="comment_array_large",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "comment": functools.reduce(
                lambda inner, _: {"level": inner}, range(99), dict[str, Any]({"level": "leaf"})
            ),
        },
        expected=basic_success,
        msg="deeply nested (100 levels) object comment should be accepted",
        id="comment_object_nested_100",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": {}},
        expected=basic_success,
        msg="empty object comment should be accepted",
        id="comment_object_empty",
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
        command={"listDatabases": 1, "comment": Timestamp(0, 0)},
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
    CommandTestCase(
        command={"listDatabases": 1, "comment": True},
        expected=basic_success,
        msg="bool true comment should be accepted",
        id="comment_bool_true",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "comment": False},
        expected=basic_success,
        msg="bool false comment should be accepted",
        id="comment_bool_false",
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
