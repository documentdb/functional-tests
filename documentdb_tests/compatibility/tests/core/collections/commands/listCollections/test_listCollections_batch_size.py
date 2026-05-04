"""Tests for listCollections batchSize and cursor behavior."""

import uuid
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.target_collection import (
    ExtraCollections,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len, Ne
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Cursor batchSize Controls firstBatch]: cursor.batchSize
# controls the number of documents returned in firstBatch.
CURSOR_BATCH_SIZE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        id="batch_size_controls_first_batch",
        docs=[{"_id": 1}],
        command={"listCollections": 1, "cursor": {"batchSize": 2}},
        expected={"cursor.firstBatch": Len(2)},
        msg="batchSize=2 should return exactly 2 documents in firstBatch",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        id="batch_size_zero_opens_cursor",
        docs=[{"_id": 1}],
        command={"listCollections": 1, "cursor": {"batchSize": 0}},
        expected={"cursor.firstBatch": Len(0), "cursor.id": Ne(INT64_ZERO)},
        msg="batchSize=0 should produce empty firstBatch with open cursor",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        id="filter_applied_before_batching",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "listCollections": 1,
            "filter": {"name": ctx.collection},
            "cursor": {"batchSize": 1},
        },
        expected={"cursor.firstBatch": Len(1), "cursor.id": Eq(INT64_ZERO)},
        msg="Filter should be applied before batching; batchSize=1 with 1 match exhausts cursor",
    ),
]

# Property [batchSize Double Truncation]: double batchSize values are
# truncated toward zero before being applied.
BATCH_SIZE_DOUBLE_TRUNCATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="double_2_9",
        command={"listCollections": 1, "cursor": {"batchSize": 2.9}},
        expected={"cursor.firstBatch": Len(2)},
        msg="batchSize=2.9 should truncate to 2",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="double_1_5",
        command={"listCollections": 1, "cursor": {"batchSize": 1.5}},
        expected={"cursor.firstBatch": Len(1)},
        msg="batchSize=1.5 should truncate to 1",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="double_0_9",
        command={"listCollections": 1, "cursor": {"batchSize": 0.9}},
        expected={"cursor.firstBatch": Len(0)},
        msg="batchSize=0.9 should truncate to 0",
    ),
]

# Property [batchSize Decimal128 Banker Rounding]: Decimal128 batchSize
# values use banker's rounding (round half to even).
BATCH_SIZE_DECIMAL128_ROUNDING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_2_5",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_TWO_AND_HALF}},
        expected={"cursor.firstBatch": Len(2)},
        msg="batchSize=Decimal128('2.5') should round to 2 (banker's rounding)",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_2_9",
        command={"listCollections": 1, "cursor": {"batchSize": Decimal128("2.9")}},
        expected={"cursor.firstBatch": Len(3)},
        msg="batchSize=Decimal128('2.9') should round to 3",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_1_5",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_ONE_AND_HALF}},
        expected={"cursor.firstBatch": Len(2)},
        msg="batchSize=Decimal128('1.5') should round to 2 (banker's rounding)",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_0_9",
        command={"listCollections": 1, "cursor": {"batchSize": Decimal128("0.9")}},
        expected={"cursor.firstBatch": Len(1)},
        msg="batchSize=Decimal128('0.9') should round to 1",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_3_5",
        command={"listCollections": 1, "cursor": {"batchSize": Decimal128("3.5")}},
        expected={"cursor.firstBatch": Len(4)},
        msg="batchSize=Decimal128('3.5') should round to 4 (banker's rounding)",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_4_5",
        command={"listCollections": 1, "cursor": {"batchSize": Decimal128("4.5")}},
        expected={"cursor.firstBatch": Len(4)},
        msg="batchSize=Decimal128('4.5') should round to 4 (banker's rounding)",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_4_999",
        command={"listCollections": 1, "cursor": {"batchSize": Decimal128("4.999")}},
        expected={"cursor.firstBatch": Len(5)},
        msg="batchSize=Decimal128('4.999') should round to 5",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_0_5",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_HALF}},
        expected={"cursor.firstBatch": Len(0)},
        msg="batchSize=Decimal128('0.5') should round to 0 (banker's rounding)",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_0_1",
        command={"listCollections": 1, "cursor": {"batchSize": Decimal128("0.1")}},
        expected={"cursor.firstBatch": Len(0)},
        msg="batchSize=Decimal128('0.1') should round to 0",
    ),
]

# Property [batchSize Negative Fractional to Zero]: negative fractional
# values that truncate or round to zero are accepted as batchSize=0.
BATCH_SIZE_NEGATIVE_FRACTIONAL_ZERO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="double_neg_0_5",
        command={"listCollections": 1, "cursor": {"batchSize": -0.5}},
        expected={"cursor.firstBatch": Len(0)},
        msg="batchSize=-0.5 should truncate to 0",
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_neg_0_5",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_NEGATIVE_HALF}},
        expected={"cursor.firstBatch": Len(0)},
        msg="batchSize=Decimal128('-0.5') should round to 0",
    ),
]

