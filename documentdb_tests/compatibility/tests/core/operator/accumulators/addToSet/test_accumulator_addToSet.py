"""Tests for $addToSet accumulator ($group)."""

from __future__ import annotations

import math
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

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [Null Collected]: null values are collected as valid values and deduplicated.
ADDTOSET_NULL_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null and deduplicate to a single null",
    ),
    AccumulatorTestCase(
        "null_single",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect a single null value",
    ),
    AccumulatorTestCase(
        "null_among_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None, 5, 3]}],
        msg="$addToSet should collect null alongside other values",
    ),
    AccumulatorTestCase(
        "null_and_values_dedup",
        docs=[{"v": 10}, {"v": None}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, None, 5]}],
        msg="$addToSet should collect null and distinct values without duplication",
    ),
]

# Property [Missing Excluded]: missing fields are excluded from the result.
ADDTOSET_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_all",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should return empty array when all fields are missing",
    ),
    AccumulatorTestCase(
        "missing_single",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should return empty array for a single doc with missing field",
    ),
    AccumulatorTestCase(
        "missing_among_values",
        docs=[{"x": 1}, {"v": 5}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5, 3]}],
        msg="$addToSet should exclude missing fields and collect only present values",
    ),
]

# Property [Null and Missing Combined]: null is collected while missing is excluded.
ADDTOSET_NULL_MISSING_COMBINED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "combined_null_and_missing",
        docs=[{"v": None}, {"x": 1}, {"v": None}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null but exclude missing fields",
    ),
    AccumulatorTestCase(
        "combined_null_missing_and_values",
        docs=[{"v": 10}, {"v": None}, {"x": 1}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, None, 5]}],
        msg="$addToSet should collect null and values but exclude missing fields",
    ),
]

# Property [$$REMOVE Excluded]: $$REMOVE via $cond is treated as missing.
ADDTOSET_REMOVE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_all",
        docs=[{"v": -1}, {"v": -2}, {"v": -3}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should treat $$REMOVE as missing and return empty array",
    ),
    AccumulatorTestCase(
        "remove_some",
        docs=[{"v": -1}, {"v": 5}, {"v": -2}, {"v": 10}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5, 10]}],
        msg="$addToSet should exclude $$REMOVE values and collect the rest",
    ),
    AccumulatorTestCase(
        "remove_and_null_value",
        docs=[{"v": 1}, {"v": 2}, {"v": 3}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gt": ["$v", 2]}, None, "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null produced by $cond while excluding $$REMOVE",
    ),
    AccumulatorTestCase(
        "remove_dedup",
        docs=[{"v": 5}, {"v": 5}, {"v": -1}, {"v": -2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5]}],
        msg="$addToSet should deduplicate values and exclude $$REMOVE entries",
    ),
]

# Property [Unique Value Collection]: $addToSet returns an array of all unique values.
ADDTOSET_UNIQUE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "unique_distinct",
        docs=[{"v": 10}, {"v": 20}, {"v": 30}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20, 30]}],
        msg="$addToSet should return all distinct values",
    ),
    AccumulatorTestCase(
        "unique_with_duplicates",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20, 30]}],
        msg="$addToSet should deduplicate repeated values",
    ),
    AccumulatorTestCase(
        "unique_all_same",
        docs=[{"v": 42}, {"v": 42}, {"v": 42}, {"v": 42}, {"v": 42}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [42]}],
        msg="$addToSet should collapse identical values into one element",
    ),
    AccumulatorTestCase(
        "unique_single_doc",
        docs=[{"v": 7}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [7]}],
        msg="$addToSet should return single-element array for one document",
    ),
]

# Property [Array as Single Element]: array values are appended as a single element, not unwound.
ADDTOSET_ARRAY_ELEMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "array_distinct",
        docs=[{"v": [1, 2]}, {"v": [3, 4]}, {"v": [1, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[1, 2], [3, 4]]}],
        msg="$addToSet should treat arrays as single elements and deduplicate identical arrays",
    ),
    AccumulatorTestCase(
        "array_empty",
        docs=[{"v": []}, {"v": []}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[], [1]]}],
        msg="$addToSet should treat empty arrays as single elements and deduplicate them",
    ),
    AccumulatorTestCase(
        "array_nested",
        docs=[{"v": [[1]]}, {"v": [[2]]}, {"v": [[1]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[[1]], [[2]]]}],
        msg="$addToSet should treat nested arrays as single elements and deduplicate them",
    ),
    AccumulatorTestCase(
        "array_mixed_scalar",
        docs=[{"v": 1}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, [1]]}],
        msg="$addToSet should distinguish scalar 1 from array [1]",
    ),
    AccumulatorTestCase(
        "array_single_doc",
        docs=[{"v": [1, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[1, 2, 3]]}],
        msg="$addToSet should wrap the array value as a single element in the result",
    ),
]

