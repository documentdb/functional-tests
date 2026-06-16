"""Tests for $pull operator data type handling.

Covers: numeric equivalence, BSON type distinction,
NaN/Infinity handling, and BSON ordering wiring.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

DATA_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int_removes_long_double_decimal",
        setup_docs=[{"_id": 1, "arr": [1, Int64(1), 1.0, Decimal128("1")]}],
        query={"_id": 1},
        update={"$pull": {"arr": 1}},
        expected={"_id": 1, "arr": []},
        msg="Should remove all numerically equivalent values (int, long, double, decimal128)",
    ),
    UpdateTestCase(
        "double_zero_removes_all_zeros",
        setup_docs=[{"_id": 1, "arr": [0, Int64(0), 0.0, Decimal128("0")]}],
        query={"_id": 1},
        update={"$pull": {"arr": 0.0}},
        expected={"_id": 1, "arr": []},
        msg="Should remove all numerically equivalent zeros",
    ),
    UpdateTestCase(
        "condition_gte_type_agnostic",
        setup_docs=[{"_id": 1, "arr": [Int64(3), 5.0, Decimal128("7"), 1]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$gte": 5}}},
        expected={"_id": 1, "arr": [Int64(3), 1]},
        msg="Should remove elements >= value regardless of numeric subtype",
    ),
    UpdateTestCase(
        "false_does_not_remove_int_zero",
        setup_docs=[{"_id": 1, "arr": [False, 0, Int64(0)]}],
        query={"_id": 1},
        update={"$pull": {"arr": False}},
        expected={"_id": 1, "arr": [0, Int64(0)]},
        msg="Should not remove int(0) when pulling false (BSON type distinction)",
    ),
    UpdateTestCase(
        "true_does_not_remove_int_one",
        setup_docs=[{"_id": 1, "arr": [True, 1, Int64(1)]}],
        query={"_id": 1},
        update={"$pull": {"arr": True}},
        expected={"_id": 1, "arr": [1, Int64(1)]},
        msg="Should not remove int(1) when pulling true (BSON type distinction)",
    ),
    UpdateTestCase(
        "null_removes_only_null",
        setup_docs=[{"_id": 1, "arr": [None, 0, "", False]}],
        query={"_id": 1},
        update={"$pull": {"arr": None}},
        expected={"_id": 1, "arr": [0, "", False]},
        msg="Should remove only null elements, not other falsy values",
    ),
    UpdateTestCase(
        "type_bool_removes_only_booleans",
        setup_docs=[{"_id": 1, "arr": [True, False, 0, 1, "true"]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$type": "bool"}}},
        expected={"_id": 1, "arr": [0, 1, "true"]},
        msg="Should remove only boolean elements with $type condition",
    ),
    UpdateTestCase(
        "gt_mixed_bson_types",
        setup_docs=[{"_id": 1, "arr": [1, 5, "hello", True, None, 10]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$gt": 3}}},
        expected={"_id": 1, "arr": [1, "hello", True, None]},
        msg="Should only compare within same BSON type for $gt on mixed types",
    ),
    UpdateTestCase(
        "lt_mixed_bson_types",
        setup_docs=[{"_id": 1, "arr": ["apple", "banana", "cherry", 5, None]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$lt": "cherry"}}},
        expected={"_id": 1, "arr": ["cherry", 5, None]},
        msg="Should only compare within same BSON type for $lt on mixed types",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATA_TYPE_TESTS))
def test_pull_data_types(collection, test: UpdateTestCase):
    """Test $pull data type handling: numeric equivalence, type distinction, BSON ordering."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


NAN_INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "pull_nan",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_NAN, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": FLOAT_NAN}},
        expected={"_id": 1, "arr": [1, 3]},
        msg="Should remove NaN elements from array",
    ),
    UpdateTestCase(
        "pull_decimal128_nan",
        setup_docs=[{"_id": 1, "arr": [1, DECIMAL128_NAN, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": DECIMAL128_NAN}},
        expected={"_id": 1, "arr": [1, 3]},
        msg="Should remove Decimal128 NaN elements",
    ),
    UpdateTestCase(
        "pull_infinity",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_INFINITY, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": FLOAT_INFINITY}},
        expected={"_id": 1, "arr": [1, 3]},
        msg="Should remove Infinity elements",
    ),
    UpdateTestCase(
        "pull_negative_infinity",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_NEGATIVE_INFINITY, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": FLOAT_NEGATIVE_INFINITY}},
        expected={"_id": 1, "arr": [1, 3]},
        msg="Should remove -Infinity elements",
    ),
    UpdateTestCase(
        "pull_negative_zero",
        setup_docs=[{"_id": 1, "arr": [1, DOUBLE_NEGATIVE_ZERO, 0.0, Int64(0), 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": DOUBLE_NEGATIVE_ZERO}},
        expected={"_id": 1, "arr": [1, 3]},
        msg="Should remove -0.0 and all numerically equivalent zeros (0.0, Int64(0))",
    ),
    UpdateTestCase(
        "pull_gt_nan_condition",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_NAN, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$gt": FLOAT_NAN}}},
        expected={"_id": 1, "arr": [1, FLOAT_NAN, 3]},
        msg="Should not remove any elements with $gt: NaN (NaN comparisons return false)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_INFINITY_TESTS))
def test_pull_nan_infinity(collection, test: UpdateTestCase):
    """Test $pull with NaN and Infinity values."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccessNaN(result, [test.expected], msg=test.msg)
