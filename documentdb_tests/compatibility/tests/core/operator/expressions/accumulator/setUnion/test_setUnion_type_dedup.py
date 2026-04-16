from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Boolean Deduplication]: true and false are distinct from each other
# and from their numeric equivalents.
SETUNION_BOOLEAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bool_dedup_distinct",
        expression={"$setUnion": ["$a"]},
        doc={"a": [True, False, True, False]},
        expected=[False, True],
        msg="$setUnion should treat true and false as distinct values",
    ),
    ExpressionTestCase(
        "bool_dedup_distinct_from_int_true",
        expression={"$setUnion": ["$a"]},
        doc={"a": [True, 1]},
        expected=[1, True],
        msg="$setUnion should treat true and 1 as distinct elements",
    ),
    ExpressionTestCase(
        "bool_dedup_distinct_from_int_false",
        expression={"$setUnion": ["$a"]},
        doc={"a": [False, 0]},
        expected=[0, False],
        msg="$setUnion should treat false and 0 as distinct elements",
    ),
]

# Property [Date/Time Deduplication]: ObjectId, datetime, and Timestamp values
# are deduplicated by value.
SETUNION_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "datetime_dedup_objectid",
        expression={"$setUnion": ["$a"]},
        doc={
            "a": [
                ObjectId("507f1f77bcf86cd799439011"),
                ObjectId("507f1f77bcf86cd799439011"),
                ObjectId("507f1f77bcf86cd799439022"),
            ]
        },
        expected=[
            ObjectId("507f1f77bcf86cd799439011"),
            ObjectId("507f1f77bcf86cd799439022"),
        ],
        msg="$setUnion should deduplicate identical ObjectId values",
    ),
    ExpressionTestCase(
        "datetime_dedup_datetime",
        expression={"$setUnion": ["$a"]},
        doc={
            "a": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, tzinfo=timezone.utc),
            ]
        },
        expected=[
            datetime(2024, 1, 1),
            datetime(2025, 1, 1),
        ],
        msg="$setUnion should deduplicate identical datetime values",
    ),
    ExpressionTestCase(
        "datetime_dedup_timestamp",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Timestamp(1, 1), Timestamp(1, 1), Timestamp(2, 1)]},
        expected=[Timestamp(1, 1), Timestamp(2, 1)],
        msg="$setUnion should deduplicate identical Timestamp values",
    ),
]

# Property [MinKey/MaxKey Deduplication]: MinKey and MaxKey are singletons that
# deduplicate with themselves.
SETUNION_MINMAX_KEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minmax_dedup_minkey",
        expression={"$setUnion": ["$a"]},
        doc={"a": [MinKey(), MinKey()]},
        expected=[MinKey()],
        msg="$setUnion should deduplicate MinKey with itself",
    ),
    ExpressionTestCase(
        "minmax_dedup_maxkey",
        expression={"$setUnion": ["$a"]},
        doc={"a": [MaxKey(), MaxKey()]},
        expected=[MaxKey()],
        msg="$setUnion should deduplicate MaxKey with itself",
    ),
]

# Property [Object Deduplication and Distinctness]: identical objects
# deduplicate; objects differing in key order, values, or key sets are distinct.
SETUNION_OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_dedup_identical",
        expression={"$setUnion": ["$a"]},
        doc={"a": [{"x": 1}, {"x": 1}, {"y": 2}]},
        expected=[{"x": 1}, {"y": 2}],
        msg="$setUnion should deduplicate identical objects",
    ),
    ExpressionTestCase(
        "obj_dedup_key_order_distinct",
        expression={"$setUnion": ["$a"]},
        doc={"a": [{"x": 1, "y": 2}, {"y": 2, "x": 1}]},
        expected=[{"x": 1, "y": 2}, {"y": 2, "x": 1}],
        msg="$setUnion should treat objects with different key order as distinct",
    ),
    ExpressionTestCase(
        "obj_dedup_different_values",
        expression={"$setUnion": ["$a"]},
        doc={"a": [{"x": 1}, {"x": 2}]},
        expected=[{"x": 1}, {"x": 2}],
        msg="$setUnion should treat objects with different values for the same key as distinct",
    ),
    ExpressionTestCase(
        "obj_dedup_different_key_sets",
        expression={"$setUnion": ["$a"]},
        doc={"a": [{"x": 1}, {"y": 1}]},
        expected=[{"x": 1}, {"y": 1}],
        msg="$setUnion should treat objects with different key sets as distinct",
    ),
]