# Property [Document Duplicate Detection]: documents are duplicates only if they have
# exact same fields, values, and field order.
ADDTOSET_DOC_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "doc_identical",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 1, "b": 2}]}],
        msg="$addToSet should deduplicate identical documents",
    ),
    AccumulatorTestCase(
        "doc_different_field_order",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"b": 2, "a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"b": 2, "a": 1}, {"a": 1, "b": 2}]}],
        msg="$addToSet should treat documents with different field order as distinct",
    ),
    AccumulatorTestCase(
        "doc_different_values",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 3}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 1, "b": 2}, {"a": 1, "b": 3}]}],
        msg="$addToSet should treat documents with different values as distinct",
    ),
    AccumulatorTestCase(
        "doc_nested_identical",
        docs=[{"v": {"a": {"x": 1}}}, {"v": {"a": {"x": 1}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": {"x": 1}}]}],
        msg="$addToSet should deduplicate nested documents with identical structure",
    ),
    AccumulatorTestCase(
        "doc_nested_different_order",
        docs=[{"v": {"a": {"x": 1, "y": 2}}}, {"v": {"a": {"y": 2, "x": 1}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": {"x": 1, "y": 2}}, {"a": {"y": 2, "x": 1}}]}],
        msg="$addToSet should treat nested documents with different field order as distinct",
    ),
    AccumulatorTestCase(
        "doc_empty",
        docs=[{"v": {}}, {"v": {}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{}]}],
        msg="$addToSet should deduplicate empty documents",
    ),
    AccumulatorTestCase(
        "doc_subset",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1, "b": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 1, "b": 2}, {"a": 1}]}],
        msg="$addToSet should treat a document subset and superset as distinct",
    ),
    AccumulatorTestCase(
        "doc_with_array_value",
        docs=[{"v": {"a": [1, 2]}}, {"v": {"a": [1, 2]}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": [1, 2]}]}],
        msg="$addToSet should deduplicate documents containing identical array values",
    ),
    AccumulatorTestCase(
        "doc_with_null_value",
        docs=[{"v": {"a": None}}, {"v": {"a": None}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": None}]}],
        msg="$addToSet should deduplicate documents with null field values",
    ),
    AccumulatorTestCase(
        "doc_with_nested_null",
        docs=[{"v": {"a": {"b": None}}}, {"v": {"a": {"b": None}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": {"b": None}}]}],
        msg="$addToSet should deduplicate documents with nested null values",
    ),
]

# Property [String Deduplication]: strings are compared by byte value with no Unicode normalization.
ADDTOSET_STRING_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string_identical",
        docs=[{"v": "abc"}, {"v": "abc"}, {"v": "def"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["abc", "def"]}],
        msg="$addToSet should deduplicate identical strings",
    ),
    AccumulatorTestCase(
        "string_empty",
        docs=[{"v": ""}, {"v": ""}, {"v": "x"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["", "x"]}],
        msg="$addToSet should deduplicate empty strings",
    ),
    AccumulatorTestCase(
        "string_unicode_no_normalization",
        docs=[
            {"v": "\u00e9"},
            {"v": "\u0065\u0301"},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["\u00e9", "\u0065\u0301"]}],
        msg="$addToSet should not normalize Unicode; precomposed and decomposed are distinct",
    ),
]

# Property [BSON Type Collection]: $addToSet collects and deduplicates values of every
# non-deprecated BSON type.
ADDTOSET_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_int32",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20]}],
        msg="$addToSet should collect and deduplicate int32 values",
    ),
    AccumulatorTestCase(
        "bson_int64",
        docs=[{"v": Int64(10)}, {"v": Int64(20)}, {"v": Int64(10)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Int64(10), Int64(20)]}],
        msg="$addToSet should collect and deduplicate Int64 values",
    ),
    AccumulatorTestCase(
        "bson_double",
        docs=[{"v": 1.5}, {"v": 2.5}, {"v": 1.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1.5, 2.5]}],
        msg="$addToSet should collect and deduplicate double values",
    ),
    AccumulatorTestCase(
        "bson_decimal128",
        docs=[
            {"v": Decimal128("1.5")},
            {"v": Decimal128("2.5")},
            {"v": Decimal128("1.5")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("1.5"), Decimal128("2.5")]}],
        msg="$addToSet should collect and deduplicate Decimal128 values",
    ),
    AccumulatorTestCase(
        "bson_string",
        docs=[{"v": "abc"}, {"v": "def"}, {"v": "abc"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["abc", "def"]}],
        msg="$addToSet should collect and deduplicate string values",
    ),
    AccumulatorTestCase(
        "bson_bool",
        docs=[{"v": True}, {"v": False}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [True, False]}],
        msg="$addToSet should collect and deduplicate boolean values",
    ),
    AccumulatorTestCase(
        "bson_datetime",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2021, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[
            {
                "result": [
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2021, 1, 1, tzinfo=timezone.utc),
                ]
            }
        ],
        msg="$addToSet should collect and deduplicate datetime values",
    ),
    AccumulatorTestCase(
        "bson_objectid",
        docs=[
            {"v": ObjectId("000000000000000000000001")},
            {"v": ObjectId("000000000000000000000002")},
            {"v": ObjectId("000000000000000000000001")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[
            {
                "result": [
                    ObjectId("000000000000000000000001"),
                    ObjectId("000000000000000000000002"),
                ]
            }
        ],
        msg="$addToSet should collect and deduplicate ObjectId values",
    ),
    AccumulatorTestCase(
        "bson_binary",
        docs=[{"v": Binary(b"\x00")}, {"v": Binary(b"\x01")}, {"v": Binary(b"\x00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [b"\x00", b"\x01"]}],
        msg="$addToSet should collect and deduplicate Binary values",
    ),
    AccumulatorTestCase(
        "bson_regex",
        docs=[{"v": Regex("abc")}, {"v": Regex("def")}, {"v": Regex("abc")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Regex("abc"), Regex("def")]}],
        msg="$addToSet should collect and deduplicate Regex values",
    ),
    AccumulatorTestCase(
        "bson_code",
        docs=[
            {"v": Code("function(){}")},
            {"v": Code("function(){return 1}")},
            {"v": Code("function(){}")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["function(){}", "function(){return 1}"]}],
        msg="$addToSet should collect and deduplicate Code values",
    ),
    AccumulatorTestCase(
        "bson_timestamp",
        docs=[
            {"v": Timestamp(100, 1)},
            {"v": Timestamp(200, 1)},
            {"v": Timestamp(100, 1)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Timestamp(100, 1), Timestamp(200, 1)]}],
        msg="$addToSet should collect and deduplicate Timestamp values",
    ),
    AccumulatorTestCase(
        "bson_minkey",
        docs=[{"v": MinKey()}, {"v": MinKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"": MinKey()}]}],
        msg="$addToSet should deduplicate MinKey values",
    ),
    AccumulatorTestCase(
        "bson_maxkey",
        docs=[{"v": MaxKey()}, {"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"": MaxKey()}]}],
        msg="$addToSet should deduplicate MaxKey values",
    ),
    AccumulatorTestCase(
        "bson_document",
        docs=[{"v": {"x": 1}}, {"v": {"x": 2}}, {"v": {"x": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"x": 1}, {"x": 2}]}],
        msg="$addToSet should collect and deduplicate embedded document values",
    ),
    AccumulatorTestCase(
        "bson_array",
        docs=[{"v": [1, 2]}, {"v": [3, 4]}, {"v": [1, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[1, 2], [3, 4]]}],
        msg="$addToSet should collect and deduplicate array values as single elements",
    ),
    AccumulatorTestCase(
        "bson_null",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should deduplicate null values",
    ),
]

# Property [Mixed Type Collection]: $addToSet collects values of different
# BSON types in the same group.
ADDTOSET_MIXED_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_types",
        docs=[
            {"v": 42},
            {"v": "hello"},
            {"v": True},
            {"v": [1, 2]},
            {"v": {"a": 1}},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [42, "hello", True, [1, 2], {"a": 1}]}],
        msg="$addToSet should collect values of different BSON types in one group",
    ),
]

