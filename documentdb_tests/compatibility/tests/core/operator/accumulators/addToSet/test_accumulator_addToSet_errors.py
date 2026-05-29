"""Tests for $addToSet accumulator error cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [Arity]: $addToSet in accumulator context is a unary operator and
# rejects array syntax.
ADDTOSET_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": []}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$addToSet should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": [1]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$addToSet should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": ["$v"]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$addToSet should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": [1, 2, 3]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$addToSet should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$add": [1, 2], "$multiply": [3, 4]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$addToSet should reject multi-key expression object",
    ),
]

# Property [Expression Error Propagation]: errors from sub-expressions propagate.
ADDTOSET_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid",
        docs=[{"v": "not_a_number"}],
        pipeline=[{"$group": {"_id": None, "result": {"$addToSet": {"$toInt": "$v"}}}}],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$addToSet should propagate $toInt conversion error",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$addToSet": {"$divide": ["$v", 0]}}}}],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$addToSet should propagate divide-by-zero error",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_field_path",
        docs=[{"_id": 0, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$addToSet": {"$divide": [1, "$v"]}}}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$addToSet should propagate $divide by zero when divisor comes from field path",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_later_doc",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$addToSet": {"$divide": [1, "$v"]}}}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$addToSet should propagate error even when failing doc is not the first",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$addToSet": {"$mod": ["$v", 0]}}}}],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$addToSet should propagate mod-by-zero error",
    ),
]

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


ADDTOSET_ERROR_TESTS = ADDTOSET_ARITY_ERROR_TESTS + ADDTOSET_EXPRESSION_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_ERROR_TESTS))
def test_accumulator_addToSet_errors(collection, test_case):
    """Test $addToSet accumulator error cases with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
