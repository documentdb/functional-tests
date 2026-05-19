"""Tests for aggregate command aggregate field type acceptance and rejection."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [Numeric-1 Acceptance]: numeric values equal to 1 activate
# collection-agnostic mode across all numeric types.
AGGREGATE_FIELD_NUMERIC_ONE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int32_one",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept int32 1 for collection-agnostic mode",
    ),
    CommandTestCase(
        "int64_one",
        command={
            "aggregate": Int64(1),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Int64 1 for collection-agnostic mode",
    ),
    CommandTestCase(
        "double_one",
        command={
            "aggregate": 1.0,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double 1.0 for collection-agnostic mode",
    ),
    CommandTestCase(
        "decimal128_one",
        command={
            "aggregate": Decimal128("1"),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128('1') for collection-agnostic mode",
    ),
    CommandTestCase(
        "decimal128_precision_loss",
        command={
            "aggregate": Decimal128("0.99999999999999999"),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 that rounds to 1.0 in double precision",
    ),
]

# Property [String Name Character Acceptance]: string collection names with
# special characters, unicode, and long lengths are accepted.
AGGREGATE_FIELD_STRING_CHARS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string_name",
        docs=[{"_id": 1}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept a string collection name",
    ),
    CommandTestCase(
        "string_dollar_prefix",
        command={"aggregate": "$hello", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept dollar-prefixed collection name",
    ),
    CommandTestCase(
        "string_dollar_cmd",
        command={"aggregate": "$cmd", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept $cmd as collection name",
    ),
    CommandTestCase(
        "string_dollar_cmd_dot_x",
        command={"aggregate": "$cmd.x", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept $cmd.x as collection name",
    ),
    CommandTestCase(
        "string_control_char",
        command={"aggregate": "test\x01coll", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept collection name with control character U+0001",
    ),
    CommandTestCase(
        "string_whitespace",
        command={"aggregate": "test coll", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept collection name with whitespace",
    ),
    CommandTestCase(
        "string_unicode",
        command={"aggregate": "test\u00e9", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept collection name with unicode characters",
    ),
    CommandTestCase(
        "string_emoji",
        command={"aggregate": "test\U0001f600", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept collection name with emoji",
    ),
    CommandTestCase(
        "string_cjk",
        command={"aggregate": "test\u4e2d\u6587", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept collection name with CJK characters",
    ),
    CommandTestCase(
        "string_long_name",
        command={"aggregate": "a" * 100_000, "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept collection name longer than 100K characters",
    ),
]

# Property [System Collection Acceptance]: system.* collection names are
# accepted as valid aggregate targets.
AGGREGATE_FIELD_SYSTEM_COLLECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string_system_users",
        command={"aggregate": "system.users", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept system.users as collection name",
    ),
    CommandTestCase(
        "string_system_profile",
        command={"aggregate": "system.profile", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept system.profile as collection name",
    ),
    CommandTestCase(
        "string_system_views",
        command={"aggregate": "system.views", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept system.views as collection name",
    ),
    CommandTestCase(
        "string_system_buckets",
        command={"aggregate": "system.buckets.test", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept system.buckets.* as collection name",
    ),
    CommandTestCase(
        "string_system_js",
        command={"aggregate": "system.js", "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept system.js as collection name",
    ),
]

AGGREGATE_FIELD_ACCEPTANCE_TESTS = (
    AGGREGATE_FIELD_NUMERIC_ONE_TESTS
    + AGGREGATE_FIELD_STRING_CHARS_TESTS
    + AGGREGATE_FIELD_SYSTEM_COLLECTION_TESTS
)

# Property [Field Type Rejection]: non-string, non-numeric BSON types for the
# aggregate field are rejected.
AGGREGATE_FIELD_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "reject_null",
        command={"aggregate": None, "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject null as an invalid type",
    ),
    CommandTestCase(
        "reject_bool_true",
        command={"aggregate": True, "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject boolean True as a type error",
    ),
    CommandTestCase(
        "reject_array",
        command={"aggregate": [1, 2], "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject array type",
    ),
    CommandTestCase(
        "reject_document",
        command={"aggregate": {"a": 1}, "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject document type",
    ),
    CommandTestCase(
        "reject_objectid",
        command={"aggregate": ObjectId(), "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject ObjectId type",
    ),
    CommandTestCase(
        "reject_datetime",
        command={
            "aggregate": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "pipeline": [],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject datetime type",
    ),
    CommandTestCase(
        "reject_timestamp",
        command={"aggregate": Timestamp(1, 1), "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject Timestamp type",
    ),
    CommandTestCase(
        "reject_regex",
        command={"aggregate": Regex(".*"), "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject Regex type",
    ),
    CommandTestCase(
        "reject_code",
        command={"aggregate": Code("function(){}"), "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject Code type",
    ),
    CommandTestCase(
        "reject_code_with_scope",
        command={
            "aggregate": Code("function(){}", {"x": 1}),
            "pipeline": [],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject Code with scope type",
    ),
    CommandTestCase(
        "reject_minkey",
        command={"aggregate": MinKey(), "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject MinKey type",
    ),
    CommandTestCase(
        "reject_maxkey",
        command={"aggregate": MaxKey(), "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject MaxKey type",
    ),
    CommandTestCase(
        "reject_binary",
        command={"aggregate": Binary(b"hello"), "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject Binary type",
    ),
    CommandTestCase(
        "reject_binary_uuid",
        command={
            "aggregate": Binary.from_uuid(uuid.uuid4()),
            "pipeline": [],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject Binary UUID with a distinct message",
    ),
    CommandTestCase(
        "reject_binary_uuid_short",
        command={
            "aggregate": Binary(b"short", subtype=4),
            "pipeline": [],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject non-standard-size Binary subtype 4 with UUID error",
    ),
]

# Property [Numeric Value Rejection]: numeric values other than 1 (including
# zero, negative, fractional, NaN, and infinity) are rejected.
AGGREGATE_FIELD_NUMERIC_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "reject_int_0",
        command={
            "aggregate": 0,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject numeric 0",
    ),
    CommandTestCase(
        "reject_int_2",
        command={
            "aggregate": 2,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject numeric value 2",
    ),
    CommandTestCase(
        "reject_int_neg1",
        command={
            "aggregate": -1,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative numeric value",
    ),
    CommandTestCase(
        "reject_int64_2",
        command={
            "aggregate": Int64(2),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Int64 value other than 1",
    ),
    CommandTestCase(
        "reject_double_2_5",
        command={
            "aggregate": 2.5,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject double value other than 1.0",
    ),
    CommandTestCase(
        "reject_decimal128_not_one",
        command={
            "aggregate": Decimal128("0.9999999999999999"),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128 that does not round to 1.0",
    ),
    *[
        CommandTestCase(
            f"reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": v,
                "pipeline": [{"$documents": [{"a": 1}]}],
                "cursor": {},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"aggregate should reject {tid} numeric value",
        )
        for tid, val in [
            ("double_zero", DOUBLE_ZERO),
            ("double_neg_zero", DOUBLE_NEGATIVE_ZERO),
            ("double_nan", FLOAT_NAN),
            ("double_infinity", FLOAT_INFINITY),
            ("double_neg_infinity", FLOAT_NEGATIVE_INFINITY),
            ("int64_zero", INT64_ZERO),
            ("decimal128_zero", DECIMAL128_ZERO),
            ("decimal128_neg_zero", DECIMAL128_NEGATIVE_ZERO),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
]

# Property [String Format Rejection]: string values with invalid formats
# (empty, dot-prefixed, embedded null byte, $cmd.aggregate) are rejected.
AGGREGATE_FIELD_STRING_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "reject_empty_string",
        command={"aggregate": "", "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject empty string collection name",
    ),
    CommandTestCase(
        "reject_dot_prefix",
        command={"aggregate": ".hello", "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject dot-prefixed collection name",
    ),
    CommandTestCase(
        "reject_embedded_null_byte",
        command={"aggregate": "test\x00coll", "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject collection name with embedded null byte",
    ),
    CommandTestCase(
        "reject_cmd_aggregate",
        command={"aggregate": "$cmd.aggregate", "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject the specific string $cmd.aggregate",
    ),
]

AGGREGATE_FIELD_REJECTION_TESTS = (
    AGGREGATE_FIELD_TYPE_REJECTION_TESTS
    + AGGREGATE_FIELD_NUMERIC_REJECTION_TESTS
    + AGGREGATE_FIELD_STRING_REJECTION_TESTS
)

AGGREGATE_FIELD_TESTS = AGGREGATE_FIELD_ACCEPTANCE_TESTS + AGGREGATE_FIELD_REJECTION_TESTS


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_FIELD_TESTS))
def test_aggregate_field(database_client, collection, test):
    """Test aggregate field acceptance and rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
