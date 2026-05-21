"""Tests for aggregate command collation locale sub-field rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_TRAILING_ZERO

# Property [Locale Invalid String Values]: invalid locale strings produce
# BAD_VALUE_ERROR.
COLLATION_LOCALE_INVALID_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "locale_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject empty string locale",
    ),
    CommandTestCase(
        "locale_null_byte",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en\x00us"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject locale containing null byte",
    ),
    CommandTestCase(
        "locale_invalid_sa",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "sa"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject unsupported locale sa",
    ),
    CommandTestCase(
        "locale_invalid_tk",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "tk"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject unsupported locale tk",
    ),
    CommandTestCase(
        "locale_region_en_GB",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en_GB"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject unsupported region-code locale en_GB",
    ),
    CommandTestCase(
        "locale_region_fr_FR",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "fr_FR"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject unsupported region-code locale fr_FR",
    ),
    CommandTestCase(
        "locale_invalid_variant_pinyin",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "zh@collation=pinyin"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject invalid locale variant zh@collation=pinyin",
    ),
    CommandTestCase(
        "locale_case_variant_EN",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "EN"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject case variant EN of valid locale en",
    ),
    CommandTestCase(
        "locale_case_variant_Fr",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "Fr"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject case variant Fr of valid locale fr",
    ),
    CommandTestCase(
        "locale_case_variant_Simple",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "Simple"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject case variant Simple of simple locale",
    ),
    CommandTestCase(
        "locale_case_variant_SIMPLE",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "SIMPLE"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject case variant SIMPLE of simple locale",
    ),
    CommandTestCase(
        "locale_hyphen_en_US",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en-US"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject hyphen variant en-US",
    ),
    CommandTestCase(
        "locale_hyphen_fr_CA",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "fr-CA"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject hyphen variant fr-CA",
    ),
    CommandTestCase(
        "locale_long_invalid_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "abcdefghijklm"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject very long invalid locale string",
    ),
    CommandTestCase(
        "locale_dollar_prefixed_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "$field"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should treat dollar-prefixed string as invalid locale",
    ),
    CommandTestCase(
        "locale_dollar_prefixed_root",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "$$ROOT"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should treat double-dollar-prefixed string as invalid locale",
    ),
]

# Property [Locale Non-String Type]: non-string types for locale produce
# TYPE_MISMATCH_ERROR.
COLLATION_LOCALE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "locale_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": 42},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject int32 locale",
    ),
    CommandTestCase(
        "locale_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": Int64(42)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Int64 locale",
    ),
    CommandTestCase(
        "locale_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": 3.14},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject double locale",
    ),
    CommandTestCase(
        "locale_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": DECIMAL128_TRAILING_ZERO},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Decimal128 locale",
    ),
    CommandTestCase(
        "locale_type_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean locale",
    ),
    CommandTestCase(
        "locale_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": ["en"]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array locale",
    ),
    CommandTestCase(
        "locale_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": {"value": "en"}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object locale",
    ),
    CommandTestCase(
        "locale_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId locale",
    ),
    CommandTestCase(
        "locale_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime locale",
    ),
    CommandTestCase(
        "locale_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp locale",
    ),
    CommandTestCase(
        "locale_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary locale",
    ),
    CommandTestCase(
        "locale_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex locale",
    ),
    CommandTestCase(
        "locale_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code locale",
    ),
    CommandTestCase(
        "locale_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope locale",
    ),
    CommandTestCase(
        "locale_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey locale",
    ),
    CommandTestCase(
        "locale_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey locale",
    ),
]

COLLATION_LOCALE_ERROR_TESTS: list[CommandTestCase] = (
    COLLATION_LOCALE_INVALID_VALUE_TESTS + COLLATION_LOCALE_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_LOCALE_ERROR_TESTS))
def test_aggregate_collation_locale_rejection(database_client, collection, test):
    """Test aggregate command collation sub-field rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
