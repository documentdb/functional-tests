"""Tests for $lastN accumulator error cases: malformed specification, missing
arguments, and invalid ``n`` values.

$lastN takes an object with exactly the fields ``n`` and ``input``, where ``n``
must evaluate to a positive integer.

Two divergences from the array-expression form in expressions/array/lastN/: this
form collapses invalid-``n`` into the generic 7548606, and reports 40237 rather
than 5787801 for an array specification.

The missing/zero/negative ``n`` cases intentionally overlap
stages/group/test_group_n_accumulator_errors.py, which sweeps those values across
all six N-accumulators."""

from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    N_ACCUMULATOR_INVALID_N_ERROR,
    N_ACCUMULATOR_MISSING_INPUT_FIRSTN_FAMILY_ERROR,
    N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
    N_ACCUMULATOR_SPEC_NOT_OBJECT_ERROR,
    N_ACCUMULATOR_UNKNOWN_ARGUMENT_ERROR,
    OUT_OF_RANGE_CONVERSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, FLOAT_NAN

# These cases fail at pipeline parse time, before any document is read, so one
# document and a bare $group stage are sufficient.
DOCS: list[dict] = [{"_id": 0, "v": 1}]

# Property [Malformed Specification]: the argument must be an object containing
# only the known n / input fields. A scalar argument is a bad specification; an
# array argument is a unary-operator violation.
LASTN_MALFORMED_SPEC_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "spec_not_object",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": 5}}}],
        error_code=N_ACCUMULATOR_SPEC_NOT_OBJECT_ERROR,
        msg="$lastN should reject a scalar (non-object) specification",
    ),
    AccumulatorTestCase(
        "spec_array",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": [1, 2]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$lastN should reject array syntax in accumulator context",
    ),
    AccumulatorTestCase(
        "unknown_argument",
        docs=DOCS,
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$lastN": {"n": 2, "input": "$v", "extra": 1}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_UNKNOWN_ARGUMENT_ERROR,
        msg="$lastN should reject an unknown argument field rather than ignoring it",
    ),
]

# Property [Missing input]: the mirror of [Missing n]. The error code is shared
# by the firstN family ($firstN/$lastN/$minN/$maxN); there is no $lastN-specific
# one.
LASTN_MISSING_INPUT_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_input",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": {"n": 2}}}}],
        error_code=N_ACCUMULATOR_MISSING_INPUT_FIRSTN_FAMILY_ERROR,
        msg="$lastN should reject an argument object that omits input",
    ),
]

# Property [Missing n]: $lastN requires the ``n`` field in its argument object.
LASTN_MISSING_N_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_n",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": {"input": "$v"}}}}],
        error_code=N_ACCUMULATOR_MISSING_N_FIRSTN_FAMILY_ERROR,
        msg="$lastN should reject an argument object that omits n",
    ),
]

# Property [Non-Positive n]: ``n`` must be greater than zero. Zero and negative
# values are rejected with N_ACCUMULATOR_INVALID_N_ERROR.
LASTN_NON_POSITIVE_N_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "n_zero",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": {"n": 0, "input": "$v"}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject n = 0",
    ),
    AccumulatorTestCase(
        "n_negative",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": {"n": -1, "input": "$v"}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject a negative n",
    ),
    AccumulatorTestCase(
        "n_expression_negative",
        docs=DOCS,
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$lastN": {"n": {"$add": [1, -3]}, "input": "$v"}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should validate n after evaluating it as an expression",
    ),
]

# Property [Non-Coercible n]: NaN, infinity, and out-of-range doubles fail during
# conversion to a 64-bit integer, not with the generic invalid-n code.
LASTN_NON_COERCIBLE_N_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "n_out_of_range_double",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": {"n": 1e19, "input": "$v"}}}}],
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$lastN should reject an n too large to coerce to a 64-bit integer",
    ),
    AccumulatorTestCase(
        "n_nan",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": {"n": FLOAT_NAN, "input": "$v"}}}}],
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$lastN should reject NaN as n",
    ),
    AccumulatorTestCase(
        "n_infinity",
        docs=DOCS,
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$lastN": {"n": FLOAT_INFINITY, "input": "$v"}},
                }
            }
        ],
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="$lastN should reject infinity as n",
    ),
]

# Property [Non-Integer n]: ``n`` must be integral. Fractional double and
# Decimal128 values are rejected with N_ACCUMULATOR_INVALID_N_ERROR.
LASTN_NON_INTEGER_N_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "n_non_integer_double",
        docs=DOCS,
        pipeline=[{"$group": {"_id": None, "result": {"$lastN": {"n": 2.5, "input": "$v"}}}}],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject a non-integer double n",
    ),
    AccumulatorTestCase(
        "n_non_integer_decimal128",
        docs=DOCS,
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$lastN": {"n": Decimal128("1.5"), "input": "$v"}},
                }
            }
        ],
        error_code=N_ACCUMULATOR_INVALID_N_ERROR,
        msg="$lastN should reject a non-integer Decimal128 n",
    ),
]

LASTN_ERROR_TESTS = (
    LASTN_MALFORMED_SPEC_ERROR_TESTS
    + LASTN_MISSING_INPUT_ERROR_TESTS
    + LASTN_MISSING_N_ERROR_TESTS
    + LASTN_NON_POSITIVE_N_ERROR_TESTS
    + LASTN_NON_INTEGER_N_ERROR_TESTS
    + LASTN_NON_COERCIBLE_N_ERROR_TESTS
)


@pytest.mark.aggregate
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
