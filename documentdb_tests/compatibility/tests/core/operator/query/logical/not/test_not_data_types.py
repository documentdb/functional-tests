"""
Tests for $not query operator with BSON data types and operators.

Covers $not with each supported operator ($gt, $gte, $lt, $lte, $eq, $ne,
$in, $nin, $exists, $type, $size, $elemMatch, $mod, $regex), data type
coverage across BSON types, numeric equivalence across types, and BSON type
distinction (false vs 0, true vs 1, null vs missing).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "val": 5}, {"_id": 2, "val": 15}, {"_id": 3, "val": 25}]

BSON_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_with_gt",
        filter={"val": {"$not": {"$gt": 10}}},
        doc=DOCS,
        expected=[{"_id": 1, "val": 5}],
        msg="$not with $gt should return docs where val <= 10",
    ),
    QueryTestCase(
        id="not_with_gte",
        filter={"val": {"$not": {"$gte": 15}}},
        doc=DOCS,
        expected=[{"_id": 1, "val": 5}],
        msg="$not with $gte should return docs where val < 15",
    ),
    QueryTestCase(
        id="not_with_lt",
        filter={"val": {"$not": {"$lt": 10}}},
        doc=DOCS,
        expected=[{"_id": 2, "val": 15}, {"_id": 3, "val": 25}],
        msg="$not with $lt should return docs where val >= 10",
    ),
    QueryTestCase(
        id="not_with_lte",
        filter={"val": {"$not": {"$lte": 15}}},
        doc=DOCS,
        expected=[{"_id": 3, "val": 25}],
        msg="$not with $lte should return docs where val > 15",
    ),
    QueryTestCase(
        id="not_with_eq",
        filter={"val": {"$not": {"$eq": 5}}},
        doc=DOCS,
        expected=[{"_id": 2, "val": 15}, {"_id": 3, "val": 25}],
        msg="$not with $eq should return docs where val != 5",
    ),
    QueryTestCase(
        id="not_with_ne",
        filter={"val": {"$not": {"$ne": 5}}},
        doc=DOCS,
        expected=[{"_id": 1, "val": 5}],
        msg="$not with $ne (double negation) should return docs where val == 5",
    ),
    QueryTestCase(
        id="not_with_in",
        filter={"val": {"$not": {"$in": [5, 15]}}},
        doc=DOCS,
        expected=[{"_id": 3, "val": 25}],
        msg="$not with $in should return docs where val not in list",
    ),
    QueryTestCase(
        id="not_with_nin",
        filter={"val": {"$not": {"$nin": [5, 15]}}},
        doc=DOCS,
        expected=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}],
        msg="$not with $nin (double negation) should return docs where val in list",
    ),
    QueryTestCase(
        id="not_with_exists_true",
        filter={"val": {"$not": {"$exists": True}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "other": 10}],
        expected=[{"_id": 2, "other": 10}],
        msg="$not with $exists:true should return docs where field does not exist",
    ),
    QueryTestCase(
        id="not_with_type",
        filter={"val": {"$not": {"$type": "int"}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": "hello"}],
        expected=[{"_id": 2, "val": "hello"}],
        msg="$not with $type should return docs where field is not the specified type",
    ),
    QueryTestCase(
        id="not_with_size",
        filter={"val": {"$not": {"$size": 3}}},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": [1, 2]}],
        expected=[{"_id": 2, "val": [1, 2]}],
        msg="$not with $size should return docs where array is not the specified size",
    ),
    QueryTestCase(
        id="not_with_elemMatch",
        filter={"val": {"$not": {"$elemMatch": {"$gt": 5}}}},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": [1, 10]}],
        expected=[{"_id": 1, "val": [1, 2, 3]}],
        msg="$not with $elemMatch should return docs where no element satisfies condition",
    ),
    QueryTestCase(
        id="not_with_mod",
        filter={"val": {"$not": {"$mod": [2, 0]}}},
        doc=DOCS,
        expected=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}, {"_id": 3, "val": 25}],
        msg="$not with $mod should return docs where val is not divisible by 2",
    ),
    QueryTestCase(
        id="not_with_regex_operator",
        filter={"val": {"$not": {"$regex": "^h"}}},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": "world"}],
        expected=[{"_id": 2, "val": "world"}],
        msg="$not with $regex should return docs not matching the pattern",
    ),
    QueryTestCase(
        id="not_regex_no_match_returns_all",
        filter={"title": {"$not": {"$regex": "^Z"}}},
        doc=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}],
        expected=[{"_id": 1, "title": "Test"}, {"_id": 2, "title": "Hello"}],
        msg="$not with non-matching regex should return all documents",
    ),
    QueryTestCase(
        id="not_with_multiple_operators_gt_lt",
        filter={"val": {"$not": {"$gt": 5, "$lt": 20}}},
        doc=[{"_id": 1, "val": 3}, {"_id": 2, "val": 10}, {"_id": 3, "val": 25}],
        expected=[{"_id": 1, "val": 3}, {"_id": 3, "val": 25}],
        msg="$not with multiple operators ($gt and $lt) should negate the compound condition",
    ),
]

DATA_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_with_double_field",
        filter={"val": {"$not": {"$gt": 5}}},
        doc=[{"_id": 1, "val": 3.14}],
        expected=[{"_id": 1, "val": 3.14}],
        msg="$not $gt:5 on double field 3.14 should return the doc",
    ),
    QueryTestCase(
        id="not_with_boolean_field",
        filter={"val": {"$not": {"$eq": True}}},
        doc=[{"_id": 1, "val": True}, {"_id": 2, "val": False}],
        expected=[{"_id": 2, "val": False}],
        msg="$not $eq:true on boolean field should return false doc",
    ),
    QueryTestCase(
        id="not_with_int32_field",
        filter={"val": {"$not": {"$gt": 50}}},
        doc=[{"_id": 1, "val": 42}],
        expected=[{"_id": 1, "val": 42}],
        msg="$not $gt:50 on int32 field 42 should return the doc",
    ),
    QueryTestCase(
        id="not_with_int64_field",
        filter={"val": {"$not": {"$gt": 50}}},
        doc=[{"_id": 1, "val": Int64(42)}],
        expected=[{"_id": 1, "val": Int64(42)}],
        msg="$not $gt:50 on int64 field 42 should return the doc",
    ),
    QueryTestCase(
        id="not_with_decimal128_field",
        filter={"val": {"$not": {"$gt": 50}}},
        doc=[{"_id": 1, "val": Decimal128("42")}],
        expected=[{"_id": 1, "val": Decimal128("42")}],
        msg="$not $gt:50 on decimal128 field 42 should return the doc",
    ),
    QueryTestCase(
        id="not_with_null_field",
        filter={"val": {"$not": {"$gt": 5}}},
        doc=[{"_id": 1, "val": None}],
        expected=[{"_id": 1, "val": None}],
        msg="$not $gt:5 on null field should return the doc (null doesn't satisfy $gt)",
    ),
    QueryTestCase(
        id="not_with_object_field",
        filter={"val": {"$not": {"$type": "object"}}},
        doc=[{"_id": 1, "val": {"a": 1}}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:object should exclude object docs",
    ),
    QueryTestCase(
        id="not_with_array_field",
        filter={"val": {"$not": {"$type": "array"}}},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:array should exclude array docs",
    ),
    QueryTestCase(
        id="not_with_date_field",
        filter={"val": {"$not": {"$type": "date"}}},
        doc=[{"_id": 1, "val": datetime(2024, 1, 1, tzinfo=timezone.utc)}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:date should exclude date docs",
    ),
    QueryTestCase(
        id="not_with_timestamp_field",
        filter={"val": {"$not": {"$type": "timestamp"}}},
        doc=[{"_id": 1, "val": Timestamp(1, 1)}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:timestamp should exclude timestamp docs",
    ),
    QueryTestCase(
        id="not_with_minkey_field",
        filter={"val": {"$not": {"$type": "minKey"}}},
        doc=[{"_id": 1, "val": MinKey()}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:minKey should exclude minKey docs",
    ),
    QueryTestCase(
        id="not_with_maxkey_field",
        filter={"val": {"$not": {"$type": "maxKey"}}},
        doc=[{"_id": 1, "val": MaxKey()}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:maxKey should exclude maxKey docs",
    ),
    QueryTestCase(
        id="not_with_binary_field",
        filter={"val": {"$not": {"$type": "binData"}}},
        doc=[{"_id": 1, "val": Binary(b"\x01\x02")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:binData should exclude binary docs",
    ),
    QueryTestCase(
        id="not_with_objectid_field",
        filter={"val": {"$not": {"$type": "objectId"}}},
        doc=[{"_id": 1, "val": ObjectId("000000000000000000000001")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:objectId should exclude objectId docs",
    ),
    QueryTestCase(
        id="not_with_regex_field",
        filter={"val": {"$not": {"$type": "regex"}}},
        doc=[{"_id": 1, "val": Regex("abc")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:regex should exclude regex docs",
    ),
    QueryTestCase(
        id="not_with_javascript_field",
        filter={"val": {"$not": {"$type": "javascript"}}},
        doc=[{"_id": 1, "val": Code("function() {}")}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$not $type:javascript should exclude JavaScript Code docs",
    ),
    QueryTestCase(
        id="not_type_multiple",
        filter={"val": {"$not": {"$type": ["string", "int"]}}},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": 42}, {"_id": 3, "val": 3.14}],
        expected=[{"_id": 3, "val": 3.14}],
        msg="$not $type with multiple types should return docs matching neither type",
    ),
]

NUMERIC_EQUIVALENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int64_equals_int32_numerically",
        filter={"val": {"$not": {"$eq": 10}}},
        doc=[{"_id": 1, "val": Int64(10)}],
        expected=[],
        msg="$not $eq:10 should NOT return int64(10) — numerically equal",
    ),
    QueryTestCase(
        id="double_equals_int_numerically",
        filter={"val": {"$not": {"$eq": 10}}},
        doc=[{"_id": 1, "val": 10.0}],
        expected=[],
        msg="$not $eq:10 should NOT return double 10.0 — numerically equal",
    ),
    QueryTestCase(
        id="decimal128_equals_int_numerically",
        filter={"val": {"$not": {"$eq": 10}}},
        doc=[{"_id": 1, "val": Decimal128("10")}],
        expected=[],
        msg="$not $eq:10 should NOT return Decimal128('10') — numerically equal",
    ),
]

BSON_TYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_vs_zero_not_eq_false",
        filter={"val": {"$not": {"$eq": False}}},
        doc=[{"_id": 1, "val": False}, {"_id": 2, "val": 0}],
        expected=[{"_id": 2, "val": 0}],
        msg="$not $eq:false should return 0 but not false (type distinction)",
    ),
    QueryTestCase(
        id="true_vs_one_not_eq_true",
        filter={"val": {"$not": {"$eq": True}}},
        doc=[{"_id": 1, "val": True}, {"_id": 2, "val": 1}],
        expected=[{"_id": 2, "val": 1}],
        msg="$not $eq:true should return 1 but not true (type distinction)",
    ),
    QueryTestCase(
        id="null_vs_missing_not_eq_null",
        filter={"val": {"$not": {"$eq": None}}},
        doc=[{"_id": 1, "val": None}, {"_id": 2, "other": 1}, {"_id": 3, "val": 5}],
        expected=[{"_id": 3, "val": 5}],
        msg="$not $eq:null should exclude both null and missing docs",
    ),
    QueryTestCase(
        id="not_gt_cross_type_comparison",
        filter={"val": {"$not": {"$gt": "string"}}},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": "zebra"}],
        expected=[{"_id": 1, "val": 5}],
        msg="$not $gt:string on numeric field returns numeric doc (type bracketing)",
    ),
]

ALL_TESTS = (
    BSON_OPERATOR_TESTS + DATA_TYPE_TESTS + NUMERIC_EQUIVALENCE_TESTS + BSON_TYPE_DISTINCTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_data_types(collection, test):
    """Test $not query operator with various BSON data types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
