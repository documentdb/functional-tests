"""Tests for $addToSet accumulator deduplication behavior."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [Document Duplicate Detection]: documents are duplicates only if they have
# exact same fields, values, and field order.
ADDTOSET_DOC_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "doc_identical",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 1, "b": 2}]}],
        msg="$addToSet should deduplicate identical documents",
    ),
    AccumulatorTestCase(
        "doc_different_field_order",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"b": 2, "a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"b": 2, "a": 1}, {"a": 1, "b": 2}]}],
        msg="$addToSet should treat documents with different field order as distinct",
    ),
    AccumulatorTestCase(
        "doc_different_values",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 3}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 1, "b": 2}, {"a": 1, "b": 3}]}],
        msg="$addToSet should treat documents with different values as distinct",
    ),
    AccumulatorTestCase(
        "doc_nested_identical",
        docs=[{"v": {"a": {"x": 1}}}, {"v": {"a": {"x": 1}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": {"x": 1}}]}],
        msg="$addToSet should deduplicate nested documents with identical structure",
    ),
    AccumulatorTestCase(
        "doc_nested_different_order",
        docs=[{"v": {"a": {"x": 1, "y": 2}}}, {"v": {"a": {"y": 2, "x": 1}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": {"x": 1, "y": 2}}, {"a": {"y": 2, "x": 1}}]}],
        msg="$addToSet should treat nested documents with different field order as distinct",
    ),
    AccumulatorTestCase(
        "doc_empty",
        docs=[{"v": {}}, {"v": {}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{}]}],
        msg="$addToSet should deduplicate empty documents",
    ),
    AccumulatorTestCase(
        "doc_subset",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1, "b": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 1, "b": 2}, {"a": 1}]}],
        msg="$addToSet should treat a document subset and superset as distinct",
    ),
    AccumulatorTestCase(
        "doc_with_array_value",
        docs=[{"v": {"a": [1, 2]}}, {"v": {"a": [1, 2]}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": [1, 2]}]}],
        msg="$addToSet should deduplicate documents containing identical array values",
    ),
    AccumulatorTestCase(
        "doc_with_null_value",
        docs=[{"v": {"a": None}}, {"v": {"a": None}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": None}]}],
        msg="$addToSet should deduplicate documents with null field values",
    ),
    AccumulatorTestCase(
        "doc_with_nested_null",
        docs=[{"v": {"a": {"b": None}}}, {"v": {"a": {"b": None}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": {"b": None}}]}],
        msg="$addToSet should deduplicate documents with nested null values",
    ),
]

# Property [String Deduplication]: strings are compared by byte value with no Unicode normalization.
ADDTOSET_STRING_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string_identical",
        docs=[{"v": "abc"}, {"v": "abc"}, {"v": "def"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["abc", "def"]}],
        msg="$addToSet should deduplicate identical strings",
    ),
    AccumulatorTestCase(
        "string_empty",
        docs=[{"v": ""}, {"v": ""}, {"v": "x"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["", "x"]}],
        msg="$addToSet should deduplicate empty strings",
    ),
    AccumulatorTestCase(
        "string_unicode_no_normalization",
        docs=[
            {"v": "\u00e9"},
            {"v": "\u0065\u0301"},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["\u00e9", "\u0065\u0301"]}],
        msg="$addToSet should not normalize Unicode; precomposed and decomposed are distinct",
    ),
    AccumulatorTestCase(
        "string_embedded_null_bytes",
        docs=[{"v": "a\x00b"}, {"v": "a\x00b"}, {"v": "a\x00c"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["a\x00b", "a\x00c"]}],
        msg="$addToSet should compare strings with embedded null bytes by byte value",
    ),
    AccumulatorTestCase(
        "string_4byte_utf8_emoji",
        docs=[{"v": "\U0001f600"}, {"v": "\U0001f600"}, {"v": "\U0001f601"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["\U0001f600", "\U0001f601"]}],
        msg="$addToSet should compare 4-byte UTF-8 characters (emoji) by byte value",
    ),
]

# Property [Mixed Type Collection]: $addToSet collects values of different
# BSON types in the same group.
ADDTOSET_MIXED_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_types",
        docs=[
            {"v": 42},
            {"v": "hello"},
            {"v": True},
            {"v": [1, 2]},
            {"v": {"a": 1}},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [42, "hello", True, [1, 2], {"a": 1}]}],
        msg="$addToSet should collect values of different BSON types in one group",
    ),
]

# Property [Numeric Equivalence]: numerically equivalent values across types are deduplicated.
ADDTOSET_NUMERIC_EQUIV_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_all_ones",
        docs=[{"v": 1}, {"v": Int64(1)}, {"v": 1.0}, {"v": Decimal128("1")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1]}],
        msg="$addToSet should deduplicate numerically equivalent values of all numeric types",
    ),
    AccumulatorTestCase(
        "equiv_all_zeros",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": 0.0}, {"v": Decimal128("0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [0]}],
        msg="$addToSet should deduplicate numerically equivalent zero values",
    ),
    AccumulatorTestCase(
        "equiv_int32_int64",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5]}],
        msg="$addToSet should deduplicate int32 and Int64 with same numeric value",
    ),
    AccumulatorTestCase(
        "equiv_double_int32",
        docs=[{"v": 3.0}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [3.0]}],
        msg="$addToSet should deduplicate double and int32 with same numeric value",
    ),
    AccumulatorTestCase(
        "equiv_decimal128_int64",
        docs=[{"v": Decimal128("100")}, {"v": Int64(100)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("100")]}],
        msg="$addToSet should deduplicate Decimal128 and Int64 with same numeric value",
    ),
    AccumulatorTestCase(
        "equiv_negative",
        docs=[{"v": -1}, {"v": Int64(-1)}, {"v": -1.0}, {"v": Decimal128("-1")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [-1]}],
        msg="$addToSet should deduplicate negative numerically equivalent values",
    ),
]

# Property [BSON Type Distinction]: values of different BSON types are distinct even when similar.
ADDTOSET_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [0, False]}],
        msg="$addToSet should treat false and int32(0) as distinct BSON types",
    ),
    AccumulatorTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, True]}],
        msg="$addToSet should treat true and int32(1) as distinct BSON types",
    ),
    AccumulatorTestCase(
        "distinct_null_vs_missing",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null but exclude missing field",
    ),
    AccumulatorTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["", None]}],
        msg="$addToSet should treat empty string and null as distinct",
    ),
    AccumulatorTestCase(
        "distinct_string_vs_number",
        docs=[{"v": "123"}, {"v": 123}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [123, "123"]}],
        msg="$addToSet should treat string '123' and int 123 as distinct",
    ),
]

# Property [NaN Deduplication]: NaN values are equal for deduplication purposes.
ADDTOSET_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_double_dedup",
        docs=[{"v": float("nan")}, {"v": float("nan")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [FLOAT_NAN]}],
        msg="$addToSet should deduplicate double NaN values",
    ),
    AccumulatorTestCase(
        "nan_decimal128_dedup",
        docs=[{"v": Decimal128("NaN")}, {"v": Decimal128("NaN")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("NaN")]}],
        msg="$addToSet should deduplicate Decimal128 NaN values",
    ),
    AccumulatorTestCase(
        "nan_cross_type",
        docs=[{"v": float("nan")}, {"v": Decimal128("NaN")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [FLOAT_NAN]}],
        msg="$addToSet should deduplicate float NaN and Decimal128 NaN as numerically equal",
    ),
    AccumulatorTestCase(
        "nan_with_finite",
        docs=[{"v": float("nan")}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [FLOAT_NAN, 5]}],
        msg="$addToSet should treat NaN and finite values as distinct",
    ),
]

# Property [Infinity Deduplication]: Infinity values are equal across numeric types.
ADDTOSET_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "inf_double_dedup",
        docs=[{"v": float("inf")}, {"v": float("inf")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("inf")]}],
        msg="$addToSet should deduplicate positive Infinity values",
    ),
    AccumulatorTestCase(
        "neg_inf_double_dedup",
        docs=[{"v": float("-inf")}, {"v": float("-inf")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("-inf")]}],
        msg="$addToSet should deduplicate negative Infinity values",
    ),
    AccumulatorTestCase(
        "inf_cross_type",
        docs=[{"v": float("inf")}, {"v": Decimal128("Infinity")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("inf")]}],
        msg="$addToSet should deduplicate float Infinity and Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "inf_vs_neg_inf",
        docs=[{"v": float("inf")}, {"v": float("-inf")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [float("-inf"), float("inf")]}],
        msg="$addToSet should treat positive and negative Infinity as distinct",
    ),
]

# Property [Negative Zero]: -0.0 and 0.0 are numerically equal and deduplicated.
ADDTOSET_NEG_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "neg_zero_double",
        docs=[{"v": -0.0}, {"v": 0.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [-0.0]}],
        msg="$addToSet should deduplicate -0.0 and 0.0 as numerically equal",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128",
        docs=[{"v": Decimal128("-0")}, {"v": Decimal128("0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("-0")]}],
        msg="$addToSet should deduplicate Decimal128 -0 and 0 as numerically equal",
    ),
    AccumulatorTestCase(
        "neg_zero_cross_type",
        docs=[{"v": -0.0}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [-0.0]}],
        msg="$addToSet should deduplicate -0.0 and int 0 as numerically equal",
    ),
]

# Property [Decimal128 Precision]: Decimal128 values with same numeric value but different
# representations are deduplicated.
ADDTOSET_DECIMAL128_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("1.0")]}],
        msg="$addToSet should deduplicate Decimal128 values with different trailing zeros",
    ),
    AccumulatorTestCase(
        "decimal_34_digit_precision",
        docs=[
            {"v": Decimal128("1.234567890123456789012345678901234")},
            {"v": Decimal128("1.234567890123456789012345678901234")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("1.234567890123456789012345678901234")]}],
        msg="$addToSet should deduplicate and preserve full 34-digit Decimal128 precision",
    ),
    AccumulatorTestCase(
        "decimal_max_min_distinct",
        docs=[
            {"v": Decimal128("9.999999999999999999999999999999999E+6144")},
            {"v": Decimal128("1E-6176")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[
            {
                "result": [
                    Decimal128("1E-6176"),
                    Decimal128("9.999999999999999999999999999999999E+6144"),
                ]
            }
        ],
        msg="$addToSet should treat Decimal128 max and min as distinct values",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

ADDTOSET_DEDUP_TESTS = (
    ADDTOSET_DOC_DEDUP_TESTS
    + ADDTOSET_STRING_DEDUP_TESTS
    + ADDTOSET_MIXED_TYPE_TESTS
    + ADDTOSET_NUMERIC_EQUIV_TESTS
    + ADDTOSET_TYPE_DISTINCTION_TESTS
    + ADDTOSET_NAN_TESTS
    + ADDTOSET_INFINITY_TESTS
    + ADDTOSET_NEG_ZERO_TESTS
    + ADDTOSET_DECIMAL128_PRECISION_TESTS
)

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_DEDUP_TESTS))
def test_accumulator_addToSet_dedup(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator deduplication behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccessNaN(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])
