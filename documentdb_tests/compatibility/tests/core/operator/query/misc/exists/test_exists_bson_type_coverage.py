"""
Tests for $exists BSON type coverage.

Verifies $exists: true matches all BSON types when field is present (int, long,
double, decimal128, string, bool, null, object, array, binData, objectId, regex,
timestamp, date, minKey, maxKey), and $exists: false core semantics (null field
still exists, missing field matches).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.codec_options import CodecOptions

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EXISTS_TRUE_BSON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": 1}],
        expected=[{"_id": 1, "a": 1}],
        msg="$exists: true matches int field",
    ),
    QueryTestCase(
        id="long",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": Int64(1)}],
        expected=[{"_id": 1, "a": Int64(1)}],
        msg="$exists: true matches long field",
    ),
    QueryTestCase(
        id="double",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": 1.5}],
        expected=[{"_id": 1, "a": 1.5}],
        msg="$exists: true matches double field",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": Decimal128("1.0")}],
        expected=[{"_id": 1, "a": Decimal128("1.0")}],
        msg="$exists: true matches decimal128 field",
    ),
    QueryTestCase(
        id="string",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$exists: true matches string field",
    ),
    QueryTestCase(
        id="bool_false",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": False}],
        expected=[{"_id": 1, "a": False}],
        msg="$exists: true matches boolean false field",
    ),
    QueryTestCase(
        id="null",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": None}],
        expected=[{"_id": 1, "a": None}],
        msg="$exists: true matches null field (field exists with null value)",
    ),
    QueryTestCase(
        id="object",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": {"b": 1}}],
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="$exists: true matches object field",
    ),
    QueryTestCase(
        id="empty_object",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": {}}],
        expected=[{"_id": 1, "a": {}}],
        msg="$exists: true matches empty object field",
    ),
    QueryTestCase(
        id="array",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$exists: true matches array field",
    ),
    QueryTestCase(
        id="empty_array",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": []}],
        expected=[{"_id": 1, "a": []}],
        msg="$exists: true matches empty array field",
    ),
    QueryTestCase(
        id="empty_string",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": ""}],
        expected=[{"_id": 1, "a": ""}],
        msg="$exists: true matches empty string field",
    ),
    QueryTestCase(
        id="zero",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": 0}],
        expected=[{"_id": 1, "a": 0}],
        msg="$exists: true matches zero field",
    ),
    QueryTestCase(
        id="bindata",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": Binary(b"data", 0)}],
        expected=[{"_id": 1, "a": b"data"}],
        msg="$exists: true matches binData field",
    ),
    QueryTestCase(
        id="bindata_user_defined",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": Binary(b"data", 128)}],
        expected=[{"_id": 1, "a": Binary(b"data", 128)}],
        msg="$exists: true matches binData subtype 128 (user-defined)",
    ),
    QueryTestCase(
        id="objectid",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        expected=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        msg="$exists: true matches objectId field",
    ),
    QueryTestCase(
        id="regex",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": Regex("pattern", "i")}],
        expected=[{"_id": 1, "a": Regex("pattern", "i")}],
        msg="$exists: true matches regex field",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": Timestamp(1, 1)}],
        expected=[{"_id": 1, "a": Timestamp(1, 1)}],
        msg="$exists: true matches timestamp field",
    ),
    QueryTestCase(
        id="date",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$exists: true matches date field",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": MinKey()}],
        expected=[{"_id": 1, "a": MinKey()}],
        msg="$exists: true matches minKey field",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$exists": True}},
        doc=[{"_id": 1, "a": MaxKey()}],
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="$exists: true matches maxKey field",
    ),
]

ALL_TESTS = EXISTS_TRUE_BSON_TESTS


TZ_AWARE_CODEC = CodecOptions(tz_aware=True)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_exists_field_value_types(collection, test):
    """Parametrized test for $exists field value type handling."""
    collection.insert_many(test.doc)
    codec = TZ_AWARE_CODEC
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter}, codec_options=codec
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)
