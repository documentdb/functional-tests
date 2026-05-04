"""Tests for $lookup equality match behavior."""

from __future__ import annotations

import datetime
import math

import pytest
from bson import Binary, Code, DBRef, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_MAX,
    INT64_ZERO,
)

# Property [Equality Match Behavior]: equality matching compares resolved
# localField and foreignField values using standard BSON comparison.
LOOKUP_EQUALITY_MATCH_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "cross_numeric_type_matching",
        docs=[
            {"_id": 1, "lf": 42},
            {"_id": 2, "lf": Int64(42)},
            {"_id": 3, "lf": 42.0},
            {"_id": 4, "lf": Decimal128("42")},
            {"_id": 5, "lf": Decimal128("42.00")},
            {"_id": 6, "lf": Decimal128("4.2E+1")},
        ],
        foreign_docs=[{"_id": 100, "ff": 42}],
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
            {"_id": 1, "lf": 42, "joined": [{"_id": 100, "ff": 42}]},
            {"_id": 2, "lf": Int64(42), "joined": [{"_id": 100, "ff": 42}]},
            {"_id": 3, "lf": 42.0, "joined": [{"_id": 100, "ff": 42}]},
            {"_id": 4, "lf": Decimal128("42"), "joined": [{"_id": 100, "ff": 42}]},
            {"_id": 5, "lf": Decimal128("42.00"), "joined": [{"_id": 100, "ff": 42}]},
            {"_id": 6, "lf": Decimal128("4.2E+1"), "joined": [{"_id": 100, "ff": 42}]},
        ],
        msg=(
            "$lookup should match numerically equal values regardless of"
            " numeric type including Decimal128 with trailing zeros and"
            " scientific notation"
        ),
    ),
    LookupTestCase(
        "negative_zero_matches_all_zeros",
        docs=[{"_id": 1, "lf": DOUBLE_NEGATIVE_ZERO}],
        foreign_docs=[
            {"_id": 100, "ff": 0},
            {"_id": 101, "ff": DOUBLE_ZERO},
            {"_id": 102, "ff": INT64_ZERO},
            {"_id": 103, "ff": DECIMAL128_ZERO},
            {"_id": 104, "ff": DECIMAL128_NEGATIVE_ZERO},
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
                "lf": DOUBLE_NEGATIVE_ZERO,
                "joined": [
                    {"_id": 100, "ff": 0},
                    {"_id": 101, "ff": DOUBLE_ZERO},
                    {"_id": 102, "ff": INT64_ZERO},
                    {"_id": 103, "ff": DECIMAL128_ZERO},
                    {"_id": 104, "ff": DECIMAL128_NEGATIVE_ZERO},
                ],
            },
        ],
        msg=(
            "$lookup should match -0.0 against 0, 0.0, int(0),"
            " Decimal128('0'), and Decimal128('-0')"
        ),
    ),
    LookupTestCase(
        "nan_matches_nan_across_types",
        docs=[
            {"_id": 1, "lf": FLOAT_NAN},
            {"_id": 2, "lf": FLOAT_NEGATIVE_NAN},
        ],
        foreign_docs=[
            {"_id": 100, "ff": FLOAT_NAN},
            {"_id": 101, "ff": DECIMAL128_NAN},
            {"_id": 102, "ff": FLOAT_NEGATIVE_NAN},
            {"_id": 103, "ff": DECIMAL128_NEGATIVE_NAN},
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
                "lf": pytest.approx(math.nan, nan_ok=True),
                "joined": [
                    {"_id": 100, "ff": pytest.approx(math.nan, nan_ok=True)},
                    {"_id": 101, "ff": DECIMAL128_NAN},
                    {"_id": 102, "ff": pytest.approx(math.nan, nan_ok=True)},
                    {"_id": 103, "ff": DECIMAL128_NEGATIVE_NAN},
                ],
            },
            {
                "_id": 2,
                "lf": pytest.approx(math.nan, nan_ok=True),
                "joined": [
                    {"_id": 100, "ff": pytest.approx(math.nan, nan_ok=True)},
                    {"_id": 101, "ff": DECIMAL128_NAN},
                    {"_id": 102, "ff": pytest.approx(math.nan, nan_ok=True)},
                    {"_id": 103, "ff": DECIMAL128_NEGATIVE_NAN},
                ],
            },
        ],
        msg="$lookup should match NaN across float and Decimal128 types including negative NaN",
    ),
    LookupTestCase(
        "infinity_matches_infinity_across_types",
        docs=[
            {"_id": 1, "lf": FLOAT_INFINITY},
            {"_id": 2, "lf": FLOAT_NEGATIVE_INFINITY},
        ],
        foreign_docs=[
            {"_id": 100, "ff": FLOAT_INFINITY},
            {"_id": 101, "ff": DECIMAL128_INFINITY},
            {"_id": 102, "ff": FLOAT_NEGATIVE_INFINITY},
            {"_id": 103, "ff": DECIMAL128_NEGATIVE_INFINITY},
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
                "lf": FLOAT_INFINITY,
                "joined": [
                    {"_id": 100, "ff": FLOAT_INFINITY},
                    {"_id": 101, "ff": DECIMAL128_INFINITY},
                ],
            },
            {
                "_id": 2,
                "lf": FLOAT_NEGATIVE_INFINITY,
                "joined": [
                    {"_id": 102, "ff": FLOAT_NEGATIVE_INFINITY},
                    {"_id": 103, "ff": DECIMAL128_NEGATIVE_INFINITY},
                ],
            },
        ],
        msg=(
            "$lookup should match Infinity across float and Decimal128 types"
            " including negative infinity"
        ),
    ),
    LookupTestCase(
        "decimal128_extreme_values_self_match",
        docs=[
            {"_id": 1, "lf": DECIMAL128_MAX_COEFFICIENT},
            {"_id": 2, "lf": DECIMAL128_LARGE_EXPONENT},
            {"_id": 3, "lf": DECIMAL128_MIN_POSITIVE},
            {"_id": 4, "lf": DECIMAL128_MAX},
        ],
        foreign_docs=[
            {"_id": 100, "ff": DECIMAL128_MAX_COEFFICIENT},
            {"_id": 101, "ff": DECIMAL128_LARGE_EXPONENT},
            {"_id": 102, "ff": DECIMAL128_MIN_POSITIVE},
            {"_id": 103, "ff": DECIMAL128_MAX},
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
                "lf": DECIMAL128_MAX_COEFFICIENT,
                "joined": [
                    {"_id": 100, "ff": DECIMAL128_MAX_COEFFICIENT},
                ],
            },
            {
                "_id": 2,
                "lf": DECIMAL128_LARGE_EXPONENT,
                "joined": [{"_id": 101, "ff": DECIMAL128_LARGE_EXPONENT}],
            },
            {
                "_id": 3,
                "lf": DECIMAL128_MIN_POSITIVE,
                "joined": [{"_id": 102, "ff": DECIMAL128_MIN_POSITIVE}],
            },
            {
                "_id": 4,
                "lf": DECIMAL128_MAX,
                "joined": [{"_id": 103, "ff": DECIMAL128_MAX}],
            },
        ],
        msg=(
            "$lookup should self-match Decimal128 extreme values including"
            " max coefficient, large exponent, min positive, and max representable"
        ),
    ),
    LookupTestCase(
        "int64_double_precision_boundary",
        docs=[
            {"_id": 1, "lf": Int64(DOUBLE_MAX_SAFE_INTEGER)},
            {"_id": 2, "lf": INT64_MAX},
        ],
        foreign_docs=[
            {"_id": 100, "ff": float(DOUBLE_MAX_SAFE_INTEGER)},
            {"_id": 101, "ff": DOUBLE_FROM_INT64_MAX},
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
                "lf": Int64(DOUBLE_MAX_SAFE_INTEGER),
                "joined": [{"_id": 100, "ff": float(DOUBLE_MAX_SAFE_INTEGER)}],
            },
            {"_id": 2, "lf": INT64_MAX, "joined": []},
        ],
        msg=(
            "$lookup should match int64 at the max safe integer boundary with"
            " its double equivalent but not int64 max with its double"
            " approximation due to precision loss"
        ),
    ),
    LookupTestCase(
        "boolean_does_not_match_numeric",
        docs=[
            {"_id": 1, "lf": True},
            {"_id": 2, "lf": False},
        ],
        foreign_docs=[
            {"_id": 100, "ff": 1},
            {"_id": 101, "ff": 0},
            {"_id": 102, "ff": True},
            {"_id": 103, "ff": False},
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
            {"_id": 1, "lf": True, "joined": [{"_id": 102, "ff": True}]},
            {"_id": 2, "lf": False, "joined": [{"_id": 103, "ff": False}]},
        ],
        msg="$lookup should not match boolean True/False with numeric 1/0",
    ),
    LookupTestCase(
        "regex_matches_identical_regex_not_string",
        docs=[{"_id": 1, "lf": Regex("abc")}],
        foreign_docs=[
            {"_id": 100, "ff": Regex("abc")},
            {"_id": 101, "ff": "abc"},
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
                "lf": Regex("abc"),
                "joined": [{"_id": 100, "ff": Regex("abc")}],
            },
        ],
        msg="$lookup should match Regex only against identical Regex, not strings",
    ),
    LookupTestCase(
        "code_does_not_match_code_with_scope_or_string",
        docs=[
            {"_id": 1, "lf": Code("x")},
            {"_id": 2, "lf": Code("x", {})},
        ],
        foreign_docs=[
            {"_id": 100, "ff": Code("x")},
            {"_id": 101, "ff": Code("x", {})},
            {"_id": 102, "ff": "x"},
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
                "lf": Code("x"),
                "joined": [{"_id": 100, "ff": Code("x")}],
            },
            {
                "_id": 2,
                "lf": Code("x", {}),
                "joined": [{"_id": 101, "ff": Code("x", {})}],
            },
        ],
        msg=(
            "$lookup should not match Code with CodeWithScope or string,"
            " and CodeWithScope should not match Code or string"
        ),
    ),
    LookupTestCase(
        "minkey_and_maxkey_only_match_themselves",
        docs=[
            {"_id": 1, "lf": MinKey()},
            {"_id": 2, "lf": MaxKey()},
        ],
        foreign_docs=[
            {"_id": 100, "ff": MinKey()},
            {"_id": 101, "ff": MaxKey()},
            {"_id": 102, "ff": -1},
            {"_id": 103, "ff": 999_999},
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
                "lf": MinKey(),
                "joined": [{"_id": 100, "ff": MinKey()}],
            },
            {
                "_id": 2,
                "lf": MaxKey(),
                "joined": [{"_id": 101, "ff": MaxKey()}],
            },
        ],
        msg="$lookup should match MinKey and MaxKey only against themselves",
    ),
    LookupTestCase(
        "embedded_document_order_sensitive",
        docs=[
            {"_id": 1, "lf": {"a": 1, "b": 2}},
            {"_id": 2, "lf": {"b": 2, "a": 1}},
        ],
        foreign_docs=[{"_id": 100, "ff": {"a": 1, "b": 2}}],
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
                "lf": {"a": 1, "b": 2},
                "joined": [{"_id": 100, "ff": {"a": 1, "b": 2}}],
            },
            {"_id": 2, "lf": {"b": 2, "a": 1}, "joined": []},
        ],
        msg="$lookup should perform order-sensitive exact matching for embedded documents",
    ),
    LookupTestCase(
        "binary_subtype_matters",
        docs=[
            {"_id": 1, "lf": Binary(b"\x01\x02", 0)},
            {"_id": 2, "lf": Binary(b"\x01\x02", 5)},
        ],
        foreign_docs=[{"_id": 100, "ff": Binary(b"\x01\x02", 0)}],
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
                "lf": b"\x01\x02",
                "joined": [{"_id": 100, "ff": b"\x01\x02"}],
            },
            {"_id": 2, "lf": Binary(b"\x01\x02", 5), "joined": []},
        ],
        msg="$lookup should consider Binary subtype when matching",
    ),
    LookupTestCase(
        "timestamp_does_not_match_int_or_datetime",
        docs=[{"_id": 1, "lf": Timestamp(1000, 1)}],
        foreign_docs=[
            {"_id": 100, "ff": Timestamp(1000, 1)},
            {"_id": 101, "ff": 1000},
            {"_id": 102, "ff": datetime.datetime(1970, 1, 1, 0, 16, 40)},
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
                "lf": Timestamp(1000, 1),
                "joined": [{"_id": 100, "ff": Timestamp(1000, 1)}],
            },
        ],
        msg="$lookup should not match Timestamp against int or datetime",
    ),
    LookupTestCase(
        "timestamp_boundary_values_self_match",
        docs=[
            {"_id": 1, "lf": Timestamp(2**32 - 1, 1)},
            {"_id": 2, "lf": Timestamp(1, 2**32 - 1)},
            {"_id": 3, "lf": Timestamp(2**32 - 1, 2**32 - 1)},
        ],
        foreign_docs=[
            {"_id": 100, "ff": Timestamp(2**32 - 1, 1)},
            {"_id": 101, "ff": Timestamp(1, 2**32 - 1)},
            {"_id": 102, "ff": Timestamp(2**32 - 1, 2**32 - 1)},
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
                "lf": Timestamp(2**32 - 1, 1),
                "joined": [{"_id": 100, "ff": Timestamp(2**32 - 1, 1)}],
            },
            {
                "_id": 2,
                "lf": Timestamp(1, 2**32 - 1),
                "joined": [{"_id": 101, "ff": Timestamp(1, 2**32 - 1)}],
            },
            {
                "_id": 3,
                "lf": Timestamp(2**32 - 1, 2**32 - 1),
                "joined": [
                    {"_id": 102, "ff": Timestamp(2**32 - 1, 2**32 - 1)},
                ],
            },
        ],
        msg=(
            "$lookup should self-match Timestamp boundary values including"
            " max time, max increment, and max both components"
        ),
    ),
    LookupTestCase(
        "datetime_boundary_values_self_match",
        docs=[
            {"_id": 1, "lf": datetime.datetime(1960, 1, 1)},
            {"_id": 2, "lf": datetime.datetime(2099, 12, 31, 23, 59, 59, 999_000)},
            {"_id": 3, "lf": datetime.datetime(2024, 6, 15, 12, 30, 45, 123_000)},
        ],
        foreign_docs=[
            {"_id": 100, "ff": datetime.datetime(1960, 1, 1)},
            {"_id": 101, "ff": datetime.datetime(2099, 12, 31, 23, 59, 59, 999_000)},
            {"_id": 102, "ff": datetime.datetime(2024, 6, 15, 12, 30, 45, 123_000)},
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
                "lf": datetime.datetime(1960, 1, 1),
                "joined": [{"_id": 100, "ff": datetime.datetime(1960, 1, 1)}],
            },
            {
                "_id": 2,
                "lf": datetime.datetime(2099, 12, 31, 23, 59, 59, 999_000),
                "joined": [
                    {
                        "_id": 101,
                        "ff": datetime.datetime(2099, 12, 31, 23, 59, 59, 999_000),
                    },
                ],
            },
            {
                "_id": 3,
                "lf": datetime.datetime(2024, 6, 15, 12, 30, 45, 123_000),
                "joined": [
                    {
                        "_id": 102,
                        "ff": datetime.datetime(2024, 6, 15, 12, 30, 45, 123_000),
                    },
                ],
            },
        ],
        msg=(
            "$lookup should self-match datetime boundary values including"
            " pre-epoch, far future, and millisecond precision"
        ),
    ),
    LookupTestCase(
        "string_matches_identical_string",
        docs=[
            {"_id": 1, "lf": "hello"},
            {"_id": 2, "lf": ""},
        ],
        foreign_docs=[
            {"_id": 100, "ff": "hello"},
            {"_id": 101, "ff": ""},
            {"_id": 102, "ff": "Hello"},
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
            {"_id": 1, "lf": "hello", "joined": [{"_id": 100, "ff": "hello"}]},
            {"_id": 2, "lf": "", "joined": [{"_id": 101, "ff": ""}]},
        ],
        msg="$lookup should match strings by exact case-sensitive equality",
    ),
    LookupTestCase(
        "null_matches_null_and_missing",
        docs=[
            {"_id": 1, "lf": None},
            {"_id": 2},
        ],
        foreign_docs=[
            {"_id": 100, "ff": None},
            {"_id": 101},
            {"_id": 102, "ff": 0},
            {"_id": 103, "ff": False},
            {"_id": 104, "ff": ""},
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
                    {"_id": 100, "ff": None},
                    {"_id": 101},
                ],
            },
            {
                "_id": 2,
                "joined": [
                    {"_id": 100, "ff": None},
                    {"_id": 101},
                ],
            },
        ],
        msg=(
            "$lookup should match null against null and missing fields"
            " but not against 0, false, or empty string"
        ),
    ),
    LookupTestCase(
        "objectid_matches_identical_objectid",
        docs=[
            {"_id": 1, "lf": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
            {"_id": 2, "lf": ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")},
        ],
        foreign_docs=[
            {"_id": 100, "ff": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
            {"_id": 101, "ff": "aaaaaaaaaaaaaaaaaaaaaaaa"},
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
                "lf": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"),
                "joined": [
                    {"_id": 100, "ff": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
                ],
            },
            {
                "_id": 2,
                "lf": ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb"),
                "joined": [],
            },
        ],
        msg="$lookup should match ObjectId only against identical ObjectId not string",
    ),
    LookupTestCase(
        "array_matches_identical_array",
        docs=[
            {"_id": 1, "lf": [1, 2, 3]},
            {"_id": 2, "lf": [3, 2, 1]},
        ],
        foreign_docs=[
            {"_id": 100, "ff": [1, 2, 3]},
            {"_id": 101, "ff": 1},
            {"_id": 102, "ff": 2},
            {"_id": 103, "ff": 3},
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
                "lf": [1, 2, 3],
                "joined": [
                    {"_id": 100, "ff": [1, 2, 3]},
                    {"_id": 101, "ff": 1},
                    {"_id": 102, "ff": 2},
                    {"_id": 103, "ff": 3},
                ],
            },
            {
                "_id": 2,
                "lf": [3, 2, 1],
                "joined": [
                    {"_id": 100, "ff": [1, 2, 3]},
                    {"_id": 101, "ff": 1},
                    {"_id": 102, "ff": 2},
                    {"_id": 103, "ff": 3},
                ],
            },
        ],
        msg=(
            "$lookup should match array elements individually against scalar"
            " foreign values and against elements of foreign arrays"
        ),
    ),
    LookupTestCase(
        "dbref_matches_identical_dbref",
        docs=[
            {"_id": 1, "lf": DBRef("col", 1)},
            {"_id": 2, "lf": DBRef("col", 2)},
        ],
        foreign_docs=[
            {"_id": 100, "ff": DBRef("col", 1)},
            {"_id": 101, "ff": {"$ref": "col", "$id": 1}},
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
                "lf": DBRef("col", 1),
                "joined": [
                    {"_id": 100, "ff": DBRef("col", 1)},
                    {"_id": 101, "ff": DBRef("col", 1)},
                ],
            },
            {"_id": 2, "lf": DBRef("col", 2), "joined": []},
        ],
        msg="$lookup should match DBRef against identical DBRef",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_EQUALITY_MATCH_TESTS))
def test_lookup_equality_match(collection, test_case: LookupTestCase):
    """Test $lookup equality match behavior."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
