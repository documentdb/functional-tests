"""Tests for $mergeObjects accumulator: edge cases and special field names."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Single Document]: a single-document group returns the document
# as-is without modification.
MERGE_OBJECTS_SINGLE_DOC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "single_doc_passthrough",
        docs=[{"v": {"a": 1, "b": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should return the document unchanged for a single-document group",
    ),
    AccumulatorTestCase(
        "single_doc_empty",
        docs=[{"v": {}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document for a single empty document",
    ),
    AccumulatorTestCase(
        "single_doc_nested",
        docs=[{"v": {"a": {"b": {"c": 1}}}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"a": {"b": {"c": 1}}}}],
        msg="$mergeObjects should preserve nested structure in single-document group",
    ),
]

# Property [Many Documents]: $mergeObjects correctly merges many documents in
# a group.
MERGE_OBJECTS_MANY_DOCS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "many_docs_disjoint",
        docs=[{"v": {f"k{i}": i}} for i in range(20)],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {f"k{i}": i for i in range(20)}}],
        msg="$mergeObjects should correctly merge 20 documents with disjoint keys",
    ),
    AccumulatorTestCase(
        "many_docs_same_key",
        docs=[{"v": {"a": i}} for i in range(10)],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"a": 9}}],
        msg="$mergeObjects should use last value when many documents share the same key",
    ),
]

# Property [Large Documents]: $mergeObjects handles documents with many fields.
MERGE_OBJECTS_LARGE_DOC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "large_doc_many_fields",
        docs=[{"v": {f"field_{i}": i for i in range(50)}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {f"field_{i}": i for i in range(50)}}],
        msg="$mergeObjects should handle documents with 50 fields",
    ),
]

# Property [Special Field Names]: $mergeObjects correctly handles special
# field names including unicode, dollar-prefixed, dotted, empty string, and
# numeric string keys.
MERGE_OBJECTS_SPECIAL_FIELD_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_unicode_keys",
        docs=[{"v": {"\u65e5\u672c\u8a9e": 1}}, {"v": {"\u4e2d\u6587": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"\u65e5\u672c\u8a9e": 1, "\u4e2d\u6587": 2}}],
        msg="$mergeObjects should preserve Unicode field names",
    ),
    AccumulatorTestCase(
        "special_dollar_prefix",
        docs=[{"v": {"$a": 1}}, {"v": {"$b": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"$a": 1, "$b": 2}}],
        msg="$mergeObjects should preserve dollar-prefixed field names",
    ),
    AccumulatorTestCase(
        "special_dotted_keys",
        docs=[{"v": {"a.b": 1}}, {"v": {"c.d": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"a.b": 1, "c.d": 2}}],
        msg="$mergeObjects should preserve dotted field names as literal keys",
    ),
    AccumulatorTestCase(
        "special_empty_string_key",
        docs=[{"v": {"": 1}}, {"v": {"a": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"": 1, "a": 2}}],
        msg="$mergeObjects should preserve empty string field names",
    ),
    AccumulatorTestCase(
        "special_numeric_string_keys",
        docs=[{"v": {"0": "zero"}}, {"v": {"1": "one"}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"0": "zero", "1": "one"}}],
        msg="$mergeObjects should preserve numeric string field names",
    ),
    AccumulatorTestCase(
        "special_long_field_name",
        docs=[{"v": {"a" * 200: 1}}, {"v": {"b": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"a" * 200: 1, "b": 2}}],
        msg="$mergeObjects should preserve very long field names",
    ),
    AccumulatorTestCase(
        "special_dollar_overlap",
        docs=[{"v": {"$a": 1}}, {"v": {"$a": 99}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"$a": 99}}],
        msg="$mergeObjects should apply last-wins to dollar-prefixed overlapping keys",
    ),
]

# Property [_id Field Handling]: $mergeObjects treats _id as a normal field
# in the merged result.
MERGE_OBJECTS_ID_FIELD_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "id_field_merged",
        docs=[{"v": {"_id": 100, "a": 1}}, {"v": {"b": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"_id": 100, "a": 1, "b": 2}}],
        msg="$mergeObjects should include _id from merged documents as a normal field",
    ),
    AccumulatorTestCase(
        "id_field_overwritten",
        docs=[{"v": {"_id": 1, "a": 1}}, {"v": {"_id": 2, "b": 2}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"_id": 2, "a": 1, "b": 2}}],
        msg="$mergeObjects should overwrite _id with last value, like any other field",
    ),
]

# Property [Deeply Nested Structure]: $mergeObjects preserves deeply nested
# structures in the merged result.
MERGE_OBJECTS_DEEP_NESTING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "deep_nesting_preserved",
        docs=[
            {"v": {"a": {"b": {"c": {"d": {"e": 1}}}}}},
            {"v": {"f": 2}},
        ],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"a": {"b": {"c": {"d": {"e": 1}}}}, "f": 2}}],
        msg="$mergeObjects should preserve deeply nested document structure",
    ),
    AccumulatorTestCase(
        "deep_nesting_overwrite",
        docs=[
            {"v": {"a": {"b": {"c": 1}}}},
            {"v": {"a": {"x": 2}}},
        ],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {"a": {"x": 2}}}],
        msg="$mergeObjects should replace entire nested structure on overwrite",
    ),
]

MERGE_OBJECTS_EDGE_TESTS = (
    MERGE_OBJECTS_SINGLE_DOC_TESTS
    + MERGE_OBJECTS_MANY_DOCS_TESTS
    + MERGE_OBJECTS_LARGE_DOC_TESTS
    + MERGE_OBJECTS_SPECIAL_FIELD_TESTS
    + MERGE_OBJECTS_ID_FIELD_TESTS
    + MERGE_OBJECTS_DEEP_NESTING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MERGE_OBJECTS_EDGE_TESTS))
def test_accumulator_mergeObjects_edge_cases(collection, test_case: AccumulatorTestCase):
    """Test $mergeObjects edge cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
