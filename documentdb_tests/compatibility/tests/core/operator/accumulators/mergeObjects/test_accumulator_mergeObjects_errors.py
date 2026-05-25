"""Tests for $mergeObjects accumulator: arity errors, syntax validation, and error propagation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Syntax Validation]: "$" by itself is not a valid FieldPath and
# produces an error.
MERGE_OBJECTS_SYNTAX_VALIDATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "syntax_bare_dollar",
        docs=[{"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$"}}}],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$mergeObjects should reject '$' as an invalid FieldPath",
    ),
]

# Property [Arity Rejection]: $mergeObjects in accumulator context is a unary
# operator and must reject array syntax.
MERGE_OBJECTS_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$mergeObjects should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": [{"a": 1}]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$mergeObjects should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$mergeObjects should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": [{"a": 1}, {"b": 2}]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$mergeObjects should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": {"a": 1}}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$literal": {"a": 1}, "$toUpper": "hello"}},
                }
            }
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$mergeObjects should reject multi-key expression object",
    ),
]

# Property [Expression Error Propagation]: when the accumulator expression
# errors for any document in the group, the error propagates to the caller.
MERGE_OBJECTS_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_to_object_id_invalid",
        docs=[{"v": "not_valid_oid"}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$mergeObjects": {
                            "$cond": [
                                True,
                                {"converted": {"$toObjectId": "$v"}},
                                {"fallback": 1},
                            ]
                        }
                    },
                }
            }
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$mergeObjects should propagate $toObjectId conversion error from expression",
    ),
]

MERGE_OBJECTS_ERROR_TESTS = (
    MERGE_OBJECTS_SYNTAX_VALIDATION_TESTS
    + MERGE_OBJECTS_ARITY_ERROR_TESTS
    + MERGE_OBJECTS_EXPRESSION_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MERGE_OBJECTS_ERROR_TESTS))
def test_accumulator_mergeObjects_errors(collection, test_case: AccumulatorTestCase):
    """Test $mergeObjects error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)  # type: ignore[arg-type]
