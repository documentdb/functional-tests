"""Tests for $min accumulator — error cases ($group)."""

from __future__ import annotations

from typing import Any

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


def _group_min(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline for $min."""
    return [{"$group": {"_id": None, "result": {"$min": accumulator}}}]


def _run_accumulator(collection, test_case: AccumulatorTestCase):
    """Insert docs and run the pipeline."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )


# ---------------------------------------------------------------------------
# Property [Expression Error Propagation]: errors in sub-expressions used as
# $min operand propagate as errors.
# ---------------------------------------------------------------------------
MIN_EXPRESSION_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid",
        docs=[{"v": "not_a_number"}],
        pipeline=_group_min({"$toInt": "$v"}),
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$min should propagate $toInt conversion error",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=_group_min({"$divide": ["$v", 0]}),
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$min should propagate divide-by-zero error",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=_group_min({"$mod": ["$v", 0]}),
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$min should propagate mod-by-zero error",
    ),
]

# ---------------------------------------------------------------------------
# Property [Arity Rejection]: $min in accumulator context is unary and rejects
# array syntax.
# ---------------------------------------------------------------------------
MIN_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=_group_min([]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element",
        docs=[{"v": 1}],
        pipeline=_group_min([1]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref",
        docs=[{"v": 1}],
        pipeline=_group_min(["$v"]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element",
        docs=[{"v": 1}],
        pipeline=_group_min([1, 2, 3]),
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression",
        docs=[{"v": 1}],
        pipeline=_group_min({"$add": [1, 2], "$multiply": [3, 4]}),
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$min should reject multi-key expression object",
    ),
]

# ---------------------------------------------------------------------------
# Combined error tests
# ---------------------------------------------------------------------------
MIN_GROUP_ERROR_TESTS = MIN_EXPRESSION_ERROR_GROUP_TESTS + MIN_ARITY_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_ERROR_TESTS))
def test_accumulator_min_group_errors(collection, test_case):
    """Test $min accumulator error cases with $group."""
    result = _run_accumulator(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
