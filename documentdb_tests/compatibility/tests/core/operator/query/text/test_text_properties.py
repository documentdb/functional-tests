"""
Tests for $text query operator properties.

Validates null/missing field handling, BSON data types, and textScore projection and ordering.
"""

from datetime import datetime

import pytest
from bson import Decimal128, Int64, ObjectId, Regex, Timestamp
from bson.code import Code
from bson.max_key import MaxKey
from bson.min_key import MinKey

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, Len

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_field",
        filter={"$text": {"$search": "hello"}},
        doc=[
            {"_id": 1, "content": None},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[{"_id": 2, "content": "hello world"}],
        msg="Null field should not match",
    ),
    QueryTestCase(
        id="missing_field",
        filter={"$text": {"$search": "hello"}},
        doc=[
            {"_id": 1, "other": "data"},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[{"_id": 2, "content": "hello world"}],
        msg="Missing field should not match",
    ),
    QueryTestCase(
        id="empty_string_field",
        filter={"$text": {"$search": "hello"}},
        doc=[
            {"_id": 1, "content": ""},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[{"_id": 2, "content": "hello world"}],
        msg="Empty string field should not match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_MISSING_TESTS))
def test_text_null_and_missing(collection, test):
    """Test $text with null/missing/empty field values."""
    collection.create_index([("content", "text")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


NON_STRING_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="data_int32_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": 42}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Int32 field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_int64_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": Int64(99)}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Int64 field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_double_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": 3.14}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Double field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_boolean_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": True}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Boolean field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_date_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": datetime(2024, 1, 1)}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Date field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_object_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": {"nested": "hello"}}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="$text should not match text in object field",
    ),
    QueryTestCase(
        id="data_decimal128_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": Decimal128("9.99")}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Decimal128 field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_bindata_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": b"hello"}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="BinData field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_objectid_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": ObjectId()}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="ObjectId field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_regex_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": Regex("hello")}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Regex field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_javascript_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": Code("function(){}")}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="JavaScript field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_timestamp_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": Timestamp(1, 1)}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="Timestamp field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_minkey_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": MinKey()}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="MinKey field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_maxkey_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": MaxKey()}, {"_id": 2, "content": "hello"}],
        expected=[{"_id": 2, "content": "hello"}],
        msg="MaxKey field should not be matched by $text query",
    ),
    QueryTestCase(
        id="data_array_of_strings",
        filter={"$text": {"$search": "hello"}},
        doc=[
            {"_id": 1, "content": ["hello", "world"]},
            {"_id": 2, "content": "goodbye"},
        ],
        expected=[{"_id": 1, "content": ["hello", "world"]}],
        msg="Array of strings should be matched by $text query",
    ),
    QueryTestCase(
        id="data_string_field",
        filter={"$text": {"$search": "hello"}},
        doc=[{"_id": 1, "content": "hello world"}],
        expected=[{"_id": 1, "content": "hello world"}],
        msg="String field should be matched by $text query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_STRING_TYPE_TESTS))
def test_text_bson_data_types(collection, test):
    """Test $text query does not match documents where the field contains non-string BSON types."""
    collection.create_index([("content", "text")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


def test_text_meta_textscore_projection(collection):
    """Test $text with $meta textScore in projection returns score field."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "coffee database system"},
            {"_id": 2, "content": "python programming"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "coffee"}},
            "projection": {"content": 1, "score": {"$meta": "textScore"}},
        },
    )
    assertProperties(
        result,
        {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0._id": Exists(),
            "cursor.firstBatch.0.score": IsType("double"),
        },
        raw_res=True,
        msg="Should return document with numeric score field",
    )


def test_text_aggregate_match_count(collection):
    """Test $text in aggregate $match followed by $count."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "coffee database"},
            {"_id": 2, "content": "coffee system"},
            {"_id": 3, "content": "python language"},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$text": {"$search": "coffee"}}},
                {"$count": "total"},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"total": 2}], msg="Should count matching documents")


def test_text_textscore_ordering(collection):
    """Test doc with more term occurrences scores higher."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "coffee"},
            {"_id": 2, "content": "coffee coffee coffee"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "coffee"}},
            "projection": {"score": {"$meta": "textScore"}},
            "sort": {"score": {"$meta": "textScore"}},
        },
    )
    assertProperties(
        result,
        {
            "cursor.firstBatch": Len(2),
            "cursor.firstBatch.0._id": Eq(2),
        },
        raw_res=True,
        msg="Doc with more occurrences should be first when sorted by textScore",
    )
