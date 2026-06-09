"""Tests for $bit update operator type preservation and cross-type promotion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)


@dataclass(frozen=True)
class BitPromotionTest(BaseTestCase):
    """Test case for $bit type promotion."""

    field_value: Any = None
    bit_op: Any = None
    expected_value: Any = None


def run_bit_promotion(collection, test: BitPromotionTest):
    """Insert, run $bit, return find result."""
    collection.insert_one({"_id": 1, "v": test.field_value})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$bit": {"v": test.bit_op}}}],
        },
    )
    return execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}},
    )


# Property [Type Promotion]: $bit preserves the wider integer type between field and
# operand. Int32 + Int32 stays Int32, Int64 + Int64 stays Int64, and any Int64 operand
# promotes an Int32 field result to Int64.
TESTS: list[BitPromotionTest] = [
    # Type preservation: same type in, same type out.
    BitPromotionTest(
        "int32_stays_int32",
        field_value=255,
        bit_op={"and": 0xFF},
        expected_value=255,
        msg="$bit should produce Int32 when both field and operand are Int32.",
    ),
    BitPromotionTest(
        "int64_stays_int64",
        field_value=Int64(255),
        bit_op={"and": Int64(0xFF)},
        expected_value=Int64(255),
        msg="$bit should produce Int64 when both field and operand are Int64.",
    ),
    BitPromotionTest(
        "int64_or_stays_int64",
        field_value=Int64(0),
        bit_op={"or": Int64(1)},
        expected_value=Int64(1),
        msg="$bit should produce Int64 for Int64 OR Int64.",
    ),
    BitPromotionTest(
        "int64_zero_result_stays_int64",
        field_value=Int64(0),
        bit_op={"or": Int64(0)},
        expected_value=Int64(0),
        msg="$bit should not demote Int64(0) result to Int32.",
    ),
    # Cross-type: Int64 operand promotes Int32 field.
    BitPromotionTest(
        "int32_field_int64_operand_and",
        field_value=255,
        bit_op={"and": Int64(15)},
        expected_value=Int64(15),
        msg="$bit should promote Int32 field to Int64 when operand is Int64.",
    ),
    BitPromotionTest(
        "int32_field_int64_operand_xor",
        field_value=1,
        bit_op={"xor": Int64(3)},
        expected_value=Int64(2),
        msg="$bit should promote Int32 field XOR result to Int64 when operand is Int64.",
    ),
    BitPromotionTest(
        "int32_max_with_int64_operand",
        field_value=INT32_MAX,
        bit_op={"and": Int64(INT32_MAX)},
        expected_value=Int64(INT32_MAX),
        msg="$bit should promote INT32_MAX result to Int64 when operand is Int64.",
    ),
    # Cross-type: Int32 operand on Int64 field stays Int64.
    BitPromotionTest(
        "int64_field_int32_operand_or",
        field_value=Int64(5),
        bit_op={"or": 3},
        expected_value=Int64(7),
        msg="$bit should keep Int64 field type when operand is Int32.",
    ),
    BitPromotionTest(
        "int64_field_int32_operand_and",
        field_value=Int64(255),
        bit_op={"and": 15},
        expected_value=Int64(15),
        msg="$bit should keep Int64 field type for AND with Int32 operand.",
    ),
    BitPromotionTest(
        "int64_max_with_int32_operand",
        field_value=INT64_MAX,
        bit_op={"or": 1},
        expected_value=INT64_MAX,
        msg="$bit should keep Int64 type when OR Int32(1) on INT64_MAX.",
    ),
    # Int32 dataset tests: verify correct results across Int32 boundary values.
    BitPromotionTest(
        "int32_dataset_min_and_0xff",
        field_value=INT32_MIN,
        bit_op={"and": 0xFF},
        expected_value=0,
        msg="$bit should compute INT32_MIN & 0xFF = 0.",
    ),
    BitPromotionTest(
        "int32_dataset_zero_or_0xff",
        field_value=INT32_ZERO,
        bit_op={"or": 0xFF},
        expected_value=0xFF,
        msg="$bit should compute 0 | 0xFF = 255.",
    ),
    BitPromotionTest(
        "int32_dataset_max_xor_0xff",
        field_value=INT32_MAX,
        bit_op={"xor": 0xFF},
        expected_value=INT32_MAX ^ 0xFF,
        msg="$bit should compute INT32_MAX ^ 0xFF correctly.",
    ),
    # Int64 dataset tests: verify correct results across Int64 boundary values.
    BitPromotionTest(
        "int64_dataset_min_and_0xff",
        field_value=INT64_MIN,
        bit_op={"and": Int64(0xFF)},
        expected_value=Int64(0),
        msg="$bit should compute INT64_MIN & 0xFF = 0.",
    ),
    BitPromotionTest(
        "int64_dataset_zero_or_0xff",
        field_value=INT64_ZERO,
        bit_op={"or": Int64(0xFF)},
        expected_value=Int64(0xFF),
        msg="$bit should compute Int64(0) | 0xFF = Int64(255).",
    ),
    BitPromotionTest(
        "int64_dataset_max_xor_0xff",
        field_value=INT64_MAX,
        bit_op={"xor": Int64(0xFF)},
        expected_value=Int64(int(INT64_MAX) ^ 0xFF),
        msg="$bit should compute INT64_MAX ^ 0xFF correctly.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_bit_type_promotion(collection, test: BitPromotionTest):
    """Test $bit type promotion and preservation between Int32 and Int64."""
    result = run_bit_promotion(collection, test)
    assertSuccess(result, [{"_id": 1, "v": test.expected_value}], msg=test.msg)
