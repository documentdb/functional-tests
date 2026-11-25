"""Tests for $addToSet numeric equivalence, BSON type distinction, and NaN/Infinity.

Covers: numeric equivalence across int/long/double/decimal128, BSON type
distinction rules, NaN/Infinity handling, and negative zero equivalence.
"""

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

NUMERIC_EQUIVALENCE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_dup_of_int64",
        setup_docs=[{"_id": 1, "arr": [Int64(1)]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 1}},
        expected={"_id": 1, "arr": [Int64(1)]},
        msg="int32(1) should be duplicate of int64(1) due to numeric equivalence",
    ),
    UpdateTestCase(
        "double_dup_of_int32",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 1.0}},
        expected={"_id": 1, "arr": [1]},
        msg="double(1.0) should be duplicate of int32(1) due to numeric equivalence",
    ),
    UpdateTestCase(
        "decimal128_dup_of_int32",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("1")}},
        expected={"_id": 1, "arr": [1]},
        msg="Decimal128('1') should be duplicate of int32(1) due to numeric equivalence",
    ),
    UpdateTestCase(
        "int32_zero_dup_of_double_zero",
        setup_docs=[{"_id": 1, "arr": [0.0]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 0}},
        expected={"_id": 1, "arr": [0.0]},
        msg="int32(0) should be duplicate of double(0.0) due to numeric equivalence",
    ),
    UpdateTestCase(
        "int64_zero_dup_of_decimal128_zero",
        setup_docs=[{"_id": 1, "arr": [Decimal128("0")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Int64(0)}},
        expected={"_id": 1, "arr": [Decimal128("0")]},
        msg="int64(0) should be duplicate of Decimal128('0') due to numeric equivalence",
    ),
    UpdateTestCase(
        "int64_dup_of_decimal128",
        setup_docs=[{"_id": 1, "arr": [Decimal128("1")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Int64(1)}},
        expected={"_id": 1, "arr": [Decimal128("1")]},
        msg="Int64(1) should be duplicate of Decimal128('1') due to numeric equivalence",
    ),
    UpdateTestCase(
        "int64_dup_of_double",
        setup_docs=[{"_id": 1, "arr": [1.0]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Int64(1)}},
        expected={"_id": 1, "arr": [1.0]},
        msg="Int64(1) should be duplicate of double(1.0) due to numeric equivalence",
    ),
    UpdateTestCase(
        "decimal128_dup_of_double",
        setup_docs=[{"_id": 1, "arr": [1.0]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("1")}},
        expected={"_id": 1, "arr": [1.0]},
        msg="Decimal128('1') should be duplicate of double(1.0) due to numeric equivalence",
    ),
]
BSON_TYPE_DISTINCTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "false_not_dup_of_zero",
        setup_docs=[{"_id": 1, "arr": [0]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": False}},
        expected={"_id": 1, "arr": [0, False]},
        msg="false should not be duplicate of int(0) — distinct BSON types",
    ),
    UpdateTestCase(
        "true_not_dup_of_one",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": True}},
        expected={"_id": 1, "arr": [1, True]},
        msg="true should not be duplicate of int(1) — distinct BSON types",
    ),
    UpdateTestCase(
        "empty_string_not_dup_of_null",
        setup_docs=[{"_id": 1, "arr": [None]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": ""}},
        expected={"_id": 1, "arr": [None, ""]},
        msg="empty string should not be duplicate of null — distinct types",
    ),
    UpdateTestCase(
        "binary_equal_value_dedups",
        setup_docs=[{"_id": 1, "arr": [Binary(b"hello", 0)]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Binary(b"hello", 0)}},
        expected={"_id": 1, "arr": [b"hello"]},
        msg="Equal Binary (same subtype and payload) should dedup by value",
    ),
]

NAN_INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "add_float_nan",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("nan")}},
        expected={"_id": 1, "arr": [1, float("nan")]},
        msg="Should add float NaN to array",
    ),
    UpdateTestCase(
        "dup_float_nan",
        setup_docs=[{"_id": 1, "arr": [float("nan")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("nan")}},
        expected={"_id": 1, "arr": [float("nan")]},
        msg="Should detect float NaN as duplicate",
    ),
    UpdateTestCase(
        "add_decimal128_nan",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("NaN")}},
        expected={"_id": 1, "arr": [1, Decimal128("NaN")]},
        msg="Should add Decimal128 NaN to array",
    ),
    UpdateTestCase(
        "dup_decimal128_nan",
        setup_docs=[{"_id": 1, "arr": [Decimal128("NaN")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("NaN")}},
        expected={"_id": 1, "arr": [Decimal128("NaN")]},
        msg="Should detect Decimal128 NaN as duplicate",
    ),
    UpdateTestCase(
        "add_float_inf",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("inf")}},
        expected={"_id": 1, "arr": [1, float("inf")]},
        msg="Should add Infinity to array",
    ),
    UpdateTestCase(
        "dup_float_inf",
        setup_docs=[{"_id": 1, "arr": [float("inf")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("inf")}},
        expected={"_id": 1, "arr": [float("inf")]},
        msg="Should detect Infinity as duplicate",
    ),
    UpdateTestCase(
        "add_float_neg_inf",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("-inf")}},
        expected={"_id": 1, "arr": [1, float("-inf")]},
        msg="Should add -Infinity to array",
    ),
    UpdateTestCase(
        "add_decimal128_inf",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("Infinity")}},
        expected={"_id": 1, "arr": [1, Decimal128("Infinity")]},
        msg="Should add Decimal128 Infinity to array",
    ),
    UpdateTestCase(
        "add_decimal128_neg_inf",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("-Infinity")}},
        expected={"_id": 1, "arr": [1, Decimal128("-Infinity")]},
        msg="Should add Decimal128 -Infinity to array",
    ),
    UpdateTestCase(
        "float_nan_dup_of_decimal128_nan",
        setup_docs=[{"_id": 1, "arr": [Decimal128("NaN")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("nan")}},
        expected={"_id": 1, "arr": [Decimal128("NaN")]},
        msg="float NaN should be duplicate of Decimal128 NaN (cross-type equivalence)",
    ),
    UpdateTestCase(
        "float_inf_dup_of_decimal128_inf",
        setup_docs=[{"_id": 1, "arr": [Decimal128("Infinity")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("inf")}},
        expected={"_id": 1, "arr": [Decimal128("Infinity")]},
        msg="float Infinity should be duplicate of Decimal128 Infinity (cross-type equivalence)",
    ),
    UpdateTestCase(
        "dup_float_neg_inf",
        setup_docs=[{"_id": 1, "arr": [float("-inf")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": float("-inf")}},
        expected={"_id": 1, "arr": [float("-inf")]},
        msg="Should detect -Infinity as duplicate",
    ),
]

NEG_ZERO_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "neg_zero_dup_of_zero",
        setup_docs=[{"_id": 1, "arr": [0.0]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": -0.0}},
        expected={"_id": 1, "arr": [0.0]},
        msg="-0.0 should be treated as duplicate of 0.0",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_vs_zero",
        setup_docs=[{"_id": 1, "arr": [Decimal128("0")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("-0")}},
        expected={"_id": 1, "arr": [Decimal128("0")]},
        msg="Decimal128('-0') should be treated as duplicate of Decimal128('0')",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_dup_of_double_zero",
        setup_docs=[{"_id": 1, "arr": [0.0]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": Decimal128("-0")}},
        expected={"_id": 1, "arr": [0.0]},
        msg="Decimal128('-0') should be duplicate of double 0.0 (cross-type neg-zero)",
    ),
    UpdateTestCase(
        "int_zero_dup_of_decimal128_neg_zero",
        setup_docs=[{"_id": 1, "arr": [Decimal128("-0")]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 0}},
        expected={"_id": 1, "arr": [Decimal128("-0")]},
        msg="int(0) should be duplicate of Decimal128('-0') (cross-type neg-zero)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_INFINITY_TESTS))
def test_addToSet_nan_infinity(collection, test: UpdateTestCase):
    """Test $addToSet NaN and Infinity handling."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccessNaN(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize(
    "test",
    pytest_params(NUMERIC_EQUIVALENCE_TESTS + BSON_TYPE_DISTINCTION_TESTS + NEG_ZERO_TESTS),
)
def test_addToSet_data_types(collection, test: UpdateTestCase):
    """Test $addToSet data type handling, duplicate detection, and numeric equivalence."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