# Property [Numeric Equivalence]: numerically equivalent values across types are deduplicated.
ADDTOSET_NUMERIC_EQUIV_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_all_ones",
        docs=[{"v": 1}, {"v": Int64(1)}, {"v": 1.0}, {"v": Decimal128("1")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1]}],
        msg="$addToSet should deduplicate numerically equivalent values of all numeric types",
    ),
    AccumulatorTestCase(
        "equiv_all_zeros",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": 0.0}, {"v": Decimal128("0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [0]}],
        msg="$addToSet should deduplicate numerically equivalent zero values",
    ),
    AccumulatorTestCase(
        "equiv_int32_int64",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5]}],
        msg="$addToSet should deduplicate int32 and Int64 with same numeric value",
    ),
    AccumulatorTestCase(
        "equiv_double_int32",
        docs=[{"v": 3.0}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [3.0]}],
        msg="$addToSet should deduplicate double and int32 with same numeric value",
    ),
    AccumulatorTestCase(
        "equiv_decimal128_int64",
        docs=[{"v": Decimal128("100")}, {"v": Int64(100)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("100")]}],
        msg="$addToSet should deduplicate Decimal128 and Int64 with same numeric value",
    ),
    AccumulatorTestCase(
        "equiv_negative",
        docs=[{"v": -1}, {"v": Int64(-1)}, {"v": -1.0}, {"v": Decimal128("-1")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [-1]}],
        msg="$addToSet should deduplicate negative numerically equivalent values",
    ),
]