# Property [String Deduplication and Distinctness]: identical strings
# deduplicate; comparison is case-sensitive, does not apply Unicode
# normalization, and correctly handles multi-byte characters and null bytes.
SETUNION_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_dedup_identical",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["a", "a", "b"]},
        expected=["a", "b"],
        msg="$setUnion should deduplicate identical strings",
    ),
    ExpressionTestCase(
        "str_dedup_case_sensitive",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["a", "A"]},
        expected=["a", "A"],
        msg="$setUnion should treat strings differing only in case as distinct",
    ),
    ExpressionTestCase(
        "str_dedup_no_unicode_normalization",
        # U+00E9 (precomposed) vs U+0065 U+0301 (decomposed).
        expression={"$setUnion": ["$a"]},
        doc={"a": ["\u00e9", "e\u0301"]},
        expected=["\u00e9", "e\u0301"],
        msg="$setUnion should treat precomposed and decomposed Unicode forms as distinct",
    ),
    ExpressionTestCase(
        "str_dedup_cjk",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["\u4e16", "\u4e16", "\u754c"]},
        expected=["\u4e16", "\u754c"],
        msg="$setUnion should deduplicate identical CJK characters",
    ),
    ExpressionTestCase(
        "str_dedup_emoji",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["\U0001f600", "\U0001f600", "\U0001f601"]},
        expected=["\U0001f600", "\U0001f601"],
        msg="$setUnion should deduplicate identical emoji characters",
    ),
    ExpressionTestCase(
        "str_dedup_latin_extended",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["\u00f1", "\u00f1", "\u00e7"]},
        expected=["\u00f1", "\u00e7"],
        msg="$setUnion should deduplicate identical Latin extended characters",
    ),
    ExpressionTestCase(
        "str_dedup_empty_strings",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["", ""]},
        expected=[""],
        msg="$setUnion should deduplicate empty strings with each other",
    ),
    ExpressionTestCase(
        "str_dedup_null_byte",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["a\x00b", "a\x00b"]},
        expected=["a\x00b"],
        msg="$setUnion should deduplicate identical strings containing null bytes",
    ),
    ExpressionTestCase(
        "str_dedup_null_byte_distinct_from_prefix",
        expression={"$setUnion": ["$a"]},
        doc={"a": ["a\x00b", "a"]},
        expected=["a\x00b", "a"],
        msg="$setUnion should treat a null-byte string as distinct from its prefix",
    ),
]

# Property [Regex Deduplication and Distinctness]: identical regexes
# deduplicate; different patterns or flags are distinct, and flag ordering does
# not affect deduplication.
SETUNION_REGEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "regex_dedup_identical",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Regex("abc", "i"), Regex("abc", "i"), Regex("def", "")]},
        expected=[Regex("abc", "i"), Regex("def", "")],
        msg="$setUnion should deduplicate identical Regex values",
    ),
    ExpressionTestCase(
        "regex_dedup_different_patterns",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Regex("abc", "i"), Regex("def", "i")]},
        expected=[Regex("abc", "i"), Regex("def", "i")],
        msg="$setUnion should treat regexes with different patterns as distinct",
    ),
    ExpressionTestCase(
        "regex_dedup_different_flags",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Regex("abc", "i"), Regex("abc", "m")]},
        expected=[Regex("abc", "i"), Regex("abc", "m")],
        msg="$setUnion should treat regexes with different flags as distinct",
    ),
    ExpressionTestCase(
        "regex_dedup_flag_order_canonicalized",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Regex("abc", "im"), Regex("abc", "mi")]},
        expected=[Regex("abc", "im")],
        msg="$setUnion should treat regexes with reordered flags as duplicates",
    ),
]

