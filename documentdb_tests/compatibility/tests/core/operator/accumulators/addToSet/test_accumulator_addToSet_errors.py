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
    MODULO_BY_ZERO_V2_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

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


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_EXPRESSION_ERROR_TESTS))
def test_accumulator_addToSet_errors(collection, test_case):
    """Test $addToSet accumulator error cases with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
