"""Tests for $lastN accumulator error cases: missing ``n`` and invalid ``n`` values.

$lastN requires an ``n`` argument that evaluates to a positive integer. A
missing ``n`` raises N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR (5787906);
any other invalid ``n`` -- zero, negative, or non-integer -- raises the generic
N_ACCUMULATOR_INVALID_N_ERROR (7548606)."""

from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    N_ACCUMULATOR_INVALID_N_ERROR,
    N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Missing n]: $lastN requires the ``n`` field in its argument object.
LASTN_MISSING_N_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_n",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
        msg="$lastN should reject an argument object that omits n",
    ),
]

# Property [Non-Positive n]: ``n`` must be greater than zero. Zero and negative
# values are rejected with N_ACCUMULATOR_INVALID_N_ERROR.
LASTN_NON_POSITIVE_N_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "n_zero",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 0, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject n = 0",
    ),
    AccumulatorTestCase(
        "n_negative",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": -1, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject a negative n",
    ),
]

# Property [Non-Integer n]: ``n`` must be integral. Fractional double and
# Decimal128 values are rejected with N_ACCUMULATOR_INVALID_N_ERROR.
LASTN_NON_INTEGER_N_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "n_non_integer_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2.5, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject a non-integer double n",
    ),
    AccumulatorTestCase(
        "n_non_integer_decimal128",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$lastN": {"n": Decimal128("1.5"), "input": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject a non-integer Decimal128 n",
    ),
]

LASTN_ERROR_TESTS = (
    LASTN_MISSING_N_ERROR_TESTS + LASTN_NON_POSITIVE_N_ERROR_TESTS + LASTN_NON_INTEGER_N_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LASTN_ERROR_TESTS))
def test_accumulator_lastN_errors(collection, test_case):
    """Test $lastN accumulator error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
