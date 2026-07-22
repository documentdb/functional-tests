"""Tests for $lookup correlated subquery — edge cases, errors, and boundary behavior.

Covers let expression errors, undefined variable references, naming edge cases,
numeric equivalence, special numeric values, $$REMOVE semantics, and
let variable path traversal.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessNaN
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Correlated Subquery — Edge Cases]: let expression error propagation,
# undefined variable behavior, numeric equivalence in $expr, special numeric
# values, $$REMOVE semantics, and path traversal on let variables.


LOOKUP_EDGE_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_expr_type_mismatch_error",
        docs=[{"_id": 1, "num": 5}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"bad": {"$add": ["$num", "not_a_number"]}},
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$lookup let with $add type mismatch should propagate error",
    ),
    LookupTestCase(
        "let_expr_error_for_some_docs_fails_all",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2, "x": 0},
        ],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"inv": {"$divide": [1, "$x"]}},
                    "pipeline": [{"$addFields": {"val": "$$inv"}}],
                    "as": "joined",
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg=(
            "$lookup let expression that errors for one outer doc"
            " should fail the entire aggregate"
        ),
    ),
]


LOOKUP_EDGE_UNDEFINED_VAR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "undefined_var_in_addFields_errors",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$_id"},
                    "pipeline": [{"$addFields": {"val": "$$undefined_var"}}],
                    "as": "joined",
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$lookup referencing undefined variable in $addFields should error",
    ),
]


LOOKUP_EDGE_NUMERIC_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "numeric_equivalence_int_matches_double",
        docs=[{"_id": 1, "val": 5}],
        foreign_docs=[
            {"_id": 10, "field": 5.0},
            {"_id": 11, "field": 6.0},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$val"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$field", "$$x"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "val": 5, "joined": [{"_id": 10, "field": 5.0}]}],
        msg="$lookup $expr $eq with int let var should match double of same numeric value",
    ),
    LookupTestCase(
        "numeric_equivalence_long_matches_decimal128",
        docs=[{"_id": 1, "val": Int64(5)}],
        foreign_docs=[
            {"_id": 10, "field": Decimal128("5")},
            {"_id": 11, "field": Decimal128("6")},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$val"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$field", "$$x"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "val": Int64(5), "joined": [{"_id": 10, "field": Decimal128("5")}]}],
        msg="$lookup $expr $eq with Int64 let var should match Decimal128 of same value",
    ),
    LookupTestCase(
        "type_distinction_int_does_not_match_string",
        docs=[{"_id": 1, "val": 5}],
        foreign_docs=[
            {"_id": 10, "field": "5"},
            {"_id": 11, "field": 5},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$val"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$field", "$$x"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "val": 5, "joined": [{"_id": 11, "field": 5}]}],
        msg="$lookup $expr $eq with int let var should NOT match string of same characters",
    ),
]


LOOKUP_EDGE_SPECIAL_VALUES_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "negative_zero_matches_positive_zero",
        docs=[{"_id": 1, "val": -0.0}],
        foreign_docs=[
            {"_id": 10, "field": 0.0},
            {"_id": 11, "field": 1.0},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$val"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$field", "$$x"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "val": -0.0, "joined": [{"_id": 10, "field": 0.0}]}],
        msg="$lookup $expr $eq with -0.0 let var should match 0.0 (IEEE 754 equality)",
    ),
]


LOOKUP_EDGE_REMOVE_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "remove_in_addFields_omits_field",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10, "keep": "yes"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"removed": "$$REMOVE"},
                    "pipeline": [{"$addFields": {"x": "$$removed", "y": "present"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "joined": [{"_id": 10, "keep": "yes", "y": "present"}]}],
        msg=(
            "$lookup let with $$REMOVE value should omit the field"
            " when used in $addFields (field not present in output)"
        ),
    ),
    LookupTestCase(
        "remove_type_is_missing",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"removed": "$$REMOVE"},
                    "pipeline": [{"$addFields": {"t": {"$type": "$$removed"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "joined": [{"_id": 10, "t": "missing"}]}],
        msg="$lookup let with $$REMOVE should report $type as 'missing'",
    ),
]


LOOKUP_EDGE_PATH_TRAVERSAL_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "path_traversal_on_let_var_object",
        docs=[{"_id": 1, "obj": {"nested": {"field": "deep_value"}}}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"doc": "$obj"},
                    "pipeline": [{"$addFields": {"val": "$$doc.nested.field"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "obj": {"nested": {"field": "deep_value"}},
                "joined": [{"_id": 10, "val": "deep_value"}],
            }
        ],
        msg="$lookup let var path traversal '$$doc.nested.field' should resolve sub-path",
    ),
    LookupTestCase(
        "path_traversal_on_let_var_nonexistent_path",
        docs=[{"_id": 1, "obj": {"a": 1}}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"doc": "$obj"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "val": "$$doc.missing.path",
                                "t": {"$type": "$$doc.missing.path"},
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "obj": {"a": 1},
                "joined": [{"_id": 10, "t": "missing"}],
            }
        ],
        msg=(
            "$lookup let var path traversal to non-existent sub-path"
            " should resolve to missing (field omitted from output)"
        ),
    ),
]


# --- Combine all tests ---
LOOKUP_CORRELATED_EDGE_CASES_ALL: list[LookupTestCase] = (
    LOOKUP_EDGE_ERROR_TESTS
    + LOOKUP_EDGE_UNDEFINED_VAR_TESTS
    + LOOKUP_EDGE_NUMERIC_TESTS
    + LOOKUP_EDGE_SPECIAL_VALUES_TESTS
    + LOOKUP_EDGE_REMOVE_TESTS
    + LOOKUP_EDGE_PATH_TRAVERSAL_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CORRELATED_EDGE_CASES_ALL))
def test_lookup_correlated_edge_cases(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery edge cases, errors, and boundary behavior."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )


_NAN_TEST = LookupTestCase(
    "nan_matches_nan_in_expr_eq",
    docs=[{"_id": 1, "val": float("nan")}],
    foreign_docs=[
        {"_id": 10, "field": float("nan")},
        {"_id": 11, "field": 0},
    ],
    pipeline=[
        {
            "$lookup": {
                "from": FOREIGN,
                "let": {"x": "$val"},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$field", "$$x"]}}}],
                "as": "joined",
            }
        }
    ],
    expected=[{"_id": 1, "val": float("nan"), "joined": [{"_id": 10, "field": float("nan")}]}],
    msg="$lookup $expr $eq with NaN let var matches NaN foreign field (NaN == NaN in $expr)",
)


@pytest.mark.aggregate
def test_lookup_correlated_nan_matches_nan(collection):
    """Test $lookup $expr $eq with NaN let var matches NaN (uses NaN-aware assertion)."""
    with setup_lookup(collection, _NAN_TEST) as foreign_name:
        command = build_lookup_command(collection, _NAN_TEST, foreign_name)
        result = execute_command(collection, command)
        assertSuccessNaN(result, _NAN_TEST.expected, msg=_NAN_TEST.msg)