BATCH_SIZE_FRACTIONAL_ROUNDING_TESTS: list[CommandTestCase] = (
    BATCH_SIZE_DOUBLE_TRUNCATION_TESTS
    + BATCH_SIZE_DECIMAL128_ROUNDING_TESTS
    + BATCH_SIZE_NEGATIVE_FRACTIONAL_ZERO_TESTS
)

# Property [batchSize Boundary Zero]: negative zero and NaN batchSize
# values are treated as 0 on listCollections, producing an empty
# firstBatch with the cursor left open.
BATCH_SIZE_BOUNDARY_ZERO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="double_negative_zero",
        command={"listCollections": 1, "cursor": {"batchSize": DOUBLE_NEGATIVE_ZERO}},
        msg="batchSize=-0.0 should be treated as 0",
        expected={"cursor.firstBatch": Len(0), "cursor.id": Ne(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_negative_zero",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_NEGATIVE_ZERO}},
        msg="batchSize=Decimal128('-0') should be treated as 0",
        expected={"cursor.firstBatch": Len(0), "cursor.id": Ne(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="float_nan",
        command={"listCollections": 1, "cursor": {"batchSize": FLOAT_NAN}},
        msg="batchSize=NaN (float) should be treated as 0",
        expected={"cursor.firstBatch": Len(0), "cursor.id": Ne(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_nan",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_NAN}},
        msg="batchSize=Decimal128('nan') should be treated as 0",
        expected={"cursor.firstBatch": Len(0), "cursor.id": Ne(INT64_ZERO)},
    ),
]

# Property [batchSize Infinity and Large Values Return All]: Infinity
# and large positive integer values are accepted as batchSize and
# return all results.
BATCH_SIZE_RETURN_ALL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="float_infinity",
        command={"listCollections": 1, "cursor": {"batchSize": FLOAT_INFINITY}},
        msg="batchSize=Infinity should return all results",
        expected={"ok": Eq(1.0), "cursor.id": Eq(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_infinity",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_INFINITY}},
        msg="batchSize=Decimal128('Infinity') should return all results",
        expected={"ok": Eq(1.0), "cursor.id": Eq(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="int32_max",
        command={"listCollections": 1, "cursor": {"batchSize": INT32_MAX}},
        msg="batchSize=INT32_MAX should return all results",
        expected={"ok": Eq(1.0), "cursor.id": Eq(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="int64_max",
        command={"listCollections": 1, "cursor": {"batchSize": INT64_MAX}},
        msg="batchSize=INT64_MAX should return all results",
        expected={"ok": Eq(1.0), "cursor.id": Eq(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="double_exceeding_int64_max",
        command={"listCollections": 1, "cursor": {"batchSize": DOUBLE_FROM_INT64_MAX}},
        msg="batchSize=double exceeding INT64_MAX should return all results",
        expected={"ok": Eq(1.0), "cursor.id": Eq(INT64_ZERO)},
    ),
    CommandTestCase(
        target_collection=ExtraCollections(count=5),
        docs=[{"_id": 1}],
        id="decimal128_large_exponent",
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_LARGE_EXPONENT}},
        msg="batchSize=Decimal128('1E+6144') should return all results",
        expected={"ok": Eq(1.0), "cursor.id": Eq(INT64_ZERO)},
    ),
]

# Property [batchSize Range Errors]: negative integer batchSize
# values produce BAD_VALUE_ERROR because the value after
# truncation/rounding must be >= 0.
BATCH_SIZE_RANGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listCollections": 1, "cursor": {"batchSize": -1}},
        msg="batchSize=-1 should produce BAD_VALUE_ERROR",
        id="neg_one",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "cursor": {"batchSize": -1.0}},
        msg="batchSize=-1.0 should produce BAD_VALUE_ERROR",
        id="neg_one_double",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "cursor": {"batchSize": INT32_MIN}},
        msg="batchSize=INT32_MIN should produce BAD_VALUE_ERROR",
        id="int32_min",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "cursor": {"batchSize": INT64_MIN}},
        msg="batchSize=INT64_MIN should produce BAD_VALUE_ERROR",
        id="int64_min",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "cursor": {"batchSize": FLOAT_NEGATIVE_INFINITY}},
        msg="batchSize=-Infinity should produce BAD_VALUE_ERROR",
        id="neg_infinity",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "cursor": {"batchSize": Decimal128("-1")}},
        msg="batchSize=Decimal128('-1') should produce BAD_VALUE_ERROR",
        id="decimal128_neg_one",
        error_code=BAD_VALUE_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "cursor": {"batchSize": DECIMAL128_NEGATIVE_INFINITY}},
        msg="batchSize=Decimal128('-Infinity') should produce BAD_VALUE_ERROR",
        id="decimal128_neg_infinity",
        error_code=BAD_VALUE_ERROR,
    ),
]

