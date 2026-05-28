"""Tests for distinct command deduplication behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, Regex
from bson.timestamp import Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Array Unwinding]: when the key field value is an array, each element
# is treated as a separate value for deduplication.
DISTINCT_ARRAY_UNWINDING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "array_top_level_elements",
        docs=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": [2, 4]}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [1, 2, 3, 4], "ok": 1.0},
        msg="distinct should treat each array element as a separate value",
    ),
    CommandTestCase(
        "array_nested_preserved",
        docs=[{"_id": 1, "x": [1, [1], 1]}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [1, [1]], "ok": 1.0},
        msg="distinct should preserve nested arrays as distinct values",
    ),
    CommandTestCase(
        "array_empty_contributes_nothing",
        docs=[{"_id": 1, "x": []}, {"_id": 2, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should extract zero elements from an empty array",
    ),
    CommandTestCase(
        "array_single_level_only",
        docs=[{"_id": 1, "x": [[["a"]]]}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [[["a"]]], "ok": 1.0},
        msg="distinct should only unwrap one level of array nesting",
    ),
    CommandTestCase(
        "array_mixed_with_scalar",
        docs=[{"_id": 1, "x": [1, 2]}, {"_id": 2, "x": 3}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [1, 2, 3], "ok": 1.0},
        msg="distinct should combine array elements and scalar values",
    ),
    CommandTestCase(
        "array_null_elements_unwound",
        docs=[{"_id": 1, "x": [1, None, 2]}, {"_id": 2, "x": [None, 3]}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [None, 1, 2, 3], "ok": 1.0},
        msg="distinct should unwrap null elements from arrays and deduplicate them",
    ),
    CommandTestCase(
        "array_null_element_dedup_with_explicit_null",
        docs=[
            {"_id": 1, "x": [1, None]},
            {"_id": 2, "x": None},
            {"_id": 3, "x": [2]},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [None, 1, 2], "ok": 1.0},
        msg="distinct should deduplicate null from array with explicit null field value",
    ),
]

# Property [Value Deduplication]: numeric values with the same mathematical value
# are deduplicated across types, and the first-encountered representation is
# returned.
DISTINCT_VALUE_DEDUP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dedup_numeric_across_types",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": Int64(1)},
            {"_id": 3, "x": 1.0},
            {"_id": 4, "x": Decimal128("1")},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [1], "ok": 1.0},
        msg="distinct should deduplicate numerically equal values across types",
    ),
    CommandTestCase(
        "dedup_all_zeros",
        docs=[
            {"_id": 1, "x": 0},
            {"_id": 2, "x": DOUBLE_NEGATIVE_ZERO},
            {"_id": 3, "x": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 4, "x": DECIMAL128_ZERO},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [0], "ok": 1.0},
        msg="distinct should deduplicate all zero representations to a single value",
    ),
    CommandTestCase(
        "dedup_nan_across_types",
        docs=[
            {"_id": 1, "x": FLOAT_NAN},
            {"_id": 2, "x": Decimal128("NaN")},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [pytest.approx(FLOAT_NAN, nan_ok=True)],
            "ok": 1.0,
        },
        msg="distinct should deduplicate NaN across float and Decimal128",
    ),
    CommandTestCase(
        "dedup_pos_infinity_across_types",
        docs=[
            {"_id": 1, "x": FLOAT_INFINITY},
            {"_id": 2, "x": DECIMAL128_INFINITY},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [FLOAT_INFINITY], "ok": 1.0},
        msg="distinct should deduplicate +Infinity across float and Decimal128",
    ),
    CommandTestCase(
        "dedup_neg_infinity_across_types",
        docs=[
            {"_id": 1, "x": FLOAT_NEGATIVE_INFINITY},
            {"_id": 2, "x": DECIMAL128_NEGATIVE_INFINITY},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [FLOAT_NEGATIVE_INFINITY], "ok": 1.0},
        msg="distinct should deduplicate -Infinity across float and Decimal128",
    ),
    CommandTestCase(
        "dedup_bool_not_numeric",
        docs=[
            {"_id": 1, "x": 0},
            {"_id": 2, "x": 1},
            {"_id": 3, "x": False},
            {"_id": 4, "x": True},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [0, 1, False, True], "ok": 1.0},
        msg="distinct should not deduplicate booleans with their numeric equivalents",
    ),
    CommandTestCase(
        "dedup_decimal128_trailing_zeros",
        docs=[
            {"_id": 1, "x": Decimal128("0.1")},
            {"_id": 2, "x": Decimal128("0.10")},
            {"_id": 3, "x": Decimal128("0.100")},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [Decimal128("0.1")], "ok": 1.0},
        msg="distinct should deduplicate Decimal128 values with trailing zeros",
    ),
    CommandTestCase(
        "dedup_decimal128_vs_double_distinct",
        docs=[
            {"_id": 1, "x": Decimal128("0.1")},
            {"_id": 2, "x": 0.1},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [Decimal128("0.1"), 0.1], "ok": 1.0},
        msg=(
            "distinct should treat Decimal128 and double as distinct"
            " when they differ in exact representation"
        ),
    ),
    CommandTestCase(
        "dedup_int64_beyond_double_precision",
        docs=[
            {"_id": 1, "x": Int64(DOUBLE_PRECISION_LOSS)},
            {"_id": 2, "x": float(DOUBLE_MAX_SAFE_INTEGER)},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [float(DOUBLE_MAX_SAFE_INTEGER), Int64(DOUBLE_PRECISION_LOSS)],
            "ok": 1.0,
        },
        msg="distinct should compare Int64 at full precision against double",
    ),
    CommandTestCase(
        "dedup_object_key_order_matters",
        docs=[
            {"_id": 1, "x": {"a": 1, "b": 2}},
            {"_id": 2, "x": {"b": 2, "a": 1}},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [{"a": 1, "b": 2}, {"b": 2, "a": 1}],
            "ok": 1.0,
        },
        msg="distinct should treat objects with different key order as distinct",
    ),
    CommandTestCase(
        "dedup_binary_subtype_matters",
        docs=[
            {"_id": 1, "x": Binary(b"hello", 0)},
            {"_id": 2, "x": Binary(b"hello", 5)},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [b"hello", Binary(b"hello", 5)],
            "ok": 1.0,
        },
        msg="distinct should treat same data with different binary subtypes as distinct",
    ),
    CommandTestCase(
        "dedup_timestamp_by_pair",
        docs=[
            {"_id": 1, "x": Timestamp(100, 1)},
            {"_id": 2, "x": Timestamp(100, 1)},
            {"_id": 3, "x": Timestamp(100, 2)},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [Timestamp(100, 1), Timestamp(100, 2)],
            "ok": 1.0,
        },
        msg="distinct should deduplicate Timestamp values by their (time, increment) pair",
    ),
    CommandTestCase(
        "dedup_datetime_millisecond_precision",
        docs=[
            {"_id": 1, "x": datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)},
            {"_id": 2, "x": datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)},
            {"_id": 3, "x": datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [
                datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
            ],
            "ok": 1.0,
        },
        msg="distinct should preserve millisecond precision for datetime deduplication",
    ),
    CommandTestCase(
        "dedup_first_encountered_type_wins",
        docs=[
            {"_id": 1, "x": 5.0},
            {"_id": 2, "x": 5},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [5.0], "ok": 1.0},
        msg="distinct should return the first-encountered type when duplicates exist",
    ),
    CommandTestCase(
        "dedup_decimal128_scientific_notation",
        docs=[
            {"_id": 1, "x": Decimal128("1E+3")},
            {"_id": 2, "x": Decimal128("1000")},
            {"_id": 3, "x": 1000},
            {"_id": 4, "x": 1000.0},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [Decimal128("1E+3")], "ok": 1.0},
        msg=(
            "distinct should deduplicate Decimal128 scientific notation"
            " with equivalent integer and double values"
        ),
    ),
    CommandTestCase(
        "dedup_nan_all_variants",
        docs=[
            {"_id": 1, "x": FLOAT_NAN},
            {"_id": 2, "x": FLOAT_NEGATIVE_NAN},
            {"_id": 3, "x": Decimal128("NaN")},
            {"_id": 4, "x": Decimal128("-NaN")},
            {"_id": 5, "x": Decimal128("sNaN")},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [pytest.approx(FLOAT_NAN, nan_ok=True)],
            "ok": 1.0,
        },
        msg="distinct should deduplicate all NaN variants (NaN, -NaN, sNaN) to one value",
    ),
    CommandTestCase(
        "dedup_regex_flags_matter",
        docs=[
            {"_id": 1, "x": Regex("abc", "i")},
            {"_id": 2, "x": Regex("abc", "")},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [Regex("abc", ""), Regex("abc", "i")],
            "ok": 1.0,
        },
        msg="distinct should treat regex values with different flags as distinct",
    ),
    CommandTestCase(
        "dedup_regex_empty_flags_equals_no_flags",
        docs=[
            {"_id": 1, "x": Regex("abc", "")},
            {"_id": 2, "x": Regex("abc")},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [Regex("abc", "")], "ok": 1.0},
        msg="distinct should deduplicate regex with empty flags and regex with no flags",
    ),
    CommandTestCase(
        "dedup_code_vs_code_with_scope",
        docs=[
            {"_id": 1, "x": Code("function()")},
            {"_id": 2, "x": Code("function()", {"s": 1})},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [Code("function()"), Code("function()", {"s": 1})],
            "ok": 1.0,
        },
        msg="distinct should treat Code and CodeWithScope as distinct types",
    ),
    CommandTestCase(
        "dedup_code_with_scope_different_scopes",
        docs=[
            {"_id": 1, "x": Code("function()", {"x": 1})},
            {"_id": 2, "x": Code("function()", {"x": 2})},
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={
            "values": [
                Code("function()", {"x": 1}),
                Code("function()", {"x": 2}),
            ],
            "ok": 1.0,
        },
        msg="distinct should treat CodeWithScope values with different scopes as distinct",
    ),
]

# Property [Unicode Deduplication]: precomposed and combining Unicode characters
# are distinct under binary comparison but collapsed under ICU collation.
DISTINCT_UNICODE_DEDUP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dedup_unicode_binary_distinct",
        # U+00E9 (precomposed) vs U+0065 U+0301 (combining).
        docs=[{"_id": 1, "x": "\u00e9"}, {"_id": 2, "x": "e\u0301"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": ["e\u0301", "\u00e9"], "ok": 1.0},
        msg=(
            "distinct should treat precomposed and combining characters"
            " as distinct under binary comparison"
        ),
    ),
    CommandTestCase(
        "dedup_unicode_icu_collapsed",
        # U+00E9 (precomposed) vs U+0065 U+0301 (combining).
        docs=[{"_id": 1, "x": "\u00e9"}, {"_id": 2, "x": "e\u0301"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"values": ["\u00e9"], "ok": 1.0},
        msg="distinct should collapse precomposed and combining characters under ICU collation",
    ),
    CommandTestCase(
        "dedup_unicode_simple_locale_distinct",
        # U+00E9 (precomposed) vs U+0065 U+0301 (combining).
        docs=[{"_id": 1, "x": "\u00e9"}, {"_id": 2, "x": "e\u0301"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "collation": {"locale": "simple"},
        },
        expected={"values": ["e\u0301", "\u00e9"], "ok": 1.0},
        msg="distinct should preserve binary distinction with locale=simple",
    ),
]

# Property [Array Unwinding on Views]: array unwinding behavior is identical
# for collections and views.
DISTINCT_ARRAY_UNWINDING_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "array_unwinding_view",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": [1, 2, 3]}, {"_id": 2, "x": [2, 4]}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [1, 2, 3, 4], "ok": 1},
        ignore_order_in=["values"],
        msg="distinct should unwrap arrays identically on views",
    ),
]

DISTINCT_DEDUPLICATION_TESTS: list[CommandTestCase] = (
    DISTINCT_ARRAY_UNWINDING_TESTS
    + DISTINCT_VALUE_DEDUP_TESTS
    + DISTINCT_UNICODE_DEDUP_TESTS
    + DISTINCT_ARRAY_UNWINDING_VIEW_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_DEDUPLICATION_TESTS))
def test_distinct_deduplication(
    database_client: Any, collection: Any, test: CommandTestCase
) -> None:
    """Test distinct deduplication cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
