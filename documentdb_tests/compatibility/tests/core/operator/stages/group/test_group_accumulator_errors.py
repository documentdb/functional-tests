"""Aggregation $group stage tests - accumulator error cases."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import SON, Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
    BUCKET_OUTPUT_DOT_ERROR,
    BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    GROUP_ACCUMULATOR_MULTIPLE_KEYS_ERROR,
    GROUP_UNKNOWN_OPERATOR_ERROR,
    MERGE_OBJECTS_NON_OBJECT_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Accumulator Null and Missing - Error Cases]: $mergeObjects errors
# on non-object input, and $setUnion and $concatArrays error on null or
# non-array input.
GROUP_ACCUMULATOR_NULL_MISSING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="mergeobjects_non_object_error",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$group": {"_id": None, "r": {"$mergeObjects": "$v"}}}],
        error_code=MERGE_OBJECTS_NON_OBJECT_ERROR,
        msg="$mergeObjects should error on non-object input",
    ),
    StageTestCase(
        id="setunion_null_error",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$group": {"_id": None, "r": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should error on null input",
    ),
    StageTestCase(
        id="setunion_non_array_error",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$group": {"_id": None, "r": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should error on non-array input",
    ),
    StageTestCase(
        id="concatarrays_null_error",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$group": {"_id": None, "r": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null input",
    ),
    StageTestCase(
        id="concatarrays_non_array_error",
        docs=[{"_id": 1, "v": 42}],
        pipeline=[{"$group": {"_id": None, "r": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on non-array input",
    ),
]

# Property [Accumulator Field Name Errors]: $-prefixed accumulator field
# names and dot-containing accumulator field names are rejected.
GROUP_ACCUMULATOR_FIELD_NAME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accumulator_dollar_prefix_field_name",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "$bad": {"$sum": 1}}}],
        error_code=BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
        msg="$-prefixed accumulator field name should produce an error",
    ),
    StageTestCase(
        id="accumulator_dot_field_name",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "a.b": {"$sum": 1}}}],
        error_code=BUCKET_OUTPUT_DOT_ERROR,
        msg="Dot-containing accumulator field name should produce an error",
    ),
]

# Property [Accumulator Non-Object Value Rejection]: all non-object BSON
# types, empty objects, objects with a non-$-prefixed key, and objects with an
# empty string key as accumulator field value produce an error.
GROUP_ACCUMULATOR_NON_OBJECT_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accum_value_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": 1}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="int32 as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": Int64(1)}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Int64 as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_double",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": 1.5}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="double as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": Decimal128("1")}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Decimal128 as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_string",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": "hello"}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="string as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": True}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="bool as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_null",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": None}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="null as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_array",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": [1, 2]}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="array as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": ObjectId("507f1f77bcf86cd799439011")}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="ObjectId as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": datetime(2024, 1, 1)}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="datetime as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": Timestamp(1, 1)}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Timestamp as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": Binary(b"data")}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Binary as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": Regex("abc", "i")}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Regex as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_code",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": Code("function(){}")}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Code as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": MinKey()}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="MinKey as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": MaxKey()}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="MaxKey as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_empty_object",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {}}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Empty object as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_non_dollar_key",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"bad": 1}}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Object with non-$-prefixed key as accumulator value should produce an error",
    ),
    StageTestCase(
        id="accum_value_empty_string_key",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"": 1}}}],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="Object with empty string key as accumulator value should produce an error",
    ),
]

# Property [Accumulator Array Argument Rejection]: array literal arguments to
# accumulators and non-accumulator expressions with array arguments in
# accumulator position produce an error.
GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accum_array_arg_sum",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": [1, 2]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$sum with array literal argument should produce an error",
    ),
    StageTestCase(
        id="accum_array_arg_non_accumulator",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$add": [1, 2]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="Non-accumulator expression with array argument should produce an error",
    ),
]

# Property [Accumulator Unknown Operator Rejection]: bare $, $$-prefixed keys,
# unknown $-prefixed operators, and non-accumulator expressions with non-array
# arguments in accumulator position produce an error.
GROUP_ACCUMULATOR_UNKNOWN_OPERATOR_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accum_non_accumulator_non_array",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$add": 1}}}],
        error_code=GROUP_UNKNOWN_OPERATOR_ERROR,
        msg="Non-accumulator expression with non-array argument should produce an error",
    ),
    StageTestCase(
        id="accum_bare_dollar",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$": 1}}}],
        error_code=GROUP_UNKNOWN_OPERATOR_ERROR,
        msg="Bare $ as accumulator key should produce an error",
    ),
    StageTestCase(
        id="accum_double_dollar_key",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$$ROOT": 1}}}],
        error_code=GROUP_UNKNOWN_OPERATOR_ERROR,
        msg="$$-prefixed key in accumulator object should produce an error",
    ),
    StageTestCase(
        id="accum_unknown_dollar_op",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$fakeOp": 1}}}],
        error_code=GROUP_UNKNOWN_OPERATOR_ERROR,
        msg="Unknown $-prefixed operator should produce an error",
    ),
]

# Property [Accumulator Multiple Keys Rejection]: mixed $-prefixed and
# non-$-prefixed keys or multiple $-prefixed keys in an accumulator object
# produce an error.
GROUP_ACCUMULATOR_MULTIPLE_KEYS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="accum_mixed_keys",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": SON([("$sum", 1), ("extra", 2)])}}],
        error_code=GROUP_ACCUMULATOR_MULTIPLE_KEYS_ERROR,
        msg="Mixed $-prefixed and non-$-prefixed keys should produce an error",
    ),
    StageTestCase(
        id="accum_multiple_dollar_keys",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "r": SON([("$sum", 1), ("$avg", "$v")]),
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_MULTIPLE_KEYS_ERROR,
        msg="Multiple $-prefixed keys in accumulator object should produce an error",
    ),
]

# Property [$count Non-Empty Argument]: $count rejects any non-empty
# argument with an error.
GROUP_COUNT_ACCUMULATOR_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="count_with_string_argument",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$count": "hello"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$count with a non-empty string argument should produce an error",
    ),
    StageTestCase(
        id="count_with_empty_array_argument",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": None, "r": {"$count": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$count with an empty array argument should produce an error",
    ),
]

GROUP_ACCUMULATOR_ERROR_TESTS = (
    GROUP_ACCUMULATOR_NULL_MISSING_ERROR_TESTS
    + GROUP_ACCUMULATOR_FIELD_NAME_ERROR_TESTS
    + GROUP_ACCUMULATOR_NON_OBJECT_VALUE_ERROR_TESTS
    + GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR_TESTS
    + GROUP_ACCUMULATOR_UNKNOWN_OPERATOR_ERROR_TESTS
    + GROUP_ACCUMULATOR_MULTIPLE_KEYS_ERROR_TESTS
    + GROUP_COUNT_ACCUMULATOR_VALIDATION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_ACCUMULATOR_ERROR_TESTS))
def test_group_accumulator_error(collection, test_case: StageTestCase):
    """Test $group stage accumulator error cases."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
