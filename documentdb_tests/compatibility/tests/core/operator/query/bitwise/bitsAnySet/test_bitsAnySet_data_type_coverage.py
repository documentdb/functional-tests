"""
Tests for $bitsAnySet data type coverage.

Validates matching behavior across valid field types (int32, int64, double, Decimal128, BinData),
negative zero handling, numeric cross-type equivalence (int32/int64/double/Decimal128),
and core semantics (none set, empty array).

Invalid field type skips, non-representable value skips, and null/missing field handling
are covered by test_bitwise_common.py.
"""

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_NEGATIVE_ZERO

VALID_FIELD_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_field_any_set",
        filter={"a": {"$bitsAnySet": 35}},
        doc=[{"_id": 1, "a": 54}, {"_id": 2, "a": 0}],
        expected=[{"_id": 1, "a": 54}],
        msg="Int32 54 (110110): bit 5 of mask 35 (100011) is set → matches",
    ),
    QueryTestCase(
        id="int32_field_none_set_no_match",
        filter={"a": {"$bitsAnySet": 255}},
        doc=[{"_id": 1, "a": 0}],
        expected=[],
        msg="Int32 0 has no bits set → does not match",
    ),
    QueryTestCase(
        id="int32_field_all_set",
        filter={"a": {"$bitsAnySet": 255}},
        doc=[{"_id": 1, "a": 255}],
        expected=[{"_id": 1, "a": 255}],
        msg="Int32 255 has all bits 0-7 set → matches any non-zero bitmask",
    ),
    QueryTestCase(
        id="int64_field_any_set",
        filter={"a": {"$bitsAnySet": 35}},
        doc=[{"_id": 1, "a": Int64(54)}, {"_id": 2, "a": Int64(0)}],
        expected=[{"_id": 1, "a": Int64(54)}],
        msg="Int64 field with any bit set matches",
    ),
    QueryTestCase(
        id="double_field_whole_number",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[{"_id": 1, "a": 20.0}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 2, "a": 1.0}],
        msg="Double (integer-representable) field treated as integer; 1.0 has bit 0 set",
    ),
    QueryTestCase(
        id="decimal128_field_any_set",
        filter={"a": {"$bitsAnySet": 35}},
        doc=[
            {"_id": 1, "a": Decimal128("54")},
            {"_id": 2, "a": Decimal128("0")},
        ],
        expected=[{"_id": 1, "a": Decimal128("54")}],
        msg="Decimal128 integer value works like int",
    ),
    QueryTestCase(
        id="bindata_field_bit0_set",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[
            {"_id": 1, "a": Binary(b"\x06", 128)},
            {"_id": 2, "a": Binary(b"\x01", 128)},
        ],
        expected=[{"_id": 2, "a": Binary(b"\x01", 128)}],
        msg="BinData field with bit 0 set matches numeric bitmask",
    ),
    QueryTestCase(
        id="negative_zero_no_match",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[{"_id": 1, "a": DOUBLE_NEGATIVE_ZERO}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="Negative zero treated as integer 0, no bits set",
    ),
]

NUMERIC_EQUIVALENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="numeric_cross_type_equivalence",
        filter={"a": {"$bitsAnySet": [0, 1]}},
        doc=[
            {"_id": 1, "a": 20},
            {"_id": 2, "a": Int64(20)},
            {"_id": 3, "a": 20.0},
            {"_id": 4, "a": Decimal128("20")},
            {"_id": 5, "a": 3},
        ],
        expected=[{"_id": 5, "a": 3}],
        msg="Int32, Int64, Double, Decimal128 of value 20 have bits 0,1 clear; "
        "only 3 (11) has bits 0,1 set",
    ),
]

CORE_SEMANTICS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="any_set_none_queried_set",
        filter={"a": {"$bitsAnySet": 35}},
        doc=[{"_id": 1, "a": 220}],
        expected=[],
        msg="220 (11011100): none of mask 35 (100011) bits are set → no match",
    ),
    QueryTestCase(
        id="empty_array_no_match",
        filter={"a": {"$bitsAnySet": 1}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="Empty array field does not match",
    ),
]

ALL_TESTS = VALID_FIELD_TYPE_TESTS + NUMERIC_EQUIVALENCE_TESTS + CORE_SEMANTICS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_bitsAnySet_data_type_coverage(collection, test):
    """Test $bitsAnySet matching behavior across valid BSON field types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
