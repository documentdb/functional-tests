"""Tests for $addToSet duplicate detection with complex values.

Covers: document comparison (field order matters), array value behavior,
empty/special documents, regex/binary/timestamp duplicate detection,
null/missing field handling.
"""

import pytest
from bson import Binary, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCUMENT_DUP_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "doc_exact_match_is_dup",
        setup_docs=[{"_id": 1, "arr": [{"a": 1, "b": 2}]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"a": 1, "b": 2}}},
        expected={"_id": 1, "arr": [{"a": 1, "b": 2}]},
        msg="Document with same fields and order should be duplicate",
    ),
    UpdateTestCase(
        "doc_different_order_not_dup",
        setup_docs=[{"_id": 1, "arr": [{"a": 1, "b": 2}]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"b": 2, "a": 1}}},
        expected={"_id": 1, "arr": [{"a": 1, "b": 2}, {"b": 2, "a": 1}]},
        msg="Document with different field order should not be duplicate",
    ),
    UpdateTestCase(
        "doc_new_value_added",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"y": 2}}},
        expected={"_id": 1, "arr": [{"x": 1}, {"y": 2}]},
        msg="Document not present should be added",
    ),
    UpdateTestCase(
        "nested_doc_exact_match",
        setup_docs=[{"_id": 1, "arr": [{"a": {"b": 1, "c": 2}}]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"a": {"b": 1, "c": 2}}}},
        expected={"_id": 1, "arr": [{"a": {"b": 1, "c": 2}}]},
        msg="Nested document with exact match should be duplicate",
    ),
    UpdateTestCase(
        "nested_doc_inner_different_order_not_dup",
        setup_docs=[{"_id": 1, "arr": [{"outer": {"a": 1, "b": 2}}]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"outer": {"b": 2, "a": 1}}}},
        expected={"_id": 1, "arr": [{"outer": {"a": 1, "b": 2}}, {"outer": {"b": 2, "a": 1}}]},
        msg="Nested doc with different inner field order should not be duplicate",
    ),
    UpdateTestCase(
        "empty_doc_duplicate",
        setup_docs=[{"_id": 1, "arr": [{}]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {}}},
        expected={"_id": 1, "arr": [{}]},
        msg="Empty document added twice should be detected as duplicate",
    ),
]
ARRAY_VALUE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "array_added_as_element",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": [1, 2, 3]}},
        expected={"_id": 1, "arr": [1, 2, [1, 2, 3]]},
        msg="Array value should be added as single element",
    ),
    UpdateTestCase(
        "array_dup_exact_match",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": [1, 2, 3]}},
        expected={"_id": 1, "arr": [[1, 2, 3]]},
        msg="Array already present should be duplicate",
    ),
    UpdateTestCase(
        "array_different_order_not_dup",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": [3, 2, 1]}},
        expected={"_id": 1, "arr": [[1, 2, 3], [3, 2, 1]]},
        msg="Array with different order should not be duplicate",
    ),
    UpdateTestCase(
        "array_vs_individual_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": [1, 2, 3]}},
        expected={"_id": 1, "arr": [1, 2, 3, [1, 2, 3]]},
        msg="Array value is not same as individual elements in array",
    ),
    UpdateTestCase(
        "existing_dups_not_removed",
        setup_docs=[{"_id": 1, "arr": [1, 1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 3}},
        expected={"_id": 1, "arr": [1, 1, 2, 3]},
        msg="Should not remove existing duplicates, only prevent new ones",
    ),
]
SPECIAL_VALUE_DUP_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "regex_same_flags_dup",
        setup_docs=[{"_id": 1, "arr": [Regex("^abc", "i")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Regex("^abc", "i")}},
        expected={"_id": 1, "arr": [Regex("^abc", "i")]},
        msg="Regex with same pattern and flags should be duplicate",
    ),
    UpdateTestCase(
        "regex_different_flags_not_dup",
        setup_docs=[{"_id": 1, "arr": [Regex("^abc", "i")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Regex("^abc", "")}},
        expected={"_id": 1, "arr": [Regex("^abc", "i"), Regex("^abc", "")]},
        msg="Regex with different flags should not be duplicate",
    ),
    UpdateTestCase(
        "objectid_dup",
        setup_docs=[{"_id": 1, "arr": [ObjectId("507f1f77bcf86cd799439011")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": ObjectId("507f1f77bcf86cd799439011")}},
        expected={"_id": 1, "arr": [ObjectId("507f1f77bcf86cd799439011")]},
        msg="Same ObjectId should be duplicate",
    ),
    UpdateTestCase(
        "timestamp_dup",
        setup_docs=[{"_id": 1, "arr": [Timestamp(1, 1)]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Timestamp(1, 1)}},
        expected={"_id": 1, "arr": [Timestamp(1, 1)]},
        msg="Same Timestamp should be duplicate",
    ),
    UpdateTestCase(
        "empty_doc_as_value",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {}}},
        expected={"_id": 1, "arr": [1, {}]},
        msg="Empty document should be addable as value",
    ),
    UpdateTestCase(
        "deeply_nested_doc",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"a": {"b": {"c": {"d": {"e": 1}}}}}}},
        expected={"_id": 1, "arr": [{"a": {"b": {"c": {"d": {"e": 1}}}}}]},
        msg="Deeply nested document should be addable",
    ),
    UpdateTestCase(
        "binary_same_bytes_different_subtype",
        setup_docs=[{"_id": 1, "arr": [Binary(b"\x01\x02\x03\x04", 0)]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Binary(b"\x01\x02\x03\x04", 2)}},
        expected={"_id": 1, "arr": [b"\x01\x02\x03\x04", Binary(b"\x01\x02\x03\x04", 2)]},
        msg="BinData with same bytes but different subtype should not be duplicate",
    ),
    UpdateTestCase(
        "doc_with_dollar_prefix_field",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$x": 1}}},
        expected={"_id": 1, "arr": [{"$x": 1}]},
        msg="Document with dollar-prefixed field name as value should be addable",
    ),
    UpdateTestCase(
        "doc_with_dot_notation_field",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"a.b": 1}}},
        expected={"_id": 1, "arr": [{"a.b": 1}]},
        msg="Document with dot-notation field name as value should be addable",
    ),
    UpdateTestCase(
        "dollar_prefix_without_each_is_value",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$sort": 1}}},
        expected={"_id": 1, "arr": [1, {"$sort": 1}]},
        msg="$-prefixed doc without $each should be treated as plain value, not modifier",
    ),
]

NULL_MISSING_SUCCESS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "add_null_to_array",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": None}},
        expected={"_id": 1, "arr": [1, 2, None]},
        msg="Should add null to array not containing null",
    ),
    UpdateTestCase(
        "null_duplicate",
        setup_docs=[{"_id": 1, "arr": [None, 1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": None}},
        expected={"_id": 1, "arr": [None, 1]},
        msg="Should not add duplicate null",
    ),
    UpdateTestCase(
        "missing_field_creates_array",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 5}},
        expected={"_id": 1, "arr": [5]},
        msg="Should create array field with value when field is missing",
    ),
    UpdateTestCase(
        "string_with_embedded_null_char",
        setup_docs=[{"_id": 1, "arr": ["ab\x00c"]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": "ab\x00c"}},
        expected={"_id": 1, "arr": ["ab\x00c"]},
        msg="String with embedded null character should be detected as duplicate",
    ),
]


ALL_TESTS = (
    DOCUMENT_DUP_TESTS + ARRAY_VALUE_TESTS + SPECIAL_VALUE_DUP_TESTS + NULL_MISSING_SUCCESS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_addToSet_duplicate_detection(collection, test: UpdateTestCase):
    """Test $addToSet duplicate detection and null/missing field handling."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