# Property [BSON Type Distinction]: values of different BSON types are distinct even when similar.
ADDTOSET_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [0, False]}],
        msg="$addToSet should treat false and int32(0) as distinct BSON types",
    ),
    AccumulatorTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, True]}],
        msg="$addToSet should treat true and int32(1) as distinct BSON types",
    ),
    AccumulatorTestCase(
        "distinct_null_vs_missing",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null but exclude missing field",
    ),
    AccumulatorTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["", None]}],
        msg="$addToSet should treat empty string and null as distinct",
    ),
    AccumulatorTestCase(
        "distinct_string_vs_number",
        docs=[{"v": "123"}, {"v": 123}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [123, "123"]}],
        msg="$addToSet should treat string '123' and int 123 as distinct",
    ),
]

# Property [NaN Deduplication]: NaN values are equal for deduplication purposes.
ADDTOSET_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_double_dedup",
        docs=[{"v": float("nan")}, {"v": float("nan")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [pytest.approx(math.nan, nan_ok=True)]}],
        msg="$addToSet should deduplicate double NaN values",
    ),
    AccumulatorTestCase(
        "nan_decimal128_dedup",
        docs=[{"v": Decimal128("NaN")}, {"v": Decimal128("NaN")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("NaN")]}],
        msg="$addToSet should deduplicate Decimal128 NaN values",
    ),
    AccumulatorTestCase(
        "nan_cross_type",
        docs=[{"v": float("nan")}, {"v": Decimal128("NaN")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [pytest.approx(math.nan, nan_ok=True)]}],
        msg="$addToSet should deduplicate float NaN and Decimal128 NaN as numerically equal",
    ),
    AccumulatorTestCase(
        "nan_with_finite",
        docs=[{"v": float("nan")}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [pytest.approx(math.nan, nan_ok=True), 5]}],
        msg="$addToSet should treat NaN and finite values as distinct",
    ),
]

# Property [Infinity Deduplication]: Infinity values are equal across numeric types.
ADDTOSET_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "inf_double_dedup",
        docs=[{"v": float("inf")}, {"v": float("inf")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("inf")]}],
        msg="$addToSet should deduplicate positive Infinity values",
    ),
    AccumulatorTestCase(
        "neg_inf_double_dedup",
        docs=[{"v": float("-inf")}, {"v": float("-inf")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("-inf")]}],
        msg="$addToSet should deduplicate negative Infinity values",
    ),
    AccumulatorTestCase(
        "inf_cross_type",
        docs=[{"v": float("inf")}, {"v": Decimal128("Infinity")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("inf")]}],
        msg="$addToSet should deduplicate float Infinity and Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "inf_vs_neg_inf",
        docs=[{"v": float("inf")}, {"v": float("-inf")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("-inf"), float("inf")]}],
        msg="$addToSet should treat positive and negative Infinity as distinct",
    ),
]

