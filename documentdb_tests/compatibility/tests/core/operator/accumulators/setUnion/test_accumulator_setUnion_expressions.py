"""Tests for $setUnion accumulator: expression types and error propagation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Type]: $setUnion accepts various expression types as its
# argument in $group context — literals, field paths, nested field paths,
# expression operators, and conditional expressions.
SETUNION_EXPRESSION_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_literal_array",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$literal": [10, 20]}},
                }
            },
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [10, 20]}],
        msg="$setUnion should accept $literal array expression",
    ),
    AccumulatorTestCase(
        "expr_field_path",
        docs=[{"v": [1, 2]}, {"v": [2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should accept simple field path expression",
    ),
    AccumulatorTestCase(
        "expr_nested_field_path",
        docs=[{"a": {"b": [1, 2]}}, {"a": {"b": [2, 3]}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$a.b"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should accept nested field path expression",
    ),
    AccumulatorTestCase(
        "expr_expression_operator",
        docs=[{"v": [1, 2, 2, 3]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$setUnion": ["$v", [4]]}},
                }
            },
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should accept expression operator ($setUnion expression) as argument",
    ),
    AccumulatorTestCase(
        "expr_cond_expression",
        docs=[
            {"v": [1, 2], "use": True},
            {"v": [3, 4], "use": False},
            {"v": [5, 6], "use": True},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$cond": ["$use", "$v", "$$REMOVE"],
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 5, 6]}],
        msg="$setUnion should accept $cond expression as argument",
    ),
    AccumulatorTestCase(
        "expr_object_expression",
        docs=[{"v": [1, 2]}, {"v": [2, 3]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {"$ifNull": ["$v", []]},
                    },
                }
            },
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should accept object expression ($ifNull) as argument",
    ),
]

# Property [Expression Error Propagation]: errors from sub-expressions propagate
# through $setUnion without being caught or suppressed.
SETUNION_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_prop_toint_non_convertible",
        docs=[{"v": "hello"}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$let": {
                                "vars": {"x": {"$toInt": "$v"}},
                                "in": ["$$x"],
                            }
                        }
                    },
                }
            },
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$setUnion should propagate $toInt conversion error for non-convertible value",
    ),
    AccumulatorTestCase(
        "error_prop_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$let": {
                                "vars": {"x": {"$divide": ["$v", 0]}},
                                "in": ["$$x"],
                            }
                        }
                    },
                }
            },
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$setUnion should propagate $divide by zero error",
    ),
    AccumulatorTestCase(
        "error_prop_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {
                            "$let": {
                                "vars": {"x": {"$mod": ["$v", 0]}},
                                "in": ["$$x"],
                            }
                        }
                    },
                }
            },
        ],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$setUnion should propagate $mod by zero error",
    ),
]

SETUNION_EXPRESSION_SUCCESS_TESTS = SETUNION_EXPRESSION_TYPE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_EXPRESSION_SUCCESS_TESTS))
def test_accumulator_setUnion_expressions(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator expression type handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_EXPRESSION_ERROR_TESTS))
def test_accumulator_setUnion_expression_errors(collection, test_case):
    """Test $setUnion accumulator expression error propagation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