# Property [cursor Type Errors]: when cursor is a non-document BSON
# type, the command produces a TYPE_MISMATCH_ERROR.
CURSOR_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="cursor_bool",
        command={"listCollections": 1, "cursor": True},
        msg="cursor=bool should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_int32",
        command={"listCollections": 1, "cursor": 42},
        msg="cursor=int32 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_int64",
        command={"listCollections": 1, "cursor": Int64(42)},
        msg="cursor=Int64 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_double",
        command={"listCollections": 1, "cursor": 3.14},
        msg="cursor=double should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_decimal128",
        command={"listCollections": 1, "cursor": Decimal128("99")},
        msg="cursor=Decimal128 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_string",
        command={"listCollections": 1, "cursor": "hello"},
        msg="cursor=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_empty_array",
        command={"listCollections": 1, "cursor": []},
        msg="cursor=[] should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_array_doc",
        command={"listCollections": 1, "cursor": [{}]},
        msg="cursor=[{}] should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_array_int",
        command={"listCollections": 1, "cursor": [1]},
        msg="cursor=[1] should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_objectid",
        command=lambda _: {"listCollections": 1, "cursor": ObjectId()},
        msg="cursor=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_datetime",
        command={"listCollections": 1, "cursor": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="cursor=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_timestamp",
        command={"listCollections": 1, "cursor": Timestamp(1, 1)},
        msg="cursor=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_binary",
        command={"listCollections": 1, "cursor": Binary(b"hello")},
        msg="cursor=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_binary_uuid",
        command=lambda _: {"listCollections": 1, "cursor": Binary(uuid.uuid4().bytes, 4)},
        msg="cursor=Binary subtype 4 (UUID) should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_regex",
        command={"listCollections": 1, "cursor": Regex(".*")},
        msg="cursor=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_code",
        command={"listCollections": 1, "cursor": Code("function(){}")},
        msg="cursor=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_code_with_scope",
        command={"listCollections": 1, "cursor": Code("function(){}", {"x": 1})},
        msg="cursor=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_minkey",
        command={"listCollections": 1, "cursor": MinKey()},
        msg="cursor=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="cursor_maxkey",
        command={"listCollections": 1, "cursor": MaxKey()},
        msg="cursor=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

# Property [batchSize Type Errors]: when cursor.batchSize is a
# non-numeric BSON type, the command produces a TYPE_MISMATCH_ERROR.
BATCH_SIZE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="batch_size_bool",
        command={"listCollections": 1, "cursor": {"batchSize": True}},
        msg="batchSize=bool should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_string",
        command={"listCollections": 1, "cursor": {"batchSize": "hello"}},
        msg="batchSize=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_array",
        command={"listCollections": 1, "cursor": {"batchSize": [1]}},
        msg="batchSize=array should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_object",
        command={"listCollections": 1, "cursor": {"batchSize": {"a": 1}}},
        msg="batchSize=object should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_objectid",
        command=lambda _: {"listCollections": 1, "cursor": {"batchSize": ObjectId()}},
        msg="batchSize=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_datetime",
        command={
            "listCollections": 1,
            "cursor": {"batchSize": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        },
        msg="batchSize=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_timestamp",
        command={"listCollections": 1, "cursor": {"batchSize": Timestamp(1, 1)}},
        msg="batchSize=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_binary",
        command={"listCollections": 1, "cursor": {"batchSize": Binary(b"hello")}},
        msg="batchSize=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_binary_uuid",
        command=lambda _: {
            "listCollections": 1,
            "cursor": {"batchSize": Binary(uuid.uuid4().bytes, 4)},
        },
        msg="batchSize=Binary subtype 4 (UUID) should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_regex",
        command={"listCollections": 1, "cursor": {"batchSize": Regex(".*")}},
        msg="batchSize=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_code",
        command={"listCollections": 1, "cursor": {"batchSize": Code("function(){}")}},
        msg="batchSize=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_code_with_scope",
        command={"listCollections": 1, "cursor": {"batchSize": Code("function(){}", {"x": 1})}},
        msg="batchSize=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_minkey",
        command={"listCollections": 1, "cursor": {"batchSize": MinKey()}},
        msg="batchSize=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="batch_size_maxkey",
        command={"listCollections": 1, "cursor": {"batchSize": MaxKey()}},
        msg="batchSize=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

BATCH_SIZE_ALL_TESTS: list[CommandTestCase] = (
    CURSOR_BATCH_SIZE_TESTS
    + BATCH_SIZE_FRACTIONAL_ROUNDING_TESTS
    + BATCH_SIZE_BOUNDARY_ZERO_TESTS
    + BATCH_SIZE_RETURN_ALL_TESTS
    + BATCH_SIZE_RANGE_ERROR_TESTS
    + CURSOR_TYPE_ERROR_TESTS
    + BATCH_SIZE_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(BATCH_SIZE_ALL_TESTS))
def test_listCollections_batch_size(database_client, collection, test):
    """Test listCollections batchSize and cursor behavior."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
