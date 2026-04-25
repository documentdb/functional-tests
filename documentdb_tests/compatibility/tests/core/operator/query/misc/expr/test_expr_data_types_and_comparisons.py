"""
Tests for $expr data type coverage, BSON truthiness, numeric equivalence,
type distinction, and comparison operators.

Covers truthiness by BSON type, field-to-field comparison with $gt/$gte/$lte,
cross-type numeric equivalence, BSON type distinction, BSON comparison order
boundaries, and literal expression truthiness.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.codec_options import CodecOptions

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT64_ZERO,
)

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="truthiness_true",
        doc=[{"_id": 1, "a": True}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": True}],
        msg="true is truthy",
    ),
    QueryTestCase(
        id="truthiness_false",
        doc=[{"_id": 1, "a": False}],
        filter={"$expr": "$a"},
        expected=[],
        msg="false is falsy",
    ),
    QueryTestCase(
        id="truthiness_int_1",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": 1}],
        msg="non-zero int is truthy",
    ),
    QueryTestCase(
        id="truthiness_int_0",
        doc=[{"_id": 1, "a": 0}],
        filter={"$expr": "$a"},
        expected=[],
        msg="zero int is falsy",
    ),
    QueryTestCase(
        id="truthiness_long_1",
        doc=[{"_id": 1, "a": Int64(1)}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": Int64(1)}],
        msg="non-zero long is truthy",
    ),
    QueryTestCase(
        id="truthiness_long_0",
        doc=[{"_id": 1, "a": INT64_ZERO}],
        filter={"$expr": "$a"},
        expected=[],
        msg="zero long is falsy",
    ),
    QueryTestCase(
        id="truthiness_double_1",
        doc=[{"_id": 1, "a": 1.0}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": 1.0}],
        msg="non-zero double is truthy",
    ),
    QueryTestCase(
        id="truthiness_double_0",
        doc=[{"_id": 1, "a": 0.0}],
        filter={"$expr": "$a"},
        expected=[],
        msg="zero double is falsy",
    ),
    QueryTestCase(
        id="truthiness_decimal_1",
        doc=[{"_id": 1, "a": Decimal128("1")}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": Decimal128("1")}],
        msg="non-zero Decimal128 is truthy",
    ),
    QueryTestCase(
        id="truthiness_decimal_0",
        doc=[{"_id": 1, "a": DECIMAL128_ZERO}],
        filter={"$expr": "$a"},
        expected=[],
        msg="zero Decimal128 is falsy",
    ),
    QueryTestCase(
        id="truthiness_null",
        doc=[{"_id": 1, "a": None}],
        filter={"$expr": "$a"},
        expected=[],
        msg="null is falsy",
    ),
    QueryTestCase(
        id="truthiness_string_nonempty",
        doc=[{"_id": 1, "a": "hello"}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": "hello"}],
        msg="non-empty string is truthy",
    ),
    QueryTestCase(
        id="truthiness_string_empty",
        doc=[{"_id": 1, "a": ""}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": ""}],
        msg="empty string is truthy in BSON",
    ),
    QueryTestCase(
        id="truthiness_infinity",
        doc=[{"_id": 1, "a": FLOAT_INFINITY}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": FLOAT_INFINITY}],
        msg="Infinity is truthy",
    ),
    QueryTestCase(
        id="truthiness_neg_zero_double",
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}],
        filter={"$expr": "$a"},
        expected=[],
        msg="-0.0 is falsy",
    ),
    QueryTestCase(
        id="truthiness_neg_zero_decimal",
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO}],
        filter={"$expr": "$a"},
        expected=[],
        msg="Decimal128('-0') is falsy",
    ),
    QueryTestCase(
        id="truthiness_objectid",
        doc=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": ObjectId("000000000000000000000001")}],
        msg="ObjectId is truthy",
    ),
    QueryTestCase(
        id="truthiness_empty_obj",
        doc=[{"_id": 1, "a": {}}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": {}}],
        msg="empty object is truthy",
    ),
    QueryTestCase(
        id="truthiness_empty_arr",
        doc=[{"_id": 1, "a": []}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": []}],
        msg="empty array is truthy",
    ),
    QueryTestCase(
        id="truthiness_nonempty_arr",
        doc=[{"_id": 1, "a": [1, 2]}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="non-empty array is truthy",
    ),
    QueryTestCase(
        id="truthiness_bindata_subtype_0",
        doc=[{"_id": 1, "a": Binary(b"abc", 0)}],
        filter={"$expr": "$a"},
        # driver automatically converts subtype 0 to raw bytes,
        # so expected is in raw form instead of Binary(b"abc", 0)
        expected=[{"_id": 1, "a": b"abc"}],
        msg="BinData subtype 0 (generic) is truthy",
    ),
    QueryTestCase(
        id="truthiness_bindata_subtype_1",
        doc=[{"_id": 1, "a": Binary(b"abc", 1)}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": Binary(b"abc", 1)}],
        msg="BinData subtype 1 (function) is truthy",
    ),
    QueryTestCase(
        id="truthiness_bindata_subtype_4",
        doc=[
            {
                "_id": 1,
                "a": Binary(b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10", 4),
            }
        ],
        filter={"$expr": "$a"},
        expected=[
            {
                "_id": 1,
                "a": Binary(b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10", 4),
            }
        ],
        msg="BinData subtype 4 (UUID) is truthy",
    ),
    QueryTestCase(
        id="truthiness_bindata_subtype_128",
        doc=[{"_id": 1, "a": Binary(b"abc", 128)}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": Binary(b"abc", 128)}],
        msg="BinData subtype 128 (user-defined) is truthy",
    ),
    QueryTestCase(
        id="truthiness_regex",
        doc=[{"_id": 1, "a": Regex("pattern")}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": Regex("pattern")}],
        msg="regex is truthy",
    ),
    QueryTestCase(
        id="truthiness_minkey",
        doc=[{"_id": 1, "a": MinKey()}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": MinKey()}],
        msg="MinKey is truthy",
    ),
    QueryTestCase(
        id="truthiness_maxkey",
        doc=[{"_id": 1, "a": MaxKey()}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="MaxKey is truthy",
    ),
    QueryTestCase(
        id="truthiness_timestamp",
        doc=[{"_id": 1, "a": Timestamp(1, 1)}],
        filter={"$expr": "$a"},
        expected=[{"_id": 1, "a": Timestamp(1, 1)}],
        msg="Timestamp is truthy",
    ),
    QueryTestCase(
        id="truthiness_missing",
        doc=[{"_id": 1, "b": 1}],
        filter={"$expr": "$a"},
        expected=[],
        msg="missing field is falsy",
    ),
    QueryTestCase(
        id="gt_field_to_field",
        doc=[{"_id": 1, "a": 10, "b": 5}, {"_id": 2, "a": 5, "b": 10}],
        filter={"$expr": {"$gt": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 10, "b": 5}],
        msg="field-to-field comparison",
    ),
    QueryTestCase(
        id="gte_equal",
        doc=[{"_id": 1, "a": 5, "b": 5}, {"_id": 2, "a": 3, "b": 5}],
        filter={"$expr": {"$gte": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 5, "b": 5}],
        msg="$gte matches when fields are equal",
    ),
    QueryTestCase(
        id="gte_greater",
        doc=[{"_id": 1, "a": 10, "b": 5}, {"_id": 2, "a": 3, "b": 5}],
        filter={"$expr": {"$gte": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 10, "b": 5}],
        msg="$gte matches when first field is greater",
    ),
    QueryTestCase(
        id="lte_equal",
        doc=[{"_id": 1, "a": 5, "b": 5}, {"_id": 2, "a": 8, "b": 5}],
        filter={"$expr": {"$lte": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 5, "b": 5}],
        msg="$lte matches when fields are equal",
    ),
    QueryTestCase(
        id="lte_less",
        doc=[{"_id": 1, "a": 3, "b": 5}, {"_id": 2, "a": 8, "b": 5}],
        filter={"$expr": {"$lte": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 3, "b": 5}],
        msg="$lte matches when first field is less",
    ),
    QueryTestCase(
        id="numeric_eq_int_double",
        doc=[{"_id": 1, "a": 1, "b": 1.0}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 1, "b": 1.0}],
        msg="int == double cross-type equivalence",
    ),
    QueryTestCase(
        id="numeric_eq_int_zero_double_zero",
        doc=[{"_id": 1, "a": 0, "b": 0.0}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": 0, "b": 0.0}],
        msg="int 0 == double 0.0",
    ),
    QueryTestCase(
        id="numeric_eq_neg_zero_double",
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO, "b": 0.0}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO, "b": 0.0}],
        msg="negative zero == positive zero",
    ),
    QueryTestCase(
        id="numeric_eq_neg_zero_decimal",
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO, "b": DECIMAL128_ZERO}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO, "b": DECIMAL128_ZERO}],
        msg="Decimal128 -0 == 0",
    ),
    QueryTestCase(
        id="numeric_eq_decimal128_int",
        doc=[{"_id": 1, "a": Decimal128("5"), "b": 5}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": Decimal128("5"), "b": 5}],
        msg="Decimal128 == int cross-type equivalence",
    ),
    QueryTestCase(
        id="numeric_eq_decimal128_double",
        doc=[{"_id": 1, "a": Decimal128("2.5"), "b": 2.5}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": Decimal128("2.5"), "b": 2.5}],
        msg="Decimal128 == double cross-type equivalence",
    ),
    QueryTestCase(
        id="numeric_eq_decimal128_zero_int_zero",
        doc=[{"_id": 1, "a": DECIMAL128_ZERO, "b": 0}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": DECIMAL128_ZERO, "b": 0}],
        msg="Decimal128('0') == int 0",
    ),
    QueryTestCase(
        id="numeric_eq_decimal128_neg_zero_double_neg_zero",
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO, "b": DOUBLE_NEGATIVE_ZERO}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": DECIMAL128_NEGATIVE_ZERO, "b": DOUBLE_NEGATIVE_ZERO}],
        msg="Decimal128('-0') == double -0.0",
    ),
    QueryTestCase(
        id="numeric_neq_int_string",
        doc=[{"_id": 1, "a": 1, "b": "1"}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[],
        msg="int != string (different BSON types)",
    ),
    QueryTestCase(
        id="type_distinction_false_vs_zero",
        doc=[{"_id": 1, "a": False, "b": 0}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[],
        msg="false != 0 (bool vs int)",
    ),
    QueryTestCase(
        id="type_distinction_true_vs_one",
        doc=[{"_id": 1, "a": True, "b": 1}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[],
        msg="true != 1 (bool vs int)",
    ),
    QueryTestCase(
        id="type_distinction_null_vs_zero",
        doc=[{"_id": 1, "a": None, "b": 0}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[],
        msg="null != 0 (null vs int)",
    ),
    QueryTestCase(
        id="type_distinction_empty_str_vs_null",
        doc=[{"_id": 1, "a": "", "b": None}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[],
        msg="empty string != null",
    ),
    QueryTestCase(
        id="type_distinction_null_vs_missing",
        doc=[{"_id": 1, "a": None}],
        filter={"$expr": {"$eq": ["$a", "$b"]}},
        expected=[],
        msg="null != missing field in $expr",
    ),
    QueryTestCase(
        id="bson_order_minkey_lt_null",
        doc=[{"_id": 1, "a": MinKey(), "b": None}],
        filter={"$expr": {"$lt": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": MinKey(), "b": None}],
        msg="MinKey < null",
    ),
    QueryTestCase(
        id="maxkey_gt_all",
        doc=[{"_id": 1, "a": MaxKey(), "b": Regex("pattern")}],
        filter={"$expr": {"$gt": ["$a", "$b"]}},
        expected=[{"_id": 1, "a": MaxKey(), "b": Regex("pattern")}],
        msg="MaxKey > any other type",
    ),
    QueryTestCase(
        id="literal_false",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": False},
        expected=[],
        msg="literal false is falsy — no documents match",
    ),
    QueryTestCase(
        id="literal_null",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": None},
        expected=[],
        msg="literal null is falsy — no documents match",
    ),
    QueryTestCase(
        id="literal_string",
        doc=[{"_id": 1, "a": 1}],
        filter={"$expr": "hello"},
        expected=[{"_id": 1, "a": 1}],
        msg="literal non-empty string is truthy — all documents match",
    ),
    QueryTestCase(
        id="gt_nested_dotted_fields",
        doc=[
            {"_id": 1, "stats": {"score": 90, "threshold": 80}},
            {"_id": 2, "stats": {"score": 50, "threshold": 80}},
        ],
        filter={"$expr": {"$gt": ["$stats.score", "$stats.threshold"]}},
        expected=[{"_id": 1, "stats": {"score": 90, "threshold": 80}}],
        msg="$expr comparing nested dotted fields from same document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_expr_data_types(collection, test):
    """Test $expr data type coverage, BSON comparison order, and numeric equivalence."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)