# Property [Negative Zero]: -0.0 and 0.0 are numerically equal and deduplicated.
ADDTOSET_NEG_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "neg_zero_double",
        docs=[{"v": -0.0}, {"v": 0.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [-0.0]}],
        msg="$addToSet should deduplicate -0.0 and 0.0 as numerically equal",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128",
        docs=[{"v": Decimal128("-0")}, {"v": Decimal128("0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("-0")]}],
        msg="$addToSet should deduplicate Decimal128 -0 and 0 as numerically equal",
    ),
    AccumulatorTestCase(
        "neg_zero_cross_type",
        docs=[{"v": -0.0}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [-0.0]}],
        msg="$addToSet should deduplicate -0.0 and int 0 as numerically equal",
    ),
]

# Property [Decimal128 Precision]: Decimal128 values with same numeric value but different
# representations are deduplicated.
ADDTOSET_DECIMAL128_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("1.0")]}],
        msg="$addToSet should deduplicate Decimal128 values with different trailing zeros",
    ),
    AccumulatorTestCase(
        "decimal_34_digit_precision",
        docs=[{"v": Decimal128("1.234567890123456789012345678901234")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("1.234567890123456789012345678901234")]}],
        msg="$addToSet should preserve full 34-digit Decimal128 precision",
    ),
    AccumulatorTestCase(
        "decimal_max_min_distinct",
        docs=[
            {"v": Decimal128("9.999999999999999999999999999999999E+6144")},
            {"v": Decimal128("1E-6176")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[
            {
                "result": [
                    Decimal128("1E-6176"),
                    Decimal128("9.999999999999999999999999999999999E+6144"),
                ]
            }
        ],
        msg="$addToSet should treat Decimal128 max and min as distinct values",
    ),
]

# Property [Expression Arguments]: $addToSet accepts various expression forms.
ADDTOSET_EXPRESSION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_field_path",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20]}],
        msg="$addToSet should collect values from a field path expression",
    ),
    AccumulatorTestCase(
        "expr_nested_field",
        docs=[{"a": {"b": 1}}, {"a": {"b": 2}}, {"a": {"b": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$a.b"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$addToSet should collect values from a nested field path",
    ),
    AccumulatorTestCase(
        "expr_literal",
        docs=[{"v": 1}, {"v": 2}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": 42}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [42]}],
        msg="$addToSet should deduplicate a constant literal applied to all docs",
    ),
    AccumulatorTestCase(
        "expr_computed",
        docs=[{"price": 10, "qty": 2}, {"price": 5, "qty": 3}, {"price": 10, "qty": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": {"$multiply": ["$price", "$qty"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, 15]}],
        msg="$addToSet should collect unique computed expression results",
    ),
    AccumulatorTestCase(
        "expr_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": None}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null literal and deduplicate across docs",
    ),
    AccumulatorTestCase(
        "expr_composite_array_path",
        docs=[{"a": [{"b": 1}, {"b": 2}]}, {"a": [{"b": 3}, {"b": 1}]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$a.b"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[3, 1], [1, 2]]}],
        msg="$addToSet should collect array values from composite array path",
    ),
]

# Property [Grouping by Key]: groups compute independently.
ADDTOSET_GROUPING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multi_group",
        docs=[
            {"g": "A", "v": 1},
            {"g": "A", "v": 2},
            {"g": "A", "v": 1},
            {"g": "B", "v": 3},
            {"g": "B", "v": 3},
            {"g": "B", "v": 4},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$addToSet": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 2]},
            {"_id": "B", "result": [3, 4]},
        ],
        msg="$addToSet should compute unique sets independently per group key",
    ),
]

# Property [Empty Collection]: $group on empty collection produces no output.
ADDTOSET_EMPTY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_collection",
        docs=None,
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[],
        msg="$addToSet should produce no output documents for an empty collection",
    ),
]

# Property [Edge Cases]: accumulator-specific edge cases.
ADDTOSET_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should return [null] for single null document",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should return empty array for single document with missing field",
    ),
    AccumulatorTestCase(
        "edge_many_unique",
        docs=[{"v": i} for i in range(100)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": list(range(100))}],
        msg="$addToSet should collect 100 unique values into a 100-element array",
    ),
    AccumulatorTestCase(
        "edge_many_docs_few_unique",
        docs=[{"v": i % 5} for i in range(100)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [0, 1, 2, 3, 4]}],
        msg="$addToSet should deduplicate 100 docs down to 5 unique values",
    ),
    AccumulatorTestCase(
        "edge_array_field_not_traversed",
        docs=[{"v": [5, 1, 8]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[5, 1, 8]]}],
        msg="$addToSet should treat array field as a single element, not traverse it",
    ),
    AccumulatorTestCase(
        "edge_mixed_array_scalar",
        docs=[{"v": 5}, {"v": [5]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5, [5]]}],
        msg="$addToSet should distinguish scalar 5 from array [5]",
    ),
    AccumulatorTestCase(
        "edge_binary_different_subtypes",
        docs=[{"v": Binary(b"\x00", 0)}, {"v": Binary(b"\x00", 5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [b"\x00", Binary(b"\x00", 5)]}],
        msg="$addToSet should treat Binary values with different subtypes as distinct",
    ),
    AccumulatorTestCase(
        "edge_regex_different_flags",
        docs=[{"v": Regex("abc", "i")}, {"v": Regex("abc", "m")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Regex("abc", "i"), Regex("abc", "m")]}],
        msg="$addToSet should treat Regex values with different flags as distinct",
    ),
    AccumulatorTestCase(
        "edge_expression_mixed_types",
        docs=[{"v": 1}, {"v": "hello"}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, "hello", True]}],
        msg="$addToSet should collect mixed-type values from expression",
    ),
]

