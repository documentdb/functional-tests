"""Tests for $setUnion accumulator: element deduplication across all BSON types."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [String Element Deduplication]: strings are compared case-sensitively
# with no Unicode normalization.
SETUNION_STRING_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string_case_sensitive",
        docs=[{"v": ["a"]}, {"v": ["A"]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat 'a' and 'A' as distinct (case-sensitive)",
    ),
    AccumulatorTestCase(
        "string_unicode_no_normalization",
        docs=[
            {"v": ["\u00e9"]},  # precomposed e-acute
            {"v": ["e\u0301"]},  # decomposed e + combining acute
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should not normalize Unicode (precomposed vs decomposed are distinct)",
    ),
    AccumulatorTestCase(
        "string_empty_dedup",
        docs=[{"v": [""]}, {"v": [""]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": [""]}],
        msg="$setUnion should deduplicate identical empty strings",
    ),
]

# Property [Object Element Deduplication]: objects are compared by structure
# including key order.
SETUNION_OBJECT_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "object_identical_dedup",
        docs=[{"v": [{"x": 1}]}, {"v": [{"x": 1}]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"x": 1}]}],
        msg="$setUnion should deduplicate identical objects",
    ),
    AccumulatorTestCase(
        "object_key_order_matters",
        docs=[{"v": [{"x": 1, "y": 2}]}, {"v": [{"y": 2, "x": 1}]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat objects with different key order as distinct",
    ),
    AccumulatorTestCase(
        "object_different_values",
        docs=[{"v": [{"x": 1}]}, {"v": [{"x": 2}]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat objects with different values as distinct",
    ),
]

# Property [Boolean Element Deduplication]: boolean values are distinct BSON
# types from numeric values.
SETUNION_BOOLEAN_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bool_true_dedup",
        docs=[{"v": [True]}, {"v": [True]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": [True]}],
        msg="$setUnion should deduplicate true values",
    ),
    AccumulatorTestCase(
        "bool_false_dedup",
        docs=[{"v": [False]}, {"v": [False]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": [False]}],
        msg="$setUnion should deduplicate false values",
    ),
    AccumulatorTestCase(
        "bool_true_and_false_distinct",
        docs=[{"v": [True]}, {"v": [False]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat true and false as distinct elements",
    ),
    AccumulatorTestCase(
        "bool_true_vs_int_1_distinct",
        docs=[{"v": [True]}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat true and int(1) as distinct BSON types",
    ),
    AccumulatorTestCase(
        "bool_false_vs_int_0_distinct",
        docs=[{"v": [False]}, {"v": [0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat false and int(0) as distinct BSON types",
    ),
    AccumulatorTestCase(
        "bool_false_vs_double_0_distinct",
        docs=[{"v": [False]}, {"v": [0.0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat false and double(0.0) as distinct BSON types",
    ),
    AccumulatorTestCase(
        "bool_true_vs_double_1_distinct",
        docs=[{"v": [True]}, {"v": [1.0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat true and double(1.0) as distinct BSON types",
    ),
]

# Property [DateTime/Timestamp/ObjectId Deduplication]: temporal and ID types
# deduplicate by value.
SETUNION_DATETIME_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "datetime_identical_dedup",
        docs=[
            {"v": [datetime(2023, 6, 15, tzinfo=timezone.utc)]},
            {"v": [datetime(2023, 6, 15, tzinfo=timezone.utc)]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate identical datetime elements",
    ),
    AccumulatorTestCase(
        "datetime_different_preserved",
        docs=[
            {"v": [datetime(2023, 1, 1, tzinfo=timezone.utc)]},
            {"v": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should preserve different datetime elements",
    ),
    AccumulatorTestCase(
        "timestamp_identical_dedup",
        docs=[{"v": [Timestamp(100, 1)]}, {"v": [Timestamp(100, 1)]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate identical Timestamp elements",
    ),
    AccumulatorTestCase(
        "objectid_identical_dedup",
        docs=[
            {"v": [ObjectId("507f1f77bcf86cd799439011")]},
            {"v": [ObjectId("507f1f77bcf86cd799439011")]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate identical ObjectId elements",
    ),
]

# Property [Binary/Regex Deduplication]: binary data and regex types
# deduplicate by value and subtype/flags.
SETUNION_BINARY_REGEX_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "binary_identical_dedup",
        docs=[{"v": [Binary(b"\x01\x02")]}, {"v": [Binary(b"\x01\x02")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate identical Binary elements",
    ),
    AccumulatorTestCase(
        "binary_different_subtype_distinct",
        docs=[
            {"v": [Binary(b"\x01\x02", 0)]},
            {"v": [Binary(b"\x01\x02", 5)]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat Binary with different subtypes as distinct",
    ),
    AccumulatorTestCase(
        "regex_identical_dedup",
        docs=[{"v": [Regex("abc", "i")]}, {"v": [Regex("abc", "i")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate identical Regex elements",
    ),
    AccumulatorTestCase(
        "regex_different_flags_distinct",
        docs=[{"v": [Regex("abc", "i")]}, {"v": [Regex("abc", "m")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat Regex with different flags as distinct",
    ),
]

# Property [MinKey/MaxKey Deduplication]: MinKey and MaxKey are singletons
# that deduplicate with themselves.
SETUNION_MINKEY_MAXKEY_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "minkey_dedup",
        docs=[{"v": [MinKey()]}, {"v": [MinKey()]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate MinKey elements to single MinKey",
    ),
    AccumulatorTestCase(
        "maxkey_dedup",
        docs=[{"v": [MaxKey()]}, {"v": [MaxKey()]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate MaxKey elements to single MaxKey",
    ),
    AccumulatorTestCase(
        "minkey_maxkey_distinct",
        docs=[{"v": [MinKey()]}, {"v": [MaxKey()]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat MinKey and MaxKey as distinct elements",
    ),
]

# Property [All BSON Types as Elements]: arrays containing each BSON type as
# elements are correctly unioned with all types preserved.
SETUNION_ALL_BSON_TYPES_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "all_bson_types_distinct",
        docs=[
            {"v": [42]},
            {"v": [Int64(100)]},
            {"v": [3.14]},
            {"v": [Decimal128("2.5")]},
            {"v": ["hello"]},
            {"v": [True]},
            {"v": [False]},
            {"v": [{"a": 1}]},
            {"v": [ObjectId("507f1f77bcf86cd799439011")]},
            {"v": [datetime(2023, 1, 1, tzinfo=timezone.utc)]},
            {"v": [Timestamp(1, 1)]},
            {"v": [Binary(b"\x01")]},
            {"v": [Regex("x", "")]},
            {"v": [Code("function(){}")]},
            {"v": [MinKey()]},
            {"v": [MaxKey()]},
            {"v": [None]},
            {"v": [[1, 2]]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 18}],
        msg="$setUnion should preserve all 18 distinct BSON type elements",
    ),
    AccumulatorTestCase(
        "all_bson_types_dedup",
        docs=[
            {
                "v": [
                    42,
                    Int64(100),
                    3.14,
                    Decimal128("2.5"),
                    "hello",
                    True,
                    False,
                    {"a": 1},
                    ObjectId("507f1f77bcf86cd799439011"),
                    datetime(2023, 1, 1, tzinfo=timezone.utc),
                    Timestamp(1, 1),
                    Binary(b"\x01"),
                    Regex("x", ""),
                    Code("function(){}"),
                    MinKey(),
                    MaxKey(),
                    None,
                    [1, 2],
                ]
            },
            {
                "v": [
                    42,
                    Int64(100),
                    3.14,
                    Decimal128("2.5"),
                    "hello",
                    True,
                    False,
                    {"a": 1},
                    ObjectId("507f1f77bcf86cd799439011"),
                    datetime(2023, 1, 1, tzinfo=timezone.utc),
                    Timestamp(1, 1),
                    Binary(b"\x01"),
                    Regex("x", ""),
                    Code("function(){}"),
                    MinKey(),
                    MaxKey(),
                    None,
                    [1, 2],
                ]
            },
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 18}],
        msg="$setUnion should deduplicate all BSON types to single instance of each",
    ),
]

# Property [Mixed Element Types Within Array]: arrays containing a mix of
# different BSON types are correctly unioned with cross-document deduplication
# applied per-element regardless of surrounding element types.
SETUNION_MIXED_ELEMENT_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_types_partial_overlap",
        docs=[
            {"v": [1, "a", {"id": 1}, None, [1, 2]]},
            {"v": ["a", 2, {"id": 1}, None]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 6}],
        msg="$setUnion should deduplicate mixed-type elements across documents",
    ),
    AccumulatorTestCase(
        "mixed_types_three_docs_overlap",
        docs=[
            {"v": [1, "hello", True]},
            {"v": ["hello", 2, False]},
            {"v": [True, False, 3]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 6}],
        msg="$setUnion should deduplicate across three docs with mixed int/string/bool elements",
    ),
    AccumulatorTestCase(
        "mixed_types_nested_and_scalar",
        docs=[
            {"v": [{"x": 1}, [10, 20], "abc", 42]},
            {"v": [42, "abc", [10, 20], {"x": 2}]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 5}],
        msg="$setUnion should deduplicate mixed scalars, objects, and nested arrays",
    ),
]

SETUNION_ELEMENT_DEDUP_TESTS = (
    SETUNION_STRING_DEDUP_TESTS
    + SETUNION_OBJECT_DEDUP_TESTS
    + SETUNION_BOOLEAN_DEDUP_TESTS
    + SETUNION_DATETIME_DEDUP_TESTS
    + SETUNION_BINARY_REGEX_DEDUP_TESTS
    + SETUNION_MINKEY_MAXKEY_DEDUP_TESTS
    + SETUNION_ALL_BSON_TYPES_TESTS
    + SETUNION_MIXED_ELEMENT_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_ELEMENT_DEDUP_TESTS))
def test_accumulator_setUnion_element_dedup(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator element deduplication across BSON types."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
