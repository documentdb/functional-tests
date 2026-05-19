"""Tests for aggregate command comment value acceptance."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Comment Numeric Edge Values]: the comment field accepts numeric
# boundary values including min/max, NaN, infinity, and negative zero.
AGGREGATE_COMMENT_NUMERIC_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": INT32_MAX,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept INT32_MAX as comment",
    ),
    CommandTestCase(
        "comment_int32_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": INT32_MIN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept INT32_MIN as comment",
    ),
    CommandTestCase(
        "comment_int64_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": INT64_MAX,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept INT64_MAX as comment",
    ),
    CommandTestCase(
        "comment_int64_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": INT64_MIN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept INT64_MIN as comment",
    ),
    CommandTestCase(
        "comment_double_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DOUBLE_MAX,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept DOUBLE_MAX as comment",
    ),
    CommandTestCase(
        "comment_double_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DOUBLE_MIN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept DOUBLE_MIN as comment",
    ),
    CommandTestCase(
        "comment_decimal128_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DECIMAL128_MAX,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept DECIMAL128_MAX as comment",
    ),
    CommandTestCase(
        "comment_decimal128_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DECIMAL128_MIN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept DECIMAL128_MIN as comment",
    ),
    CommandTestCase(
        "comment_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": FLOAT_NAN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept NaN as comment",
    ),
    CommandTestCase(
        "comment_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": FLOAT_NEGATIVE_NAN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept negative NaN as comment",
    ),
    CommandTestCase(
        "comment_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DECIMAL128_NAN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 NaN as comment",
    ),
    CommandTestCase(
        "comment_decimal128_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DECIMAL128_NEGATIVE_NAN,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 negative NaN as comment",
    ),
    CommandTestCase(
        "comment_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": FLOAT_INFINITY,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Infinity as comment",
    ),
    CommandTestCase(
        "comment_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": FLOAT_NEGATIVE_INFINITY,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept -Infinity as comment",
    ),
    CommandTestCase(
        "comment_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DECIMAL128_INFINITY,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 Infinity as comment",
    ),
    CommandTestCase(
        "comment_decimal128_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DECIMAL128_NEGATIVE_INFINITY,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 -Infinity as comment",
    ),
    CommandTestCase(
        "comment_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept -0.0 as comment",
    ),
]

# Property [Comment Large Values]: the comment field accepts large strings,
# objects, and arrays without size-related errors.
AGGREGATE_COMMENT_LARGE_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_large_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "x" * 100_000,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept 100KB string comment",
    ),
    CommandTestCase(
        "comment_large_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": {f"k{i}": i for i in range(1000)},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept 1000-key object comment",
    ),
    CommandTestCase(
        "comment_large_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": list(range(10_000)),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept 10000-element array comment",
    ),
]

# Property [Comment Special Strings]: the comment field accepts strings with
# special characters without interpretation or rejection.
AGGREGATE_COMMENT_SPECIAL_STRING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_string_null_byte",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "hello\x00world",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept string comment with embedded null byte",
    ),
    CommandTestCase(
        "comment_string_dollar_prefix",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "$field",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept dollar-prefixed string comment without interpretation",
    ),
    CommandTestCase(
        "comment_string_double_dollar",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "$$NOW",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double-dollar string comment without interpretation",
    ),
    CommandTestCase(
        "comment_string_unicode",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "\u00e9\u4e2d\u6587",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept unicode string comment",
    ),
    CommandTestCase(
        "comment_string_emoji",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "\U0001f600\U0001f4a5",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept emoji string comment",
    ),
    CommandTestCase(
        # U+FEFF BOM, U+200B ZWSP, U+200D ZWJ.
        "comment_string_bom_zwsp_zwj",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "\ufeff\u200b\u200d",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept string comment with BOM, ZWSP, and ZWJ",
    ),
]

# Property [Comment Parameter Combinations]: the comment field works alongside
# other command options without interference.
AGGREGATE_COMMENT_COMBINATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_with_allowdiskuse",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "with allowDiskUse",
            "allowDiskUse": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept comment combined with allowDiskUse",
    ),
    CommandTestCase(
        "comment_with_maxtimems",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "with maxTimeMS",
            "maxTimeMS": 5000,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept comment combined with maxTimeMS",
    ),
    CommandTestCase(
        "comment_with_collation",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "comment": "with collation",
            "collation": {"locale": "en"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept comment combined with collation",
    ),
    CommandTestCase(
        "comment_with_explain",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "comment": "with explain",
            "explain": True,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept comment combined with explain",
    ),
    CommandTestCase(
        "comment_with_agnostic_mode",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
            "comment": "agnostic",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept comment in collection-agnostic mode",
    ),
]

AGGREGATE_COMMENT_VALUE_TESTS = (
    AGGREGATE_COMMENT_NUMERIC_EDGE_TESTS
    + AGGREGATE_COMMENT_LARGE_VALUE_TESTS
    + AGGREGATE_COMMENT_SPECIAL_STRING_TESTS
    + AGGREGATE_COMMENT_COMBINATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_COMMENT_VALUE_TESTS))
def test_aggregate_comment_values(database_client, collection, test):
    """Test aggregate comment value acceptance."""
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