# Property [Expression Error Propagation]: errors from sub-expressions propagate.
ADDTOSET_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid",
        docs=[{"v": "not_a_number"}],
        pipeline=[{"$group": {"_id": None, "result": {"$addToSet": {"$toInt": "$v"}}}}],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$addToSet should propagate $toInt conversion error",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$addToSet": {"$divide": ["$v", 0]}}}}],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$addToSet should propagate divide-by-zero error",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$addToSet": {"$mod": ["$v", 0]}}}}],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$addToSet should propagate mod-by-zero error",
    ),
]

# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------

ADDTOSET_SUCCESS_TESTS = (
    ADDTOSET_NULL_TESTS
    + ADDTOSET_MISSING_TESTS
    + ADDTOSET_NULL_MISSING_COMBINED_TESTS
    + ADDTOSET_REMOVE_TESTS
    + ADDTOSET_UNIQUE_TESTS
    + ADDTOSET_ARRAY_ELEMENT_TESTS
    + ADDTOSET_DOC_DEDUP_TESTS
    + ADDTOSET_STRING_DEDUP_TESTS
    + ADDTOSET_BSON_TYPE_TESTS
    + ADDTOSET_MIXED_TYPE_TESTS
    + ADDTOSET_NUMERIC_EQUIV_TESTS
    + ADDTOSET_TYPE_DISTINCTION_TESTS
    + ADDTOSET_NAN_TESTS
    + ADDTOSET_INFINITY_TESTS
    + ADDTOSET_NEG_ZERO_TESTS
    + ADDTOSET_DECIMAL128_PRECISION_TESTS
    + ADDTOSET_EXPRESSION_TESTS
    + ADDTOSET_GROUPING_TESTS
    + ADDTOSET_EMPTY_TESTS
    + ADDTOSET_EDGE_CASE_TESTS
)

ADDTOSET_ERROR_TESTS = ADDTOSET_EXPRESSION_ERROR_TESTS

# ---------------------------------------------------------------------------
# Primary test functions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_SUCCESS_TESTS))
def test_accumulator_addToSet(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator success cases with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_ERROR_TESTS))
def test_accumulator_addToSet_errors(collection, test_case):
    """Test $addToSet accumulator error cases with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


# ---------------------------------------------------------------------------
# Property-specific tests
# ---------------------------------------------------------------------------

# Property [Return Type]: $addToSet always returns an array type.
ADDTOSET_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_numeric",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": [1, 2], "type": "array"}],
        msg="$addToSet should return array type for numeric inputs",
    ),
    AccumulatorTestCase(
        "return_type_string",
        docs=[{"v": "a"}, {"v": "b"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": ["a", "b"], "type": "array"}],
        msg="$addToSet should return array type for string inputs",
    ),
    AccumulatorTestCase(
        "return_type_null_only",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": [None], "type": "array"}],
        msg="$addToSet should return array type for null-only inputs",
    ),
    AccumulatorTestCase(
        "return_type_missing_only",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": [], "type": "array"}],
        msg="$addToSet should return array type for all-missing inputs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_RETURN_TYPE_TESTS))
def test_accumulator_addToSet_return_type(collection, test_case: AccumulatorTestCase):
    """Test $addToSet return type verification."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["value"])
