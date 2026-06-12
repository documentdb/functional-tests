"""Tests for $mergeObjects accumulator: core merge behavior and BSON type preservation."""

from __future__ import annotations

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

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Disjoint Keys]: documents with non-overlapping keys produce a
# merged result containing all keys.
MERGE_OBJECTS_DISJOINT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "disjoint_two_docs",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"b": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should merge two documents with disjoint keys",
    ),
    AccumulatorTestCase(
        "disjoint_three_docs",
        docs=[
            {"s": 1, "v": {"a": 1}},
            {"s": 2, "v": {"b": 2}},
            {"s": 3, "v": {"c": 3}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2, "c": 3}}],
        msg="$mergeObjects should merge three documents with disjoint keys",
    ),
    AccumulatorTestCase(
        "disjoint_multi_field_docs",
        docs=[{"s": 1, "v": {"a": 1, "b": 2}}, {"s": 2, "v": {"c": 3, "d": 4}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2, "c": 3, "d": 4}}],
        msg="$mergeObjects should merge multi-field documents with disjoint keys",
    ),
]

# Property [Overlapping Keys - Last Wins]: when documents share keys, the
# value from the last document in sort order wins.
MERGE_OBJECTS_OVERLAP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "overlap_simple",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"a": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 2}}],
        msg="$mergeObjects should use last value when key overlaps",
    ),
    AccumulatorTestCase(
        "overlap_triple",
        docs=[
            {"s": 1, "v": {"a": 1}},
            {"s": 2, "v": {"a": 2}},
            {"s": 3, "v": {"a": 3}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 3}}],
        msg="$mergeObjects should use last value from three documents with same key",
    ),
    AccumulatorTestCase(
        "overlap_partial",
        docs=[{"s": 1, "v": {"a": 1, "b": 2}}, {"s": 2, "v": {"b": 3, "c": 4}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 3, "c": 4}}],
        msg="$mergeObjects should keep non-overlapping keys and overwrite overlapping ones",
    ),
    AccumulatorTestCase(
        "overlap_type_change",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"a": "hello"}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": "hello"}}],
        msg="$mergeObjects should allow type change on overwrite",
    ),
    AccumulatorTestCase(
        "overlap_null_overwrites_value",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"a": None}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": None}}],
        msg="$mergeObjects should allow null to overwrite an existing value",
    ),
    AccumulatorTestCase(
        "overlap_value_overwrites_null",
        docs=[{"s": 1, "v": {"a": None}}, {"s": 2, "v": {"a": 1}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should allow a value to overwrite null",
    ),
]

# Property [Shallow Merge]: $mergeObjects performs a shallow merge; nested
# documents are replaced entirely, not recursively merged.
MERGE_OBJECTS_SHALLOW_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "shallow_nested_replaced",
        docs=[
            {"s": 1, "v": {"a": {"x": 1, "y": 2}}},
            {"s": 2, "v": {"a": {"y": 3, "z": 4}}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": {"y": 3, "z": 4}}}],
        msg="$mergeObjects should replace nested document entirely, not deep merge",
    ),
    AccumulatorTestCase(
        "shallow_array_replaced",
        docs=[{"s": 1, "v": {"a": [1, 2, 3]}}, {"s": 2, "v": {"a": [4, 5]}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": [4, 5]}}],
        msg="$mergeObjects should replace array entirely, not concatenate",
    ),
    AccumulatorTestCase(
        "shallow_nested_to_scalar",
        docs=[{"s": 1, "v": {"a": {"b": {"c": 1}}}}, {"s": 2, "v": {"a": 42}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 42}}],
        msg="$mergeObjects should replace deeply nested document with scalar",
    ),
    AccumulatorTestCase(
        "shallow_scalar_to_nested",
        docs=[{"s": 1, "v": {"a": 42}}, {"s": 2, "v": {"a": {"b": {"c": 1}}}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": {"b": {"c": 1}}}}],
        msg="$mergeObjects should replace scalar with deeply nested document",
    ),
]

# Property [Empty Documents]: empty documents contribute no fields and do not
# affect the merged result.
MERGE_OBJECTS_EMPTY_DOC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_all",
        docs=[{"s": 1, "v": {}}, {"s": 2, "v": {}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document when all values are empty documents",
    ),
    AccumulatorTestCase(
        "empty_with_nonempty",
        docs=[{"s": 1, "v": {}}, {"s": 2, "v": {"a": 1}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should ignore empty documents and merge non-empty ones",
    ),
    AccumulatorTestCase(
        "empty_interspersed",
        docs=[
            {"s": 1, "v": {"a": 1}},
            {"s": 2, "v": {}},
            {"s": 3, "v": {"b": 2}},
            {"s": 4, "v": {}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should ignore interspersed empty documents",
    ),
]

# Property [BSON Type Preservation]: $mergeObjects preserves the BSON type of
# field values from the merged documents.
MERGE_OBJECTS_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_int32_int64",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"b": Int64(2)}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": Int64(2)}}],
        msg="$mergeObjects should preserve int32 and Int64 types",
    ),
    AccumulatorTestCase(
        "bson_double_decimal128",
        docs=[{"s": 1, "v": {"a": 3.14}}, {"s": 2, "v": {"b": Decimal128("2.718")}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 3.14, "b": Decimal128("2.718")}}],
        msg="$mergeObjects should preserve double and Decimal128 types",
    ),
    AccumulatorTestCase(
        "bson_string_bool",
        docs=[{"s": 1, "v": {"a": "hello"}}, {"s": 2, "v": {"b": True}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": "hello", "b": True}}],
        msg="$mergeObjects should preserve string and bool types",
    ),
    AccumulatorTestCase(
        "bson_date_objectid",
        docs=[
            {"s": 1, "v": {"a": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
            {"s": 2, "v": {"b": ObjectId("000000000000000000000000")}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": {
                    "a": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "b": ObjectId("000000000000000000000000"),
                },
            }
        ],
        msg="$mergeObjects should preserve datetime and ObjectId types",
    ),
    AccumulatorTestCase(
        "bson_binary_regex",
        docs=[
            {"s": 1, "v": {"a": Binary(b"\x01\x02")}},
            {"s": 2, "v": {"b": Regex("abc", "i")}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": b"\x01\x02", "b": Regex("abc", "i")}}],
        msg="$mergeObjects should preserve Binary and Regex types",
    ),
    AccumulatorTestCase(
        "bson_timestamp_code",
        docs=[
            {"s": 1, "v": {"a": Timestamp(1, 1)}},
            {"s": 2, "v": {"b": Code("function(){}")}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": Timestamp(1, 1), "b": Code("function(){}")}}],
        msg="$mergeObjects should preserve Timestamp and Code types",
    ),
    AccumulatorTestCase(
        "bson_minkey_maxkey",
        docs=[{"s": 1, "v": {"a": MinKey()}}, {"s": 2, "v": {"b": MaxKey()}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": MinKey(), "b": MaxKey()}}],
        msg="$mergeObjects should preserve MinKey and MaxKey types",
    ),
    AccumulatorTestCase(
        "bson_array_nested",
        docs=[
            {"s": 1, "v": {"a": [1, 2, 3]}},
            {"s": 2, "v": {"b": {"nested": {"deep": True}}}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": [1, 2, 3], "b": {"nested": {"deep": True}}}}],
        msg="$mergeObjects should preserve array and nested document types",
    ),
]

# Property [Nested Structure Preservation]: $mergeObjects preserves deeply
# nested arrays-of-objects with embedded arrays without flattening or
# truncation, and correctly resolves array traversal via field paths.
MERGE_OBJECTS_NESTED_STRUCTURE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nested_arrays_of_objects_with_embedded_arrays",
        docs=[
            {
                "s": 1,
                "v": {
                    "data": {
                        "users": [
                            {"profile": {"name": "Alice", "scores": [85, 90]}},
                            {"profile": {"name": "Bob", "scores": [70, 80]}},
                        ]
                    }
                },
            },
            {"s": 2, "v": {"metadata": {"tags": [["a", "b"], ["c"]]}}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": {
                    "data": {
                        "users": [
                            {"profile": {"name": "Alice", "scores": [85, 90]}},
                            {"profile": {"name": "Bob", "scores": [70, 80]}},
                        ]
                    },
                    "metadata": {"tags": [["a", "b"], ["c"]]},
                },
            }
        ],
        msg="$mergeObjects should preserve deeply nested arrays-of-objects with embedded arrays",
    ),
    AccumulatorTestCase(
        "nested_mixed_depth_structures",
        docs=[
            {"s": 1, "v": {"a": {"arr": [{"nested": [1, 2]}, {"nested": [3]}]}}},
            {"s": 2, "v": {"b": [{"obj": {"key": "val"}}, [1, 2, 3]]}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": {
                    "a": {"arr": [{"nested": [1, 2]}, {"nested": [3]}]},
                    "b": [{"obj": {"key": "val"}}, [1, 2, 3]],
                },
            }
        ],
        msg="$mergeObjects should preserve mixed-depth nested structures with arrays and objects",
    ),
]

# Property [Grouped Merge]: $mergeObjects correctly merges documents per group
# when grouping by a key.
MERGE_OBJECTS_GROUPED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "grouped_by_category",
        docs=[
            {"cat": "A", "v": {"x": 1}},
            {"cat": "A", "v": {"y": 2}},
            {"cat": "B", "v": {"x": 10}},
            {"cat": "B", "v": {"y": 20}},
        ],
        pipeline=[
            {"$sort": {"cat": 1}},
            {"$group": {"_id": "$cat", "result": {"$mergeObjects": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": {"x": 1, "y": 2}},
            {"_id": "B", "result": {"x": 10, "y": 20}},
        ],
        msg="$mergeObjects should merge documents independently per group",
    ),
    AccumulatorTestCase(
        "grouped_with_overlap",
        docs=[
            {"s": 1, "cat": "A", "v": {"x": 1}},
            {"s": 2, "cat": "A", "v": {"x": 2, "y": 3}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": "$cat", "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": "A", "result": {"x": 2, "y": 3}}],
        msg="$mergeObjects should apply last-wins within a group",
    ),
    AccumulatorTestCase(
        "grouped_compound_id",
        docs=[
            {"r": "us", "d": "sales", "v": {"x": 1}},
            {"r": "us", "d": "sales", "v": {"y": 2}},
            {"r": "us", "d": "eng", "v": {"x": 10}},
            {"r": "eu", "d": "sales", "v": {"z": 99}},
        ],
        pipeline=[
            {"$sort": {"r": 1, "d": 1}},
            {
                "$group": {
                    "_id": {"r": "$r", "d": "$d"},
                    "result": {"$mergeObjects": "$v"},
                }
            },
            {"$sort": {"_id.r": 1, "_id.d": 1}},
        ],
        expected=[
            {"_id": {"r": "eu", "d": "sales"}, "result": {"z": 99}},
            {"_id": {"r": "us", "d": "eng"}, "result": {"x": 10}},
            {"_id": {"r": "us", "d": "sales"}, "result": {"x": 1, "y": 2}},
        ],
        msg="$mergeObjects should merge documents independently per compound group key",
    ),
]

MERGE_OBJECTS_CORE_TESTS = (
    MERGE_OBJECTS_DISJOINT_TESTS
    + MERGE_OBJECTS_OVERLAP_TESTS
    + MERGE_OBJECTS_SHALLOW_TESTS
    + MERGE_OBJECTS_EMPTY_DOC_TESTS
    + MERGE_OBJECTS_BSON_TYPE_TESTS
    + MERGE_OBJECTS_NESTED_STRUCTURE_TESTS
    + MERGE_OBJECTS_GROUPED_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MERGE_OBJECTS_CORE_TESTS))
def test_accumulator_mergeObjects_core(collection, test_case: AccumulatorTestCase):
    """Test $mergeObjects core merge behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
    actual_docs = result["cursor"]["firstBatch"]
    for actual, exp in zip(actual_docs, test_case.expected):
        if "result" in exp and isinstance(exp["result"], dict):
            actual_keys = list(actual["result"].keys())
            expected_keys = list(exp["result"].keys())
            if actual_keys != expected_keys:
                raise AssertionError(
                    f"[KEY_ORDER_MISMATCH] {test_case.msg}\n"
                    f"Expected key order: {expected_keys}\n"
                    f"Actual key order:   {actual_keys}"
                )
