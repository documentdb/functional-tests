"""Tests for $redact argument validation: lazy evaluation and non-sentinel rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    REDACT_NON_SENTINEL_ERROR,
    SIZE_NOT_ARRAY_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF, MISSING

# Property [Lazy Evaluation]: only the value the expression actually resolves to
# is validated, so unreached invalid values produce no error.
REDACT_LAZY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "lazy_cond_else_invalid_untaken",
        docs=[{"_id": 1, "level": 5, "other": "x"}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$level", 5]}, "$$KEEP", "oops"]}}],
        expected=[{"_id": 1, "level": 5, "other": "x"}],
        msg="$redact should not validate an invalid value in an untaken $cond else branch",
    ),
    StageTestCase(
        "lazy_cond_then_invalid_untaken",
        docs=[{"_id": 1, "level": 3}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$level", 5]}, "oops", "$$PRUNE"]}}],
        expected=[],
        msg="$redact should not validate an invalid value in an untaken $cond then branch",
    ),
    StageTestCase(
        "lazy_keep_short_circuits_descent",
        docs=[{"_id": 1, "keep": True, "child": {"keep": False, "bad": 1}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$keep", True]}, "$$KEEP", "$bad"]}}],
        expected=[{"_id": 1, "keep": True, "child": {"keep": False, "bad": 1}}],
        msg="$redact under $$KEEP should not evaluate the expression at a deeper level "
        "where it would resolve to a non-sentinel value",
    ),
    StageTestCase(
        "lazy_prune_short_circuits_descent",
        docs=[{"_id": 1, "drop": True, "child": {"drop": False, "bad": 1}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$drop", True]}, "$$PRUNE", "$bad"]}}],
        expected=[],
        msg="$redact under $$PRUNE should not evaluate the expression at a deeper level "
        "where it would resolve to a non-sentinel value",
    ),
    StageTestCase(
        "lazy_empty_collection_not_evaluated",
        docs=[],
        pipeline=[{"$redact": {"$literal": "not_a_sentinel"}}],
        expected=[],
        msg="$redact should not evaluate a non-sentinel expression against an empty "
        "collection, returning no documents and no error",
    ),
]

# Property [Null and Missing Argument]: an argument resolving to null or missing
# is rejected as a non-sentinel at evaluation time.
REDACT_NULL_MISSING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_bare_argument",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": None}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a bare null argument as a non-sentinel value",
    ),
    StageTestCase(
        "null_missing_field_reference",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": MISSING}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a missing-field reference that resolves to missing",
    ),
]

# Property [Non-Sentinel Type Strictness]: a resolved value of any non-sentinel
# BSON type is rejected.
REDACT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": {"$literal": val}}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg=f"$redact should reject a resolved {tid} value as a non-sentinel",
    )
    for tid, val in [
        ("string", "hello"),
        ("int32", 7),
        ("int64", Int64(9)),
        ("double", 3.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("document", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Sentinel Name Strings]: a string equal to a sentinel name or the
# literal text "$$DESCEND" resolves to a string and is rejected.
REDACT_SENTINEL_STRING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sentinel_string_descend",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": "DESCEND"}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject the bare string 'DESCEND' as a non-sentinel",
    ),
    StageTestCase(
        "sentinel_string_prune",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": "PRUNE"}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject the bare string 'PRUNE' as a non-sentinel",
    ),
    StageTestCase(
        "sentinel_string_keep",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": "KEEP"}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject the bare string 'KEEP' as a non-sentinel",
    ),
    StageTestCase(
        "sentinel_string_literal_dollar_descend",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": {"$literal": "$$DESCEND"}}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject the literal string '$$DESCEND' as a non-sentinel",
    ),
    StageTestCase(
        "sentinel_string_stored_field",
        docs=[{"_id": 1, "sname": "$$DESCEND"}],
        pipeline=[{"$redact": "$sname"}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a stored field whose value is the string '$$DESCEND'",
    ),
]

# Property [Defined Non-Sentinel System Variables]: a defined non-sentinel
# system variable resolves to a non-sentinel value and is rejected.
REDACT_DEFINED_VARIABLE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"defined_variable_{label}",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": var}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg=f"$redact should reject the defined system variable {var} as a non-sentinel",
    )
    for label, var in [
        ("root", "$$ROOT"),
        ("current", "$$CURRENT"),
        ("remove", "$$REMOVE"),
        ("now", "$$NOW"),
    ]
]

# Property [Argument Shape Strictness]: the stage does not unwrap array
# arguments or special-case empty containers, so each resolves to a
# non-sentinel value and is rejected.
REDACT_ARGUMENT_SHAPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "shape_array_single_sentinel",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": ["$$DESCEND"]}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a single-element literal array without unwrapping its "
        "sentinel element",
    ),
    StageTestCase(
        "shape_array_single_expression",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": [{"$cond": [{"$eq": [1, 1]}, "$$KEEP", "$$PRUNE"]}]}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a single-element array wrapping a sentinel-returning "
        "expression without unwrapping it",
    ),
    StageTestCase(
        "shape_array_nested_deeper",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": [["$$DESCEND"]]}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a deeper nested array without unwrapping at any depth",
    ),
    StageTestCase(
        "shape_array_multi_element",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": ["$$DESCEND", "$$KEEP"]}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a multi-element array as a single array value rather "
        "than treating it as an arity error",
    ),
    StageTestCase(
        "shape_array_field_reference",
        docs=[{"_id": 1, "arr": ["DESCEND"]}],
        pipeline=[{"$redact": "$arr"}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject a field reference whose stored value is an array "
        "identically to a literal array",
    ),
    StageTestCase(
        "shape_empty_document",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": {}}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject an empty-document argument as a non-sentinel value",
    ),
    StageTestCase(
        "shape_empty_array",
        docs=[{"_id": 1}],
        pipeline=[{"$redact": []}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact should reject an empty-array argument as a non-sentinel value",
    ),
]

# Property [Inner Expression Errors During Descent]: an inner operator error on
# a value reached at a deeper level surfaces rather than a redact error.
REDACT_INNER_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "inner_size_setintersection_missing_at_depth",
        docs=[{"_id": 1, "tags": ["A"], "sub": {"content": "x"}}],
        pipeline=[
            {
                "$redact": {
                    "$cond": {
                        "if": {"$gt": [{"$size": {"$setIntersection": ["$tags", ["A"]]}}, 0]},
                        "then": "$$DESCEND",
                        "else": "$$PRUNE",
                    }
                }
            }
        ],
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$redact should surface the inner $size error when $setIntersection of a "
        "field absent at a deeper level yields null during descent",
    ),
]

# Property [Non-Sentinel Reached via $$DESCEND]: a non-sentinel resolution
# reachable only by descending is reached and rejected at the deeper level.
REDACT_DESCEND_REACHES_NON_SENTINEL_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "descend_reaches_deep_non_sentinel",
        docs=[{"_id": 1, "keep": True, "child": {"keep": False, "bad": 1}}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$keep", True]}, "$$DESCEND", "$bad"]}}],
        error_code=REDACT_NON_SENTINEL_ERROR,
        msg="$redact under $$DESCEND should reach and reject a non-sentinel value at a "
        "deeper level that a $$KEEP/$$PRUNE short-circuit would never evaluate",
    ),
]

REDACT_VALIDATION_TESTS = (
    REDACT_LAZY_TESTS
    + REDACT_NULL_MISSING_ERROR_TESTS
    + REDACT_TYPE_ERROR_TESTS
    + REDACT_SENTINEL_STRING_ERROR_TESTS
    + REDACT_DEFINED_VARIABLE_ERROR_TESTS
    + REDACT_ARGUMENT_SHAPE_ERROR_TESTS
    + REDACT_INNER_ERROR_TESTS
    + REDACT_DESCEND_REACHES_NON_SENTINEL_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REDACT_VALIDATION_TESTS))
def test_redact_validation_cases(collection, test_case: StageTestCase):
    """Test $redact lazy evaluation and rejection of non-sentinel argument values."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
