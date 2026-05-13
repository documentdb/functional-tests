"""
Tests for $type query operator type matching.

Verifies that $type correctly matches documents by BSON type using numeric
type codes, string aliases, and the "number" meta-alias. Also verifies
numeric/string equivalence, that $type distinguishes between similar
BSON types, and null vs missing field behavior.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code
from bson.codec_options import CodecOptions

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TYPES_DOCS: list[dict] = [
    {"_id": 1, "x": 1.5},  # double
    {"_id": 2, "x": "hello"},  # string
    {"_id": 3, "x": {"a": 1}},  # object
    {"_id": 4, "x": [1, 2]},  # array
    {"_id": 5, "x": Binary(b"\x01\x02", 0)},  # binData
    {"_id": 6, "x": ObjectId()},  # objectId
    {"_id": 7, "x": True},  # bool
    {"_id": 8, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)},  # date
    {"_id": 9, "x": None},  # null
    {"_id": 10, "x": Regex("abc", "i")},  # regex
    {"_id": 11, "x": Code("function(){}")},  # javascript
    {"_id": 12, "x": 42},  # int
    {"_id": 13, "x": Timestamp(1234567890, 1)},  # timestamp
    {"_id": 14, "x": Int64(123456789012345)},  # long
    {"_id": 15, "x": Decimal128("1.23")},  # decimal
    {"_id": 16, "x": MinKey()},  # minKey
    {"_id": 17, "x": MaxKey()},  # maxKey
]

MIXED_DOCS: list[dict] = [
    {"_id": 1, "x": 1.5},  # double
    {"_id": 2, "x": 42},  # int32
    {"_id": 3, "x": Int64(123456789012345)},  # long
    {"_id": 4, "x": Decimal128("9.99")},  # decimal128
    {"_id": 5, "x": "hello"},  # string
    {"_id": 6, "x": True},  # bool
    {"_id": 7, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)},  # date
    {"_id": 8, "x": None},  # null
    {"_id": 9, "x": Timestamp(1234567890, 1)},  # timestamp
]

NUMERIC_CODE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_code_1_double",
        filter={"x": {"$type": 1}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[0]],
        msg="$type: 1 should match double fields",
    ),
    QueryTestCase(
        id="numeric_code_2_string",
        filter={"x": {"$type": 2}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[1]],
        msg="$type: 2 should match string fields",
    ),
    QueryTestCase(
        id="numeric_code_3_object",
        filter={"x": {"$type": 3}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[2]],
        msg="$type: 3 should match object fields",
    ),
    QueryTestCase(
        id="numeric_code_4_array",
        filter={"x": {"$type": 4}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[3]],
        msg="$type: 4 should match array fields",
    ),
    QueryTestCase(
        id="numeric_code_5_binData",
        filter={"x": {"$type": 5}},
        doc=ALL_TYPES_DOCS,
        expected=[{"_id": 5, "x": b"\x01\x02"}],
        msg="$type: 5 should match binData fields",
    ),
    QueryTestCase(
        id="numeric_code_7_objectId",
        filter={"x": {"$type": 7}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[5]],
        msg="$type: 7 should match objectId fields",
    ),
    QueryTestCase(
        id="numeric_code_8_bool",
        filter={"x": {"$type": 8}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[6]],
        msg="$type: 8 should match bool fields",
    ),
    QueryTestCase(
        id="numeric_code_9_date",
        filter={"x": {"$type": 9}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[7]],
        msg="$type: 9 should match date fields",
    ),
    QueryTestCase(
        id="numeric_code_10_null",
        filter={"x": {"$type": 10}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[8]],
        msg="$type: 10 should match null fields",
    ),
    QueryTestCase(
        id="numeric_code_11_regex",
        filter={"x": {"$type": 11}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[9]],
        msg="$type: 11 should match regex fields",
    ),
    QueryTestCase(
        id="numeric_code_13_javascript",
        filter={"x": {"$type": 13}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[10]],
        msg="$type: 13 should match javascript fields",
    ),
    QueryTestCase(
        id="numeric_code_16_int",
        filter={"x": {"$type": 16}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[3], ALL_TYPES_DOCS[11]],
        msg="$type: 16 should match int32 fields and arrays containing int32 elements",
    ),
    QueryTestCase(
        id="numeric_code_17_timestamp",
        filter={"x": {"$type": 17}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[12]],
        msg="$type: 17 should match timestamp fields",
    ),
    QueryTestCase(
        id="numeric_code_18_long",
        filter={"x": {"$type": 18}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[13]],
        msg="$type: 18 should match long fields",
    ),
    QueryTestCase(
        id="numeric_code_19_decimal",
        filter={"x": {"$type": 19}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[14]],
        msg="$type: 19 should match decimal128 fields",
    ),
    QueryTestCase(
        id="numeric_code_neg1_minKey",
        filter={"x": {"$type": -1}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[15]],
        msg="$type: -1 should match minKey fields",
    ),
    QueryTestCase(
        id="numeric_code_127_maxKey",
        filter={"x": {"$type": 127}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[16]],
        msg="$type: 127 should match maxKey fields",
    ),
]

STRING_ALIAS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_alias_double",
        filter={"x": {"$type": "double"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[0]],
        msg="$type: 'double' should match double fields",
    ),
    QueryTestCase(
        id="string_alias_string",
        filter={"x": {"$type": "string"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[1]],
        msg="$type: 'string' should match string fields",
    ),
    QueryTestCase(
        id="string_alias_object",
        filter={"x": {"$type": "object"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[2]],
        msg="$type: 'object' should match object fields",
    ),
    QueryTestCase(
        id="string_alias_array",
        filter={"x": {"$type": "array"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[3]],
        msg="$type: 'array' should match array fields",
    ),
    QueryTestCase(
        id="string_alias_binData",
        filter={"x": {"$type": "binData"}},
        doc=ALL_TYPES_DOCS,
        expected=[{"_id": 5, "x": b"\x01\x02"}],
        msg="$type: 'binData' should match binData fields",
    ),
    QueryTestCase(
        id="string_alias_objectId",
        filter={"x": {"$type": "objectId"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[5]],
        msg="$type: 'objectId' should match objectId fields",
    ),
    QueryTestCase(
        id="string_alias_bool",
        filter={"x": {"$type": "bool"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[6]],
        msg="$type: 'bool' should match bool fields",
    ),
    QueryTestCase(
        id="string_alias_date",
        filter={"x": {"$type": "date"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[7]],
        msg="$type: 'date' should match date fields",
    ),
    QueryTestCase(
        id="string_alias_null",
        filter={"x": {"$type": "null"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[8]],
        msg="$type: 'null' should match null fields",
    ),
    QueryTestCase(
        id="string_alias_regex",
        filter={"x": {"$type": "regex"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[9]],
        msg="$type: 'regex' should match regex fields",
    ),
    QueryTestCase(
        id="string_alias_javascript",
        filter={"x": {"$type": "javascript"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[10]],
        msg="$type: 'javascript' should match javascript fields",
    ),
    QueryTestCase(
        id="string_alias_int",
        filter={"x": {"$type": "int"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[3], ALL_TYPES_DOCS[11]],
        msg="$type: 'int' should match int32 fields and arrays containing int32 elements",
    ),
    QueryTestCase(
        id="string_alias_timestamp",
        filter={"x": {"$type": "timestamp"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[12]],
        msg="$type: 'timestamp' should match timestamp fields",
    ),
    QueryTestCase(
        id="string_alias_long",
        filter={"x": {"$type": "long"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[13]],
        msg="$type: 'long' should match long fields",
    ),
    QueryTestCase(
        id="string_alias_decimal",
        filter={"x": {"$type": "decimal"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[14]],
        msg="$type: 'decimal' should match decimal128 fields",
    ),
    QueryTestCase(
        id="string_alias_minKey",
        filter={"x": {"$type": "minKey"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[15]],
        msg="$type: 'minKey' should match minKey fields",
    ),
    QueryTestCase(
        id="string_alias_maxKey",
        filter={"x": {"$type": "maxKey"}},
        doc=ALL_TYPES_DOCS,
        expected=[ALL_TYPES_DOCS[16]],
        msg="$type: 'maxKey' should match maxKey fields",
    ),
]

MATCHING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="number_alias_matches_double",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": 1.5}],
        expected=[{"_id": 1, "x": 1.5}],
        msg="$type: 'number' should match double fields",
    ),
    QueryTestCase(
        id="number_alias_matches_int32",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": 42}],
        expected=[{"_id": 1, "x": 42}],
        msg="$type: 'number' should match int32 fields",
    ),
    QueryTestCase(
        id="number_alias_matches_int64",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": Int64(123)}],
        expected=[{"_id": 1, "x": Int64(123)}],
        msg="$type: 'number' should match int64 fields",
    ),
    QueryTestCase(
        id="number_alias_matches_decimal128",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": Decimal128("9.99")}],
        expected=[{"_id": 1, "x": Decimal128("9.99")}],
        msg="$type: 'number' should match decimal128 fields",
    ),
    QueryTestCase(
        id="number_alias_rejects_string",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": "hello"}],
        expected=[],
        msg="$type: 'number' should NOT match string fields",
    ),
    QueryTestCase(
        id="number_alias_rejects_bool",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": True}],
        expected=[],
        msg="$type: 'number' should NOT match boolean fields",
    ),
    QueryTestCase(
        id="number_alias_rejects_date",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected=[],
        msg="$type: 'number' should NOT match date fields",
    ),
    QueryTestCase(
        id="number_alias_rejects_null",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": None}],
        expected=[],
        msg="$type: 'number' should NOT match null fields",
    ),
    QueryTestCase(
        id="number_alias_rejects_timestamp",
        filter={"x": {"$type": "number"}},
        doc=[{"_id": 1, "x": Timestamp(1234567890, 1)}],
        expected=[],
        msg="$type: 'number' should NOT match timestamp fields",
    ),
    QueryTestCase(
        id="number_alias_mixed_collection",
        filter={"x": {"$type": "number"}},
        doc=MIXED_DOCS,
        expected=[MIXED_DOCS[0], MIXED_DOCS[1], MIXED_DOCS[2], MIXED_DOCS[3]],
        msg="$type: 'number' should match all numeric types in mixed collection",
    ),
    QueryTestCase(
        id="distinction_bool_not_match_int",
        filter={"x": {"$type": "bool"}},
        doc=[{"_id": 1, "x": 0}, {"_id": 2, "x": 1}, {"_id": 3, "x": True}],
        expected=[{"_id": 3, "x": True}],
        msg="$type: 'bool' should NOT match int 0 or int 1",
    ),
    QueryTestCase(
        id="distinction_int_not_match_bool",
        filter={"x": {"$type": "int"}},
        doc=[{"_id": 1, "x": False}, {"_id": 2, "x": True}, {"_id": 3, "x": 42}],
        expected=[{"_id": 3, "x": 42}],
        msg="$type: 'int' should NOT match boolean false or true",
    ),
    QueryTestCase(
        id="distinction_null_not_match_missing",
        filter={"x": {"$type": "null"}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "y": 1}],
        expected=[{"_id": 1, "x": None}],
        msg="$type: 'null' should NOT match missing fields",
    ),
    QueryTestCase(
        id="distinction_double_not_match_int32",
        filter={"x": {"$type": "double"}},
        doc=[{"_id": 1, "x": 1.0}, {"_id": 2, "x": 1}],
        expected=[{"_id": 1, "x": 1.0}],
        msg="$type: 'double' should NOT match int32 even if numerically equal",
    ),
    QueryTestCase(
        id="distinction_int_not_match_long",
        filter={"x": {"$type": "int"}},
        doc=[{"_id": 1, "x": 1}, {"_id": 2, "x": Int64(1)}],
        expected=[{"_id": 1, "x": 1}],
        msg="$type: 'int' should NOT match long even if numerically equal",
    ),
    QueryTestCase(
        id="distinction_string_not_match_null",
        filter={"x": {"$type": "string"}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "x": "hello"}],
        expected=[{"_id": 2, "x": "hello"}],
        msg="$type: 'string' should NOT match null",
    ),
    QueryTestCase(
        id="distinction_double_not_match_decimal128",
        filter={"x": {"$type": "double"}},
        doc=[{"_id": 1, "x": 1.5}, {"_id": 2, "x": Decimal128("1.5")}],
        expected=[{"_id": 1, "x": 1.5}],
        msg="$type: 'double' should NOT match decimal128 even if numerically equal",
    ),
    QueryTestCase(
        id="missing_field_no_match",
        filter={"x": {"$type": "string"}},
        doc=[{"_id": 1, "y": 1}],
        expected=[],
        msg="$type on missing field should return no match",
    ),
    QueryTestCase(
        id="not_type_on_missing_returns_all",
        filter={"x": {"$not": {"$type": "string"}}},
        doc=[{"_id": 1, "y": 1}, {"_id": 2, "x": 42}],
        expected=[{"_id": 1, "y": 1}, {"_id": 2, "x": 42}],
        msg="$not $type on missing field should return all non-matching docs",
    ),
    QueryTestCase(
        id="exists_true_with_type_null",
        filter={"x": {"$exists": True, "$type": "null"}},
        doc=[{"_id": 1, "x": None}, {"_id": 2, "y": 1}, {"_id": 3, "x": "hello"}],
        expected=[{"_id": 1, "x": None}],
        msg="$exists: true + $type: 'null' should match field that exists and is null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_CODE_TESTS))
def test_type_numeric_codes(collection, test):
    """Test $type matching with numeric type codes."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
        codec_options=codec,
    )
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(STRING_ALIAS_TESTS))
def test_type_string_aliases(collection, test):
    """Test $type matching with string aliases."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
        codec_options=codec,
    )
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(MATCHING_TESTS))
def test_type_matching(collection, test):
    """Test $type with number alias, BSON distinction, and null/missing behavior."""
    collection.insert_many(test.doc)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
        codec_options=codec,
    )
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


EQUIVALENCE_PAIRS = [
    ("double", 1),
    ("string", 2),
    ("object", 3),
    ("array", 4),
    ("binData", 5),
    ("objectId", 7),
    ("bool", 8),
    ("date", 9),
    ("null", 10),
    ("regex", 11),
    ("javascript", 13),
    ("int", 16),
    ("timestamp", 17),
    ("long", 18),
    ("decimal", 19),
    ("minKey", -1),
    ("maxKey", 127),
]


@pytest.mark.parametrize(
    "alias,code",
    EQUIVALENCE_PAIRS,
    ids=[f"{alias}_eq_{code}" for alias, code in EQUIVALENCE_PAIRS],
)
def test_type_numeric_string_equivalence(collection, alias, code):
    """Test that numeric type code and string alias return identical results."""
    collection.insert_many(ALL_TYPES_DOCS)
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result_code = execute_command(
        collection,
        {"find": collection.name, "filter": {"x": {"$type": code}}},
        codec_options=codec,
    )
    expected = result_code["cursor"]["firstBatch"]
    result_alias = execute_command(
        collection,
        {"find": collection.name, "filter": {"x": {"$type": alias}}},
        codec_options=codec,
    )
    assertSuccess(
        result_alias,
        expected,
        msg=f"$type: '{alias}' and $type: {code} should return same results",
    )
