"""Tests for $limit core behavior and accepted numeric types."""

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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INT64_MAX,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_MAX_FITTING_INT64,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_PRECISION_LOSS,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MAX,
)

# Property [Core Behavior]: $limit passes at most N documents unchanged,
# returns zero documents on empty or non-existent collections without error,
# and works as the sole pipeline stage.
LIMIT_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "limit_one",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 1}],
        expected=[{"_id": 1}],
        msg="$limit 1 should return exactly one document",
    ),
    StageTestCase(
        "limit_basic",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 2}],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$limit should return at most N documents",
    ),
    StageTestCase(
        "limit_equals_docs",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 3}],
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="$limit equal to document count should return all documents",
    ),
    StageTestCase(
        "limit_exceeds_docs",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 100}],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$limit exceeding document count should return all documents",
    ),
    StageTestCase(
        "limit_nonexistent_collection",
        docs=None,
        pipeline=[{"$limit": 5}],
        expected=[],
        msg="$limit on a non-existent collection should return zero documents",
    ),
    StageTestCase(
        "limit_empty_collection",
        docs=[],
        pipeline=[{"$limit": 5}],
        expected=[],
        msg="$limit on empty collection should return zero documents",
    ),
]

# Property [Document Preservation]: documents pass through $limit completely
# unmodified - all BSON field types, nesting depths, and structures are
# preserved.
LIMIT_PRESERVATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "preserve_all_types",
        docs=[
            {
                "_id": 1,
                "str": "hello",
                "int": 42,
                "float": 3.14,
                "bool": True,
                "null": None,
                "arr": [1, [2, 3]],
                "obj": {"nested": {"deep": True}},
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "oid": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"),
                "bin": Binary(b"\x01\x02"),
                "ts": Timestamp(100, 1),
                "dec": DECIMAL128_TWO_AND_HALF,
                "i64": Int64(999),
                "regex": Regex("^abc"),
                "code": Code("function(){}"),
                "codews": Code("function(){}", {}),
                "minkey": MinKey(),
                "maxkey": MaxKey(),
            }
        ],
        pipeline=[{"$limit": 1}],
        expected=[
            {
                "_id": 1,
                "str": "hello",
                "int": 42,
                "float": 3.14,
                "bool": True,
                "null": None,
                "arr": [1, [2, 3]],
                "obj": {"nested": {"deep": True}},
                "date": datetime(2024, 1, 1),
                "oid": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"),
                "bin": b"\x01\x02",
                "ts": Timestamp(100, 1),
                "dec": DECIMAL128_TWO_AND_HALF,
                "i64": Int64(999),
                "regex": Regex("^abc"),
                "code": Code("function(){}"),
                "codews": Code("function(){}", {}),
                "minkey": MinKey(),
                "maxkey": MaxKey(),
            }
        ],
        msg="$limit should preserve all BSON field types unchanged",
    ),
]

# Property [Accepted Numeric Types]: $limit accepts int32, int64,
# whole-number double, and whole-number Decimal128 values, all producing
# identical results for the same integer value.
LIMIT_NUMERIC_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "int32_value",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 1}],
        expected=[{"_id": 1}],
        msg="$limit should accept int32",
    ),
    StageTestCase(
        "int64_value",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": Int64(1)}],
        expected=[{"_id": 1}],
        msg="$limit should accept int64",
    ),
    StageTestCase(
        "double_whole",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 1.0}],
        expected=[{"_id": 1}],
        msg="$limit should accept whole-number double",
    ),
    StageTestCase(
        "decimal128_whole",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": Decimal128("1")}],
        expected=[{"_id": 1}],
        msg="$limit should accept whole-number Decimal128",
    ),
    StageTestCase(
        "decimal128_trailing_zeros",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": Decimal128("1.00")}],
        expected=[{"_id": 1}],
        msg="$limit should accept Decimal128 with trailing zeros",
    ),
    StageTestCase(
        "decimal128_exponent",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": Decimal128("10E-1")}],
        expected=[{"_id": 1}],
        msg="$limit should accept Decimal128 with exponent resolving to whole number",
    ),
]

# Property [Boundary Values]: $limit accepts int32 max, values above int32
# max as int64, int64 max, and large double values within the int64 range.
LIMIT_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "int32_max",
        docs=[{"_id": 1}],
        pipeline=[{"$limit": INT32_MAX}],
        expected=[{"_id": 1}],
        msg="$limit should accept int32 max value",
    ),
    StageTestCase(
        "above_int32_max",
        docs=[{"_id": 1}],
        pipeline=[{"$limit": Int64(INT32_OVERFLOW)}],
        expected=[{"_id": 1}],
        msg="$limit should accept values above int32 max as int64",
    ),
    StageTestCase(
        "int64_max",
        docs=[{"_id": 1}],
        pipeline=[{"$limit": INT64_MAX}],
        expected=[{"_id": 1}],
        msg="$limit should accept int64 max value",
    ),
    StageTestCase(
        "double_2_pow_53",
        docs=[{"_id": 1}],
        pipeline=[{"$limit": float(DOUBLE_MAX_SAFE_INTEGER)}],
        expected=[{"_id": 1}],
        msg="$limit should accept max safe integer as double",
    ),
    StageTestCase(
        "double_largest_below_2_pow_63",
        docs=[{"_id": 1}],
        pipeline=[{"$limit": DOUBLE_MAX_FITTING_INT64}],
        expected=[{"_id": 1}],
        msg="$limit should accept the largest double less than 2^63",
    ),
    StageTestCase(
        "double_2_pow_53_plus_1_rounds",
        docs=[{"_id": 1}],
        pipeline=[{"$limit": float(DOUBLE_PRECISION_LOSS)}],
        expected=[{"_id": 1}],
        msg=(
            "$limit should accept float(2^53+1) because IEEE 754 rounds it"
            " to a whole-number double"
        ),
    ),
    StageTestCase(
        "decimal128_int64_max",
        docs=[{"_id": 1}],
        pipeline=[{"$limit": DECIMAL128_INT64_MAX}],
        expected=[{"_id": 1}],
        msg="$limit should accept Decimal128 at int64 max boundary",
    ),
]

# Property [Consecutive Limits]: consecutive $limit stages produce a count
# equal to the minimum of all limit values.
LIMIT_CONSECUTIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "consecutive_limits_min",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 4}, {"$limit": 2}],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="Consecutive $limit stages should produce min of all limit values",
    ),
    StageTestCase(
        "consecutive_limits_second_larger",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 2}, {"$limit": 4}],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="Consecutive $limit stages should produce min even when second is larger",
    ),
]

LIMIT_SUCCESS_TESTS = (
    LIMIT_CORE_TESTS
    + LIMIT_PRESERVATION_TESTS
    + LIMIT_NUMERIC_TYPE_TESTS
    + LIMIT_BOUNDARY_TESTS
    + LIMIT_CONSECUTIVE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LIMIT_SUCCESS_TESTS))
def test_limit_success(collection, test_case: StageTestCase):
    """Test $limit core behavior, numeric types, boundaries, and invariants."""
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
