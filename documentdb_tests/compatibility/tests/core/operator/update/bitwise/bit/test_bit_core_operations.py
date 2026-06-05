"""Tests for $bit update operator core AND, OR, XOR operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MIN,
)


@dataclass(frozen=True)
class BitCoreTest(BaseTestCase):
    """Test case for $bit core operations."""

    field_value: Any = None
    bit_op: Any = None
    expected_value: Any = None


def run_bit_and_verify(collection, test: BitCoreTest):
    """Insert doc, run $bit update, return find result for verification."""
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


# Property [Bitwise AND/OR/XOR]: each operation produces the correct bitwise result
# for Int32 values including identity, idempotency, boundary, two's complement,
# and negative value cases.
TESTS: list[BitCoreTest] = [
    # AND operations
    BitCoreTest(
        "and_basic",
        field_value=13,
        bit_op={"and": 10},
        expected_value=8,
        msg="$bit should compute 1101 & 1010 = 1000.",
    ),
    BitCoreTest(
        "and_zero_mask",
        field_value=255,
        bit_op={"and": 0},
        expected_value=0,
        msg="$bit should produce 0 when AND mask is 0.",
    ),
    BitCoreTest(
        "and_identity",
        field_value=255,
        bit_op={"and": -1},
        expected_value=255,
        msg="$bit should preserve value when AND mask is -1 (all bits set).",
    ),
    BitCoreTest(
        "and_idempotent",
        field_value=255,
        bit_op={"and": 255},
        expected_value=255,
        msg="$bit should be idempotent when AND mask equals the value.",
    ),
    BitCoreTest(
        "and_low_nibble",
        field_value=255,
        bit_op={"and": 15},
        expected_value=15,
        msg="$bit should mask to low nibble with AND 0x0F.",
    ),
    # OR operations
    BitCoreTest(
        "or_basic",
        field_value=5,
        bit_op={"or": 3},
        expected_value=7,
        msg="$bit should compute 0101 | 0011 = 0111.",
    ),
    BitCoreTest(
        "or_identity",
        field_value=5,
        bit_op={"or": 0},
        expected_value=5,
        msg="$bit should preserve value when OR operand is 0.",
    ),
    BitCoreTest(
        "or_all_bits",
        field_value=5,
        bit_op={"or": -1},
        expected_value=-1,
        msg="$bit should produce -1 when OR operand is -1 (all bits set).",
    ),
    BitCoreTest(
        "or_from_zero",
        field_value=0,
        bit_op={"or": 255},
        expected_value=255,
        msg="$bit should produce operand value when OR on 0.",
    ),
    # XOR operations
    BitCoreTest(
        "xor_basic",
        field_value=5,
        bit_op={"xor": 3},
        expected_value=6,
        msg="$bit should compute 0101 ^ 0011 = 0110.",
    ),
    BitCoreTest(
        "xor_identity",
        field_value=5,
        bit_op={"xor": 0},
        expected_value=5,
        msg="$bit should preserve value when XOR operand is 0.",
    ),
    BitCoreTest(
        "xor_self_produces_zero",
        field_value=5,
        bit_op={"xor": 5},
        expected_value=0,
        msg="$bit should produce 0 when XOR operand equals the value.",
    ),
    BitCoreTest(
        "xor_bitwise_not",
        field_value=10,
        bit_op={"xor": -1},
        expected_value=-11,
        msg="$bit should compute bitwise NOT via XOR with -1.",
    ),
    # Int32 boundary values
    BitCoreTest(
        "boundary_int32_max_and_identity",
        field_value=INT32_MAX,
        bit_op={"and": -1},
        expected_value=INT32_MAX,
        msg="$bit should preserve INT32_MAX when AND mask is -1.",
    ),
    BitCoreTest(
        "boundary_int32_min_and_identity",
        field_value=INT32_MIN,
        bit_op={"and": -1},
        expected_value=INT32_MIN,
        msg="$bit should preserve INT32_MIN when AND mask is -1.",
    ),
    BitCoreTest(
        "boundary_int32_max_and_zero",
        field_value=INT32_MAX,
        bit_op={"and": 0},
        expected_value=0,
        msg="$bit should produce 0 when AND mask is 0 on INT32_MAX.",
    ),
    BitCoreTest(
        "boundary_int32_min_and_zero",
        field_value=INT32_MIN,
        bit_op={"and": 0},
        expected_value=0,
        msg="$bit should produce 0 when AND mask is 0 on INT32_MIN.",
    ),
    BitCoreTest(
        "boundary_int32_max_xor_flip",
        field_value=INT32_MAX,
        bit_op={"xor": -1},
        expected_value=INT32_MIN,
        msg="$bit should flip INT32_MAX to INT32_MIN via XOR -1.",
    ),
    BitCoreTest(
        "boundary_int32_min_xor_flip",
        field_value=INT32_MIN,
        bit_op={"xor": -1},
        expected_value=INT32_MAX,
        msg="$bit should flip INT32_MIN to INT32_MAX via XOR -1.",
    ),
    # Two's complement verification
    BitCoreTest(
        "twos_and_neg1_low_byte",
        field_value=-1,
        bit_op={"and": 0xFF},
        expected_value=255,
        msg="$bit should extract lower 8 bits from -1 (all 1s) via AND 0xFF.",
    ),
    BitCoreTest(
        "twos_and_neg256_low_byte",
        field_value=-256,
        bit_op={"and": 0xFF},
        expected_value=0,
        msg="$bit should extract lower 8 bits from -256 (all 0s) via AND 0xFF.",
    ),
    BitCoreTest(
        "twos_or_sign_bit",
        field_value=0,
        bit_op={"or": INT32_MIN},
        expected_value=INT32_MIN,
        msg="$bit should produce INT32_MIN when OR sets the sign bit on 0.",
    ),
    BitCoreTest(
        "twos_xor_sign_bit",
        field_value=1,
        bit_op={"xor": INT32_MIN},
        expected_value=-2_147_483_647,
        msg="$bit should flip sign bit on 1 via XOR with INT32_MIN.",
    ),
    # Negative value operations
    BitCoreTest(
        "neg_and_self_idempotent",
        field_value=-10,
        bit_op={"and": -10},
        expected_value=-10,
        msg="$bit should be idempotent when AND operand is the same negative value.",
    ),
    BitCoreTest(
        "neg_or_all_bits",
        field_value=10,
        bit_op={"or": -1},
        expected_value=-1,
        msg="$bit should produce -1 when OR operand is -1 on any value.",
    ),
    BitCoreTest(
        "neg_xor_all_ones_produces_zero",
        field_value=-1,
        bit_op={"xor": -1},
        expected_value=0,
        msg="$bit should produce 0 when XOR -1 on -1.",
    ),
    # Zero operations
    BitCoreTest(
        "zero_and_zero",
        field_value=0,
        bit_op={"and": 0},
        expected_value=0,
        msg="$bit should produce 0 for AND 0 on 0.",
    ),
    BitCoreTest(
        "zero_or_zero",
        field_value=0,
        bit_op={"or": 0},
        expected_value=0,
        msg="$bit should produce 0 for OR 0 on 0.",
    ),
    BitCoreTest(
        "zero_xor_zero",
        field_value=0,
        bit_op={"xor": 0},
        expected_value=0,
        msg="$bit should produce 0 for XOR 0 on 0.",
    ),
    # Bit manipulation patterns
    BitCoreTest(
        "set_bit_0",
        field_value=0,
        bit_op={"or": 1},
        expected_value=1,
        msg="$bit should set bit 0 via OR 1.",
    ),
    BitCoreTest(
        "set_bit_7",
        field_value=0,
        bit_op={"or": 128},
        expected_value=128,
        msg="$bit should set bit 7 via OR 128.",
    ),
    BitCoreTest(
        "clear_bit_0",
        field_value=255,
        bit_op={"and": -2},
        expected_value=254,
        msg="$bit should clear bit 0 via AND ~1.",
    ),
    BitCoreTest(
        "clear_bit_7",
        field_value=255,
        bit_op={"and": -129},
        expected_value=127,
        msg="$bit should clear bit 7 via AND ~128.",
    ),
    BitCoreTest(
        "toggle_bit_0_on",
        field_value=0,
        bit_op={"xor": 1},
        expected_value=1,
        msg="$bit should toggle bit 0 from 0 to 1 via XOR 1.",
    ),
    BitCoreTest(
        "toggle_bit_0_off",
        field_value=1,
        bit_op={"xor": 1},
        expected_value=0,
        msg="$bit should toggle bit 0 from 1 to 0 via XOR 1.",
    ),
    # Multiple operations on same field (and + or combined).
    BitCoreTest(
        "combined_and_or_same_field",
        field_value=255,
        bit_op={"and": 15, "or": 16},
        expected_value=31,
        msg="$bit should apply AND then OR on same field: (255 & 15) | 16 = 31.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_bit_core(collection, test: BitCoreTest):
    """Test $bit core AND/OR/XOR operations."""
    result = run_bit_and_verify(collection, test)
    assertSuccess(
        result,
        [{"_id": 1, "v": test.expected_value}],
        msg=test.msg,
    )
