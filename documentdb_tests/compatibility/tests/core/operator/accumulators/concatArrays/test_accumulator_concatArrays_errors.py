"""Tests for $concatArrays accumulator: arity, expression errors, null handling, type rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property [Arity Rejection]: $concatArrays in accumulator context is unary
# and rejects array syntax.
# ---------------------------------------------------------------------------
CONCATARRAYS_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": []}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": ["$v"]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_literal_array",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": [1]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject single-element literal array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"_id": 1, "a": [1], "b": [2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": ["$a", "$b"]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$add": [1, 2], "$multiply": [3, 4]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$concatArrays should reject multi-key expression object",
    ),
]

# ---------------------------------------------------------------------------
# Property [Expression Error Propagation]: errors from sub-expressions
# propagate through $concatArrays accumulator.
# ---------------------------------------------------------------------------
CONCATARRAYS_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_divide_by_zero",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$divide": ["$v", 0]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$concatArrays should propagate $divide by zero error",
    ),
    AccumulatorTestCase(
        "expr_error_divide_by_zero_field_path",
        docs=[{"_id": 0, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$divide": [1, "$v"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$concatArrays should propagate $divide by zero when divisor comes from field path",
    ),
    AccumulatorTestCase(
        "expr_error_divide_by_zero_later_doc",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$concatArrays": {"$let": {"vars": {}, "in": [{"$divide": [1, "$v"]}]}},
                    },
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$concatArrays should propagate error even when failing doc is not the first",
    ),
    AccumulatorTestCase(
        "expr_error_conversion_failure",
        docs=[{"_id": 1, "v": "abc"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": {"$toInt": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$concatArrays should propagate $toInt conversion error",
    ),
]

# ---------------------------------------------------------------------------
# Property [BSON Constant Arguments]: non-array BSON constants as the
# accumulator argument produce TYPE_MISMATCH_ERROR.
# ---------------------------------------------------------------------------
CONCATARRAYS_BSON_CONSTANT_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "const_true",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": True}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean True constant",
    ),
    AccumulatorTestCase(
        "const_false",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": False}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean False constant",
    ),
    AccumulatorTestCase(
        "const_int",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": 42}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject int constant",
    ),
    AccumulatorTestCase(
        "const_int64",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": Int64(42)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Int64 constant",
    ),
    AccumulatorTestCase(
        "const_double",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": 3.14}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject double constant",
    ),
    AccumulatorTestCase(
        "const_decimal128",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": Decimal128("1.5")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Decimal128 constant",
    ),
    AccumulatorTestCase(
        "const_string",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": "hello"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject string constant",
    ),
    AccumulatorTestCase(
        "const_binary",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": Binary(b"\x01")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Binary constant",
    ),
    AccumulatorTestCase(
        "const_objectid",
        docs=[{"v": [1]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": ObjectId("000000000000000000000000")},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject ObjectId constant",
    ),
    AccumulatorTestCase(
        "const_datetime",
        docs=[{"v": [1]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": datetime(2020, 1, 1, tzinfo=timezone.utc)},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject datetime constant",
    ),
    AccumulatorTestCase(
        "const_timestamp",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": Timestamp(1, 1)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Timestamp constant",
    ),
    AccumulatorTestCase(
        "const_regex",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": Regex("abc", "i")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Regex constant",
    ),
    AccumulatorTestCase(
        "const_null",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": None}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject null constant",
    ),
    AccumulatorTestCase(
        "const_minkey",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": MinKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MinKey constant",
    ),
    AccumulatorTestCase(
        "const_maxkey",
        docs=[{"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": MaxKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MaxKey constant",
    ),
]

# ---------------------------------------------------------------------------
# Property [Null Handling]: null field values produce TYPE_MISMATCH_ERROR in
# accumulator context.
# ---------------------------------------------------------------------------
CONCATARRAYS_NULL_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_single",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null field value",
    ),
    AccumulatorTestCase(
        "null_all",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when all field values are null",
    ),
    AccumulatorTestCase(
        "null_after_array",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": None},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null even after valid arrays",
    ),
    AccumulatorTestCase(
        "null_before_array",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2, "v": [1, 2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null even before valid arrays",
    ),
]

# Property [Non-Array Type Rejection]: every non-array, non-null BSON type
# produces TYPE_MISMATCH_ERROR.
CONCATARRAYS_TYPE_REJECTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_reject_string",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject string field value",
    ),
    AccumulatorTestCase(
        "type_reject_int32",
        docs=[{"_id": 1, "v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject int32 field value",
    ),
    AccumulatorTestCase(
        "type_reject_int64",
        docs=[{"_id": 1, "v": Int64(42)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Int64 field value",
    ),
    AccumulatorTestCase(
        "type_reject_double",
        docs=[{"_id": 1, "v": 3.14}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject double field value",
    ),
    AccumulatorTestCase(
        "type_reject_decimal128",
        docs=[{"_id": 1, "v": Decimal128("1.5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Decimal128 field value",
    ),
    AccumulatorTestCase(
        "type_reject_bool_true",
        docs=[{"_id": 1, "v": True}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean True field value",
    ),
    AccumulatorTestCase(
        "type_reject_bool_false",
        docs=[{"_id": 1, "v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean False field value",
    ),
    AccumulatorTestCase(
        "type_reject_object",
        docs=[{"_id": 1, "v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject embedded document field value",
    ),
    AccumulatorTestCase(
        "type_reject_empty_object",
        docs=[{"_id": 1, "v": {}}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject empty document field value",
    ),
    AccumulatorTestCase(
        "type_reject_objectid",
        docs=[{"_id": 1, "v": ObjectId()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject ObjectId field value",
    ),
    AccumulatorTestCase(
        "type_reject_datetime",
        docs=[{"_id": 1, "v": datetime(2023, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject datetime field value",
    ),
    AccumulatorTestCase(
        "type_reject_binary",
        docs=[{"_id": 1, "v": Binary(b"\x01\x02")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Binary field value",
    ),
    AccumulatorTestCase(
        "type_reject_regex",
        docs=[{"_id": 1, "v": Regex("abc", "i")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Regex field value",
    ),
    AccumulatorTestCase(
        "type_reject_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1, 1)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Timestamp field value",
    ),
    AccumulatorTestCase(
        "type_reject_minkey",
        docs=[{"_id": 1, "v": MinKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MinKey field value",
    ),
    AccumulatorTestCase(
        "type_reject_maxkey",
        docs=[{"_id": 1, "v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MaxKey field value",
    ),
]

# Property [Mixed Valid and Invalid]: when one document has a valid array and
# another has an invalid type, the error is raised.
CONCATARRAYS_MIXED_INVALID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_array_and_string",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": "hello"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when mixing array and string values",
    ),
    AccumulatorTestCase(
        "mixed_array_and_integer",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": 42},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when mixing array and integer values",
    ),
]

CONCATARRAYS_ERROR_TESTS = (
    CONCATARRAYS_ARITY_ERROR_TESTS
    + CONCATARRAYS_EXPRESSION_ERROR_TESTS
    + CONCATARRAYS_BSON_CONSTANT_ERROR_TESTS
    + CONCATARRAYS_NULL_ERROR_TESTS
    + CONCATARRAYS_TYPE_REJECTION_TESTS
    + CONCATARRAYS_MIXED_INVALID_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_ERROR_TESTS))
def test_accumulator_concatArrays_errors(collection, test_case):
    """Test $concatArrays error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
