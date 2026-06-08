"""Tests for $setUnion accumulator: type errors, null field errors, arity
rejection, mixed types, and expression error propagation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness]: each non-array BSON type as the field value must
# produce TYPE_MISMATCH_ERROR.
SETUNION_TYPE_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_error_int32",
        docs=[{"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject int32 field value",
    ),
    AccumulatorTestCase(
        "type_error_int64",
        docs=[{"v": Int64(42)}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject int64 field value",
    ),
    AccumulatorTestCase(
        "type_error_double",
        docs=[{"v": 3.14}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject double field value",
    ),
    AccumulatorTestCase(
        "type_error_decimal128",
        docs=[{"v": Decimal128("1.5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Decimal128 field value",
    ),
    AccumulatorTestCase(
        "type_error_string",
        docs=[{"v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject string field value",
    ),
    AccumulatorTestCase(
        "type_error_bool_true",
        docs=[{"v": True}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject boolean true field value",
    ),
    AccumulatorTestCase(
        "type_error_bool_false",
        docs=[{"v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject boolean false field value",
    ),
    AccumulatorTestCase(
        "type_error_object",
        docs=[{"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject embedded object field value",
    ),
    AccumulatorTestCase(
        "type_error_objectid",
        docs=[{"v": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject ObjectId field value",
    ),
    AccumulatorTestCase(
        "type_error_datetime",
        docs=[{"v": datetime(2023, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject datetime field value",
    ),
    AccumulatorTestCase(
        "type_error_timestamp",
        docs=[{"v": Timestamp(1, 1)}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Timestamp field value",
    ),
    AccumulatorTestCase(
        "type_error_binary",
        docs=[{"v": Binary(b"\x01\x02")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Binary field value",
    ),
    AccumulatorTestCase(
        "type_error_regex",
        docs=[{"v": Regex("abc", "i")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Regex field value",
    ),
    AccumulatorTestCase(
        "type_error_minkey",
        docs=[{"v": MinKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject MinKey field value",
    ),
    AccumulatorTestCase(
        "type_error_maxkey",
        docs=[{"v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject MaxKey field value",
    ),
    AccumulatorTestCase(
        "type_error_code",
        docs=[{"v": Code("function(){}")}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject Code (JavaScript) field value",
    ),
]

# Property [Mixed Array and Non-Array Error]: when a group contains a mix of
# array and non-array values, TYPE_MISMATCH_ERROR is produced.
SETUNION_MIXED_TYPE_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_array_first_then_non_array",
        docs=[{"v": [1, 2]}, {"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should error when array doc is followed by non-array doc",
    ),
    AccumulatorTestCase(
        "mixed_non_array_first_then_array",
        docs=[{"v": 42}, {"v": [1, 2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should error when non-array doc is followed by array doc",
    ),
]

# Property [Arity Rejection]: $setUnion accumulator in $group rejects array
# syntax and multi-key expression objects.
SETUNION_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$setUnion should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": [1]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$setUnion should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$setUnion should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": [1, 2, 3]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$setUnion should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": [1]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$add": [1, 2], "$multiply": [3, 4]}},
                }
            }
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$setUnion should reject multi-key expression object",
    ),
]

# Property [Null Field Error]: null field values cause TYPE_MISMATCH_ERROR in
# accumulator context.
SETUNION_NULL_FIELD_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_field_single_doc",
        docs=[{"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject null field value with TYPE_MISMATCH_ERROR",
    ),
    AccumulatorTestCase(
        "null_field_all_docs",
        docs=[{"v": None}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject when all documents have null field",
    ),
    AccumulatorTestCase(
        "null_field_mixed_with_array",
        docs=[{"v": [1, 2]}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject when any document has null field among arrays",
    ),
    AccumulatorTestCase(
        "null_field_before_array",
        docs=[{"v": None}, {"v": [1, 2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject null field regardless of document order",
    ),
]

# Property [Expression Error Propagation]: errors from sub-expressions propagate
# through $setUnion without being caught or suppressed.
SETUNION_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_prop_toint_non_convertible",
        docs=[{"v": "hello"}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$let": {
                                "vars": {"x": {"$toInt": "$v"}},
                                "in": ["$$x"],
                            }
                        }
                    },
                }
            },
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$setUnion should propagate $toInt conversion error for non-convertible value",
    ),
    AccumulatorTestCase(
        "error_prop_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$let": {
                                "vars": {"x": {"$divide": ["$v", 0]}},
                                "in": ["$$x"],
                            }
                        }
                    },
                }
            },
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$setUnion should propagate $divide by zero error",
    ),
    AccumulatorTestCase(
        "error_prop_divide_by_zero_field_path",
        docs=[{"_id": 0, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$let": {"vars": {}, "in": [{"$divide": [1, "$v"]}]}}},
                }
            },
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$setUnion should propagate $divide by zero when divisor comes from field path",
    ),
    AccumulatorTestCase(
        "error_prop_divide_by_zero_later_doc",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$let": {"vars": {}, "in": [{"$divide": [1, "$v"]}]}}},
                }
            },
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$setUnion should propagate error even when failing doc is not the first",
    ),
    AccumulatorTestCase(
        "error_prop_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$let": {
                                "vars": {"x": {"$mod": ["$v", 0]}},
                                "in": ["$$x"],
                            }
                        }
                    },
                }
            },
        ],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$setUnion should propagate $mod by zero error",
    ),
]

SETUNION_ERROR_TESTS = (
    SETUNION_TYPE_ERROR_TESTS
    + SETUNION_MIXED_TYPE_ERROR_TESTS
    + SETUNION_ARITY_ERROR_TESTS
    + SETUNION_NULL_FIELD_ERROR_TESTS
    + SETUNION_EXPRESSION_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_ERROR_TESTS))
def test_accumulator_setUnion_errors(collection, test_case):
    """Test $setUnion accumulator error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
