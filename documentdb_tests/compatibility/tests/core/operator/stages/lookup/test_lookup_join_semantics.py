"""Tests for $lookup join semantics."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Left Outer Join Semantics]: every input document appears in
# the output regardless of whether any foreign documents match.
LOOKUP_LEFT_OUTER_JOIN_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "no_match_produces_empty_array",
        docs=[{"_id": 1, "lf": "x"}],
        foreign_docs=[{"_id": 10, "ff": "y"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "x", "joined": []}],
        msg="$lookup should produce an empty array when no foreign documents match",
    ),
    LookupTestCase(
        "single_match_produces_one_element_array",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}, {"_id": 11, "ff": "b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "a", "joined": [{"_id": 10, "ff": "a"}]},
        ],
        msg="$lookup should produce a single-element array when one foreign document matches",
    ),
    LookupTestCase(
        "multiple_matches_in_insertion_order",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[
            {"_id": 12, "ff": "a"},
            {"_id": 10, "ff": "a"},
            {"_id": 11, "ff": "a"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [
                    {"_id": 12, "ff": "a"},
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": "a"},
                ],
            },
        ],
        msg="$lookup should return all matching foreign documents in insertion order",
    ),
    LookupTestCase(
        "all_input_docs_preserved",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "b"},
            {"_id": 3, "lf": "c"},
        ],
        foreign_docs=[{"_id": 10, "ff": "b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "a", "joined": []},
            {"_id": 2, "lf": "b", "joined": [{"_id": 10, "ff": "b"}]},
            {"_id": 3, "lf": "c", "joined": []},
        ],
        msg=(
            "$lookup should preserve every input document in the output"
            " regardless of whether any foreign documents match"
        ),
    ),
    LookupTestCase(
        "matched_foreign_docs_all_fields_preserved",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[
            {"_id": 10, "ff": "a", "x": 1, "y": "hello", "z": [1, 2]},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [
                    {"_id": 10, "ff": "a", "x": 1, "y": "hello", "z": [1, 2]},
                ],
            },
        ],
        msg=(
            "$lookup should return matched foreign documents as complete"
            " documents with all fields preserved"
        ),
    ),
]

# Property [Null and Missing Field Matching]: missing fields and explicit null
# values in localField and foreignField are treated as null for matching
# purposes, so they match each other.
LOOKUP_NULL_MISSING_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "missing_local_matches_null_and_missing_foreign",
        docs=[{"_id": 1}, {"_id": 2, "lf": "x"}],
        foreign_docs=[
            {"_id": 10, "ff": None},
            {"_id": 11},
            {"_id": 12, "ff": "x"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [
                    {"_id": 10, "ff": None},
                    {"_id": 11},
                ],
            },
            {
                "_id": 2,
                "lf": "x",
                "joined": [{"_id": 12, "ff": "x"}],
            },
        ],
        msg=(
            "$lookup should treat missing localField as null and match foreign"
            " documents where foreignField is null or missing"
        ),
    ),
    LookupTestCase(
        "missing_foreign_matches_null_and_missing_local",
        docs=[
            {"_id": 1, "lf": None},
            {"_id": 2},
            {"_id": 3, "lf": "x"},
        ],
        foreign_docs=[
            {"_id": 10},
            {"_id": 11, "ff": "x"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": None, "joined": [{"_id": 10}]},
            {"_id": 2, "joined": [{"_id": 10}]},
            {"_id": 3, "lf": "x", "joined": [{"_id": 11, "ff": "x"}]},
        ],
        msg=(
            "$lookup should treat missing foreignField as null and match local"
            " documents where localField is null or missing"
        ),
    ),
    LookupTestCase(
        "explicit_null_local_matches_null_and_missing_foreign",
        docs=[{"_id": 1, "lf": None}],
        foreign_docs=[
            {"_id": 10, "ff": None},
            {"_id": 11},
            {"_id": 12, "ff": "x"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": None,
                "joined": [
                    {"_id": 10, "ff": None},
                    {"_id": 11},
                ],
            },
        ],
        msg=(
            "$lookup should match explicit null localField against foreign"
            " documents where foreignField is null or missing"
        ),
    ),
    LookupTestCase(
        "explicit_null_foreign_matches_null_and_missing_local",
        docs=[
            {"_id": 1, "lf": None},
            {"_id": 2},
            {"_id": 3, "lf": "x"},
        ],
        foreign_docs=[
            {"_id": 10, "ff": None},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": None, "joined": [{"_id": 10, "ff": None}]},
            {"_id": 2, "joined": [{"_id": 10, "ff": None}]},
            {"_id": 3, "lf": "x", "joined": []},
        ],
        msg=(
            "$lookup should match explicit null foreignField against local"
            " documents where localField is null or missing"
        ),
    ),
    LookupTestCase(
        "both_missing_match_each_other",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "joined": [{"_id": 10}]},
        ],
        msg=(
            "$lookup should match documents when both localField and"
            " foreignField are missing (both treated as null)"
        ),
    ),
]

# Property [Empty and Non-Existent Foreign Collections]: when the foreign
# collection does not exist or is empty, every input document gets an empty
# joined array.
LOOKUP_EMPTY_NONEXISTENT_FOREIGN_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "nonexistent_foreign_collection",
        docs=[{"_id": 1, "lf": "a"}, {"_id": 2, "lf": "b"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "a", "joined": []},
            {"_id": 2, "lf": "b", "joined": []},
        ],
        msg=(
            "$lookup should produce an empty joined array for every"
            " input document when the foreign collection does not exist"
        ),
    ),
    LookupTestCase(
        "empty_foreign_collection",
        docs=[{"_id": 1, "lf": "a"}, {"_id": 2, "lf": "b"}],
        foreign_docs=[],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "a", "joined": []},
            {"_id": 2, "lf": "b", "joined": []},
        ],
        msg=(
            "$lookup should produce an empty joined array for every"
            " input document when the foreign collection is empty"
        ),
    ),
]

# Property [Empty and Non-Existent Local Collections]: when the local
# collection does not exist or is empty, the aggregate produces no output
# documents.
LOOKUP_EMPTY_NONEXISTENT_LOCAL_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "nonexistent_local_collection",
        docs=None,
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[],
        msg="$lookup should produce no output when the local collection does not exist",
    ),
    LookupTestCase(
        "empty_local_collection",
        docs=[],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[],
        msg="$lookup should produce no output when the local collection is empty",
    ),
]

# Property [BSON Type Preservation]: all BSON types in foreign documents
# are preserved unchanged through the join, with the joined array
# containing exact copies.
LOOKUP_BSON_TYPE_PRESERVATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "all_bson_types_preserved_through_join",
        docs=[{"_id": 1, "lf": "match"}],
        foreign_docs=[
            {
                "_id": 10,
                "ff": "match",
                "double_val": 3.14,
                "string_val": "hello",
                "doc_val": {"nested": "doc"},
                "array_val": [1, "two", 3],
                "binary_val": Binary(b"\x00\x01\x02", 0),
                "binary_uuid_val": Binary(b"\x01" * 16, 4),
                "oid_val": ObjectId("507f1f77bcf86cd799439011"),
                "bool_val": True,
                "datetime_val": datetime.datetime(2024, 6, 15, 12, 0, 0),
                "null_val": None,
                "regex_val": Regex("^abc", "i"),
                "code_val": Code("function() {}"),
                "code_scope_val": Code("function() {}", {"x": 1}),
                "int32_val": 42,
                "int64_val": Int64(2**40),
                "timestamp_val": Timestamp(1000, 1),
                "decimal128_val": Decimal128("123.456"),
                "minkey_val": MinKey(),
                "maxkey_val": MaxKey(),
            },
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "match",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "match",
                        "double_val": 3.14,
                        "string_val": "hello",
                        "doc_val": {"nested": "doc"},
                        "array_val": [1, "two", 3],
                        "binary_val": b"\x00\x01\x02",
                        "binary_uuid_val": Binary(b"\x01" * 16, 4),
                        "oid_val": ObjectId("507f1f77bcf86cd799439011"),
                        "bool_val": True,
                        "datetime_val": datetime.datetime(2024, 6, 15, 12, 0, 0),
                        "null_val": None,
                        "regex_val": Regex("^abc", 2),
                        "code_val": Code("function() {}"),
                        "code_scope_val": Code("function() {}", {"x": 1}),
                        "int32_val": 42,
                        "int64_val": Int64(2**40),
                        "timestamp_val": Timestamp(1000, 1),
                        "decimal128_val": Decimal128("123.456"),
                        "minkey_val": MinKey(),
                        "maxkey_val": MaxKey(),
                    },
                ],
            },
        ],
        msg=(
            "$lookup should preserve all BSON types in foreign documents"
            " unchanged through the join"
        ),
    ),
]

# Property [Multiple Lookups]: multiple $lookup stages in the same pipeline
# each produce independent joined arrays.
LOOKUP_MULTIPLE_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "multiple_lookups_in_sequence",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j1",
                }
            },
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "j2",
                }
            },
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "j1": [{"_id": 10, "ff": "a"}],
                "j2": [{"_id": 10, "ff": "a"}],
            },
        ],
        msg="multiple $lookup stages should each produce independent joined arrays",
    ),
]

LOOKUP_JOIN_SEMANTICS_TESTS: list[LookupTestCase] = (
    LOOKUP_LEFT_OUTER_JOIN_TESTS
    + LOOKUP_NULL_MISSING_TESTS
    + LOOKUP_EMPTY_NONEXISTENT_FOREIGN_TESTS
    + LOOKUP_EMPTY_NONEXISTENT_LOCAL_TESTS
    + LOOKUP_BSON_TYPE_PRESERVATION_TESTS
    + LOOKUP_MULTIPLE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_JOIN_SEMANTICS_TESTS))
def test_lookup_join_semantics(collection, test_case: LookupTestCase):
    """Test $lookup join semantics."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
