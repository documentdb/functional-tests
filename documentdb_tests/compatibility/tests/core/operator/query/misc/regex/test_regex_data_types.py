"""
Tests for $regex query operator data type coverage.

Covers $regex matching behavior on different field types (string, int, long,
double, decimal128, boolean, date, null, object, ObjectId, BinData, regex,
timestamp, MinKey, MaxKey), null/missing field handling, and regex-typed fields.
"""

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NON_STRING_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_field_matches",
        filter={"a": {"$regex": "abc"}},
        doc=[{"_id": 1, "a": "abc"}, {"_id": 2, "a": "xyz"}],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex on string field should match",
    ),
    QueryTestCase(
        id="empty_string_field",
        filter={"a": {"$regex": "^$"}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 1, "a": ""}],
        msg="$regex ^$ on empty string field should match",
    ),
    QueryTestCase(
        id="int_field_no_match",
        filter={"a": {"$regex": "1"}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": "1"}],
        expected=[{"_id": 2, "a": "1"}],
        msg="$regex on int field should not match",
    ),
    QueryTestCase(
        id="long_field_no_match",
        filter={"a": {"$regex": "1"}},
        doc=[{"_id": 1, "a": Int64(1)}, {"_id": 2, "a": "1"}],
        expected=[{"_id": 2, "a": "1"}],
        msg="$regex on long field should not match",
    ),
    QueryTestCase(
        id="double_field_no_match",
        filter={"a": {"$regex": "1"}},
        doc=[{"_id": 1, "a": 1.5}, {"_id": 2, "a": "1.5"}],
        expected=[{"_id": 2, "a": "1.5"}],
        msg="$regex on double field should not match",
    ),
    QueryTestCase(
        id="decimal128_field_no_match",
        filter={"a": {"$regex": "1"}},
        doc=[{"_id": 1, "a": Decimal128("1")}, {"_id": 2, "a": "1"}],
        expected=[{"_id": 2, "a": "1"}],
        msg="$regex on decimal128 field should not match",
    ),
    QueryTestCase(
        id="boolean_field_no_match",
        filter={"a": {"$regex": "true"}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": "true"}],
        expected=[{"_id": 2, "a": "true"}],
        msg="$regex on boolean field should not match",
    ),
    QueryTestCase(
        id="date_field_no_match",
        filter={"a": {"$regex": "2024"}},
        doc=[
            {"_id": 1, "a": datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)},
            {"_id": 2, "a": "2024"},
        ],
        expected=[{"_id": 2, "a": "2024"}],
        msg="$regex on date field should not match",
    ),
    QueryTestCase(
        id="null_field_no_match",
        filter={"a": {"$regex": "null"}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": "null"}],
        expected=[{"_id": 2, "a": "null"}],
        msg="$regex on null field should not match",
    ),
    QueryTestCase(
        id="object_field_no_match",
        filter={"a": {"$regex": "x"}},
        doc=[{"_id": 1, "a": {"x": 1}}, {"_id": 2, "a": "x"}],
        expected=[{"_id": 2, "a": "x"}],
        msg="$regex on object field should not match",
    ),
    QueryTestCase(
        id="objectid_field_no_match",
        filter={"a": {"$regex": "abc"}},
        doc=[{"_id": 1, "a": ObjectId()}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex on ObjectId field should not match",
    ),
    QueryTestCase(
        id="bindata_field_no_match",
        filter={"a": {"$regex": "abc"}},
        doc=[{"_id": 1, "a": Binary(b"abc")}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex on BinData field should not match",
    ),
    QueryTestCase(
        id="timestamp_field_no_match",
        filter={"a": {"$regex": "1"}},
        doc=[{"_id": 1, "a": Timestamp(1, 1)}, {"_id": 2, "a": "1"}],
        expected=[{"_id": 2, "a": "1"}],
        msg="$regex on timestamp field should not match",
    ),
    QueryTestCase(
        id="minkey_field_no_match",
        filter={"a": {"$regex": ".*"}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex on MinKey field should not match",
    ),
    QueryTestCase(
        id="maxkey_field_no_match",
        filter={"a": {"$regex": ".*"}},
        doc=[{"_id": 1, "a": MaxKey()}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex on MaxKey field should not match",
    ),
    QueryTestCase(
        id="javascript_code_field_no_match",
        filter={"a": {"$regex": "function"}},
        doc=[{"_id": 1, "a": Code("function() {}")}, {"_id": 2, "a": "function"}],
        expected=[{"_id": 2, "a": "function"}],
        msg="$regex on JavaScript code field should not match",
    ),
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_field_not_matched",
        filter={"a": {"$regex": ".*"}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex .* should not match null field",
    ),
    QueryTestCase(
        id="missing_field_not_matched",
        filter={"a": {"$regex": ".*"}},
        doc=[{"_id": 1, "b": "abc"}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 2, "a": "abc"}],
        msg="$regex .* should not match missing field",
    ),
    QueryTestCase(
        id="mixed_present_and_missing",
        filter={"a": {"$regex": "abc"}},
        doc=[
            {"_id": 1, "a": "abc"},
            {"_id": 2, "a": None},
            {"_id": 3, "b": "abc"},
            {"_id": 4, "a": "xyz"},
        ],
        expected=[{"_id": 1, "a": "abc"}],
        msg="$regex should only match docs with matching string field",
    ),
]

REGEX_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="regex_field_matched_by_regex_query",
        filter={"a": {"$regex": "abc"}},
        doc=[{"_id": 1, "a": Regex("abc")}, {"_id": 2, "a": "abc"}],
        expected=[{"_id": 1, "a": Regex("abc")}, {"_id": 2, "a": "abc"}],
        msg="$regex should match both regex-typed and string fields",
    ),
]

ALL_TESTS = NON_STRING_TYPE_TESTS + NULL_MISSING_TESTS + REGEX_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_regex_data_types(collection, test):
    """Parametrized test for $regex data type coverage."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)
