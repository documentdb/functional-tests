from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SORT_ORDER_RANGE_ERROR,
    SORT_ORDER_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [Sort Order Value Type Errors]: non-numeric, non-object types as
# sort order values produce an error.
SORT_ORDER_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "type_error_string",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": "asc"}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a string as a sort order value",
    ),
    StageTestCase(
        "type_error_bool",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": True}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a boolean as a sort order value",
    ),
    StageTestCase(
        "type_error_null",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": None}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject null as a sort order value",
    ),
    StageTestCase(
        "type_error_array",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": [1]}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject an array as a sort order value",
    ),
    StageTestCase(
        "type_error_objectid",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": ObjectId("000000000000000000000001")}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject an ObjectId as a sort order value",
    ),
    StageTestCase(
        "type_error_datetime",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": datetime(2024, 1, 1, tzinfo=timezone.utc)}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a datetime as a sort order value",
    ),
    StageTestCase(
        "type_error_timestamp",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Timestamp(1, 1)}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a Timestamp as a sort order value",
    ),
    StageTestCase(
        "type_error_binary",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Binary(b"\x01")}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a Binary as a sort order value",
    ),
    StageTestCase(
        "type_error_regex",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Regex("a")}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a Regex as a sort order value",
    ),
    StageTestCase(
        "type_error_code",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Code("f")}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a Code as a sort order value",
    ),
    StageTestCase(
        "type_error_codewithscope",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Code("f", {"x": 1})}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject a CodeWithScope as a sort order value",
    ),
    StageTestCase(
        "type_error_minkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": MinKey()}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject MinKey as a sort order value",
    ),
    StageTestCase(
        "type_error_maxkey",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": MaxKey()}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should reject MaxKey as a sort order value",
    ),
]

# Property [Sort Order Value Range Errors]: numeric sort order values that
# are not equivalent to 1 or -1 after type-specific rounding produce an error.
SORT_ORDER_RANGE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "range_error_int_zero",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": 0}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject integer 0 as a sort order value",
    ),
    StageTestCase(
        "range_error_int_two",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": 2}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject integer 2 as a sort order value",
    ),
    StageTestCase(
        "range_error_int_neg_two",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": -2}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject integer -2 as a sort order value",
    ),
    StageTestCase(
        "range_error_double_zero",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DOUBLE_ZERO}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject double 0.0 as a sort order value",
    ),
    StageTestCase(
        "range_error_double_neg_zero",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DOUBLE_NEGATIVE_ZERO}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject double -0.0 as a sort order value",
    ),
    StageTestCase(
        "range_error_double_two",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": 2.0}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject double 2.0 as a sort order value",
    ),
    StageTestCase(
        "range_error_double_0_5",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": 0.5}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject double 0.5 as a sort order value",
    ),
    StageTestCase(
        "range_error_float_nan",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": FLOAT_NAN}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject float NaN as a sort order value",
    ),
    StageTestCase(
        "range_error_float_inf",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": FLOAT_INFINITY}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject float infinity as a sort order value",
    ),
    StageTestCase(
        "range_error_float_neg_inf",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": FLOAT_NEGATIVE_INFINITY}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject float negative infinity as a sort order value",
    ),
    # Decimal128 banker's rounding: abs(1.5) rounds to 2 (rejected).
    StageTestCase(
        "range_error_decimal128_1_5",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DECIMAL128_ONE_AND_HALF}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128('1.5') which rounds to 2",
    ),
    # Decimal128 banker's rounding: abs(0.5) rounds to 0 (rejected).
    StageTestCase(
        "range_error_decimal128_0_5",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DECIMAL128_HALF}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128('0.5') which rounds to 0",
    ),
    StageTestCase(
        "range_error_decimal128_neg_zero",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DECIMAL128_NEGATIVE_ZERO}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128('-0') as a sort order value",
    ),
    StageTestCase(
        "range_error_decimal128_nan",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DECIMAL128_NAN}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128 NaN as a sort order value",
    ),
    StageTestCase(
        "range_error_decimal128_inf",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DECIMAL128_INFINITY}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128 Infinity as a sort order value",
    ),
    StageTestCase(
        "range_error_decimal128_neg_inf",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": DECIMAL128_NEGATIVE_INFINITY}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128 negative Infinity as a sort order value",
    ),
    StageTestCase(
        "range_error_int64_zero",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": INT64_ZERO}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Int64 0 as a sort order value",
    ),
    StageTestCase(
        "range_error_int64_two",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Int64(2)}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Int64 2 as a sort order value",
    ),
    StageTestCase(
        "range_error_int64_neg_two",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Int64(-2)}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Int64 -2 as a sort order value",
    ),
    StageTestCase(
        "range_error_decimal128_two",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Decimal128("2")}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128 2 as a sort order value",
    ),
    StageTestCase(
        "range_error_decimal128_neg_two",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$sort": {"v": Decimal128("-2")}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should reject Decimal128 -2 as a sort order value",
    ),
]

# Property [Error Precedence]: sort order value errors take precedence over
# field path errors on the same key, and across multiple keys the first key's
# error is reported.
SORT_ERROR_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_range_over_field_path",
        docs=[{"_id": 1}],
        pipeline=[{"$sort": {"$a": 0}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should report range error over field path error on the same key",
    ),
    StageTestCase(
        "precedence_type_over_field_path",
        docs=[{"_id": 1}],
        pipeline=[{"$sort": {"$a": "asc"}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should report type error over field path error on the same key",
    ),
    StageTestCase(
        "precedence_first_key_range_over_second_type",
        docs=[{"_id": 1}],
        pipeline=[{"$sort": {"a": 0, "b": "asc"}}],
        error_code=SORT_ORDER_RANGE_ERROR,
        msg="$sort should report the first key's range error over the second key's type error",
    ),
    StageTestCase(
        "precedence_first_key_type_over_second_range",
        docs=[{"_id": 1}],
        pipeline=[{"$sort": {"a": "asc", "b": 0}}],
        error_code=SORT_ORDER_TYPE_ERROR,
        msg="$sort should report the first key's type error over the second key's range error",
    ),
]

SORT_ORDER_ERROR_TESTS = (
    SORT_ORDER_TYPE_ERROR_TESTS + SORT_ORDER_RANGE_ERROR_TESTS + SORT_ERROR_PRECEDENCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SORT_ORDER_ERROR_TESTS))
def test_sort_order_errors(collection, test_case: StageTestCase):
    """Test $sort order value type and range errors."""
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
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