def test_expr_nan_eq_nan(collection):
    """Test $expr NaN == NaN is true"""
    collection.insert_one({"_id": 1, "a": FLOAT_NAN, "b": FLOAT_NAN})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$eq": ["$a", "$b"]}},
        },
    )
    assertSuccessNaN(result, [{"_id": 1, "a": FLOAT_NAN, "b": FLOAT_NAN}])


def test_expr_truthiness_nan_float(collection):
    """Test $expr truthiness — float NaN field is truthy."""
    collection.insert_one({"_id": 1, "a": FLOAT_NAN})
    result = execute_command(collection, {"find": collection.name, "filter": {"$expr": "$a"}})
    assertSuccessNaN(result, [{"_id": 1, "a": FLOAT_NAN}])


def test_expr_truthiness_decimal_nan(collection):
    """Test $expr truthiness — Decimal128 NaN field is truthy."""
    collection.insert_one({"_id": 1, "a": DECIMAL128_NAN})
    result = execute_command(collection, {"find": collection.name, "filter": {"$expr": "$a"}})
    assertSuccessNaN(result, [{"_id": 1, "a": DECIMAL128_NAN}])


def test_expr_truthiness_date(collection):
    """Test $expr truthiness — UTC datetime field is truthy."""
    collection.insert_one({"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)})
    codec = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$expr": "$a"}}, codec_options=codec
    )
    assertResult(
        result,
        expected=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="date is truthy",
    )