# Property [Binary Deduplication and Distinctness]: identical Binary values
# deduplicate; different subtypes with identical bytes are distinct.
SETUNION_BINARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_dedup_identical",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Binary(b"\x01"), Binary(b"\x01"), Binary(b"\x02")]},
        expected=[b"\x01", b"\x02"],
        msg="$setUnion should deduplicate identical Binary values",
    ),
    ExpressionTestCase(
        "binary_dedup_different_subtypes_same_bytes",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Binary(b"\x01\x02", 0), Binary(b"\x01\x02", 5)]},
        expected=[b"\x01\x02", Binary(b"\x01\x02", 5)],
        msg="$setUnion should treat Binary with different subtypes as distinct",
    ),
]

# Property [Code Deduplication and Distinctness]: identical Code values
# deduplicate; Code and CodeWithScope are distinct types, and CodeWithScope
# values with different scopes are distinct.
SETUNION_CODE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "code_dedup_identical",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Code("f()"), Code("f()"), Code("g()")]},
        expected=[Code("f()"), Code("g()")],
        msg="$setUnion should deduplicate identical Code values",
    ),
    ExpressionTestCase(
        "code_dedup_identical_with_scope",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Code("f()", {}), Code("f()", {}), Code("g()", {})]},
        expected=[Code("f()", {}), Code("g()", {})],
        msg="$setUnion should deduplicate identical CodeWithScope values",
    ),
    ExpressionTestCase(
        "code_vs_cws_empty_scope_distinct",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Code("f()"), Code("f()", {})]},
        expected=[Code("f()"), Code("f()", {})],
        msg="$setUnion should treat Code and CodeWithScope as distinct",
    ),
    ExpressionTestCase(
        "code_vs_cws_different_scopes_distinct",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Code("f()", {"x": 1}), Code("f()", {"y": 2})]},
        expected=[Code("f()", {"x": 1}), Code("f()", {"y": 2})],
        msg="$setUnion should treat CodeWithScope values with different scopes as distinct",
    ),
]

_ALL_BSON_ELEMENTS = [
    "hello",
    42,
    Int64(99),
    1.5,
    Decimal128("3.14"),
    True,
    False,
    None,
    {"key": "val"},
    [1, 2],
    ObjectId("507f1f77bcf86cd799439011"),
    datetime(2024, 1, 1),
    Timestamp(1, 1),
    b"\x01\x02\x03",
    Regex("abc", 2),
    MinKey(),
    MaxKey(),
    Code("function(){}"),
    Code("function(){}", {}),
]

# Property [All BSON Types Distinct]: all standard BSON types are preserved as
# distinct elements in a single union.
SETUNION_ALL_BSON_TYPES_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_bson_types_single_array",
        expression={"$setUnion": ["$a"]},
        doc={"a": _ALL_BSON_ELEMENTS},
        expected=_ALL_BSON_ELEMENTS,
        msg="$setUnion should preserve all 19 standard BSON types as distinct elements",
    ),
    ExpressionTestCase(
        "all_bson_types_two_arrays",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": _ALL_BSON_ELEMENTS[:10], "b": _ALL_BSON_ELEMENTS[10:]},
        expected=_ALL_BSON_ELEMENTS,
        msg="$setUnion should preserve all 19 standard BSON types across two arrays",
    ),
]

SETUNION_TYPE_DEDUP_TESTS_ALL = (
    SETUNION_BOOLEAN_TESTS
    + SETUNION_DATETIME_TESTS
    + SETUNION_MINMAX_KEY_TESTS
    + SETUNION_OBJECT_TESTS
    + SETUNION_STRING_TESTS
    + SETUNION_REGEX_TESTS
    + SETUNION_BINARY_TESTS
    + SETUNION_CODE_TESTS
    + SETUNION_ALL_BSON_TYPES_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_TYPE_DEDUP_TESTS_ALL))
def test_setunion_type_dedup(collection, test_case: ExpressionTestCase):
    """Test $setUnion type deduplication cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order=True,
    )
