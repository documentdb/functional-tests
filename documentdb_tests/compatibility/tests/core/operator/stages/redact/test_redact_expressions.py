"""Tests for expression support inside $redact.

Covers the predicate operators commonly used in redaction conditions and the
expression forms that resolve to a sentinel.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Condition Operator Support]: a predicate operator evaluates per
# document and selects the $$KEEP/$$PRUNE branch of a conditional.
REDACT_EXPRESSION_TESTS: list[StageTestCase] = [
    # Comparisons.
    StageTestCase(
        "expr_eq",
        docs=[{"_id": 1, "status": "public"}, {"_id": 2, "status": "private"}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$status", "public"]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "status": "public"}],
        msg="$eq should drive $redact, keeping documents whose status equals the allowed value",
    ),
    StageTestCase(
        "expr_ne",
        docs=[{"_id": 1, "status": "public"}, {"_id": 2, "status": "secret"}],
        pipeline=[{"$redact": {"$cond": [{"$ne": ["$status", "secret"]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "status": "public"}],
        msg="$ne should drive $redact, keeping documents whose status differs from the blocked one",
    ),
    StageTestCase(
        "expr_gt",
        docs=[{"_id": 1, "level": 5}, {"_id": 2, "level": 3}],
        pipeline=[{"$redact": {"$cond": [{"$gt": ["$level", 3]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 5}],
        msg="$gt should drive $redact, keeping documents strictly above the threshold level",
    ),
    StageTestCase(
        "expr_gte",
        docs=[{"_id": 1, "level": 5}, {"_id": 2, "level": 4}],
        pipeline=[{"$redact": {"$cond": [{"$gte": ["$level", 5]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 5}],
        msg="$gte should drive $redact, keeping documents at or above the threshold level",
    ),
    StageTestCase(
        "expr_lt",
        docs=[{"_id": 1, "level": 2}, {"_id": 2, "level": 3}],
        pipeline=[{"$redact": {"$cond": [{"$lt": ["$level", 3]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 2}],
        msg="$lt should drive $redact, keeping documents strictly below the threshold level",
    ),
    StageTestCase(
        "expr_lte",
        docs=[{"_id": 1, "level": 2}, {"_id": 2, "level": 5}],
        pipeline=[{"$redact": {"$cond": [{"$lte": ["$level", 2]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "level": 2}],
        msg="$lte should drive $redact, keeping documents at or below the threshold level",
    ),
    # Boolean combiners.
    StageTestCase(
        "expr_and",
        docs=[
            {"_id": 1, "status": "public", "level": 2},
            {"_id": 2, "status": "secret", "level": 2},
            {"_id": 3, "status": "public", "level": 9},
        ],
        pipeline=[
            {
                "$redact": {
                    "$cond": [
                        {"$and": [{"$eq": ["$status", "public"]}, {"$lt": ["$level", 5]}]},
                        "$$KEEP",
                        "$$PRUNE",
                    ]
                }
            }
        ],
        expected=[{"_id": 1, "status": "public", "level": 2}],
        msg="$and should drive $redact, keeping documents satisfying every clause",
    ),
    StageTestCase(
        "expr_or",
        docs=[
            {"_id": 1, "status": "public", "level": 9},
            {"_id": 2, "status": "secret", "level": 2},
            {"_id": 3, "status": "secret", "level": 9},
        ],
        pipeline=[
            {
                "$redact": {
                    "$cond": [
                        {"$or": [{"$eq": ["$status", "public"]}, {"$lt": ["$level", 5]}]},
                        "$$KEEP",
                        "$$PRUNE",
                    ]
                }
            }
        ],
        expected=[
            {"_id": 1, "status": "public", "level": 9},
            {"_id": 2, "status": "secret", "level": 2},
        ],
        msg="$or should drive $redact, keeping documents satisfying any clause",
    ),
    StageTestCase(
        "expr_not",
        docs=[{"_id": 1, "status": "public"}, {"_id": 2, "status": "secret"}],
        pipeline=[
            {
                "$redact": {
                    "$cond": [{"$not": [{"$eq": ["$status", "secret"]}]}, "$$KEEP", "$$PRUNE"]
                }
            }
        ],
        expected=[{"_id": 1, "status": "public"}],
        msg="$not should drive $redact, keeping documents that fail the negated clause",
    ),
    # Membership and set-based access control.
    StageTestCase(
        "expr_in",
        docs=[{"_id": 1, "status": "public"}, {"_id": 2, "status": "secret"}],
        pipeline=[
            {
                "$redact": {
                    "$cond": [{"$in": ["$status", ["public", "shared"]]}, "$$KEEP", "$$PRUNE"]
                }
            }
        ],
        expected=[{"_id": 1, "status": "public"}],
        msg="$in should drive $redact, keeping documents whose status is among the allowed values",
    ),
    StageTestCase(
        "expr_size",
        docs=[{"_id": 1, "tags": ["A"]}, {"_id": 2, "tags": []}],
        pipeline=[{"$redact": {"$cond": [{"$gt": [{"$size": "$tags"}, 0]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "tags": ["A"]}],
        msg="$size should drive $redact, keeping documents whose tag array is non-empty",
    ),
    StageTestCase(
        "expr_setIntersection",
        docs=[{"_id": 1, "tags": ["A", "X"]}, {"_id": 2, "tags": ["Y", "Z"]}],
        pipeline=[
            {
                "$redact": {
                    "$cond": [
                        {"$gt": [{"$size": {"$setIntersection": ["$tags", ["A", "B"]]}}, 0]},
                        "$$KEEP",
                        "$$PRUNE",
                    ]
                }
            }
        ],
        expected=[{"_id": 1, "tags": ["A", "X"]}],
        msg="$setIntersection should drive $redact, keeping documents sharing a tag with the "
        "allowed set",
    ),
    StageTestCase(
        "expr_setIsSubset",
        docs=[
            {"_id": 1, "required": ["read"], "granted": ["read", "write"]},
            {"_id": 2, "required": ["admin"], "granted": ["read"]},
        ],
        pipeline=[
            {
                "$redact": {
                    "$cond": [{"$setIsSubset": ["$required", "$granted"]}, "$$KEEP", "$$PRUNE"]
                }
            }
        ],
        expected=[{"_id": 1, "required": ["read"], "granted": ["read", "write"]}],
        msg="$setIsSubset should drive $redact, keeping documents whose required tags are all "
        "granted",
    ),
    StageTestCase(
        "expr_anyElementTrue",
        docs=[{"_id": 1, "flags": [False, True]}, {"_id": 2, "flags": [False, False]}],
        pipeline=[{"$redact": {"$cond": [{"$anyElementTrue": ["$flags"]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "flags": [False, True]}],
        msg="$anyElementTrue should drive $redact, keeping documents with any flag set",
    ),
    StageTestCase(
        "expr_allElementsTrue",
        docs=[{"_id": 1, "flags": [True, True]}, {"_id": 2, "flags": [True, False]}],
        pipeline=[{"$redact": {"$cond": [{"$allElementsTrue": ["$flags"]}, "$$KEEP", "$$PRUNE"]}}],
        expected=[{"_id": 1, "flags": [True, True]}],
        msg="$allElementsTrue should drive $redact, keeping documents with every flag set",
    ),
    # Type-based.
    StageTestCase(
        "expr_type",
        docs=[{"_id": 1, "level": 5}, {"_id": 2, "level": "high"}],
        pipeline=[
            {"$redact": {"$cond": [{"$eq": [{"$type": "$level"}, "int"]}, "$$KEEP", "$$PRUNE"]}}
        ],
        expected=[{"_id": 1, "level": 5}],
        msg="$type should drive $redact, keeping documents whose level field is the expected type",
    ),
]

# Property [Sentinel Resolution]: an expression that resolves directly to a
# sentinel drives the stage's behavior.
REDACT_SENTINEL_RESOLUTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sentinel_bare_keep",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": "$$KEEP"}],
        expected=[{"_id": 1, "a": 1}],
        msg="$redact should keep the whole document when the argument resolves to $$KEEP",
    ),
    StageTestCase(
        "sentinel_bare_prune",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": "$$PRUNE"}],
        expected=[],
        msg="$redact should drop the document when the argument resolves to $$PRUNE",
    ),
    StageTestCase(
        "sentinel_bare_descend",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": "$$DESCEND"}],
        expected=[{"_id": 1, "a": 1}],
        msg="$redact should descend and retain all content when the argument resolves to $$DESCEND",
    ),
    StageTestCase(
        "sentinel_switch_branches",
        docs=[{"_id": 1, "level": 5}, {"_id": 2, "level": 3}, {"_id": 3, "level": 1}],
        pipeline=[
            {
                "$redact": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$level", 5]}, "then": "$$KEEP"},
                            {"case": {"$eq": ["$level", 3]}, "then": "$$PRUNE"},
                        ],
                        "default": "$$KEEP",
                    }
                }
            }
        ],
        expected=[{"_id": 1, "level": 5}, {"_id": 3, "level": 1}],
        msg="$redact should honor a sentinel chosen by a $switch branch or its default",
    ),
    StageTestCase(
        "sentinel_let_user_variable",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": {"$let": {"vars": {"x": "$$PRUNE"}, "in": "$$x"}}}],
        expected=[],
        msg="$redact should honor a sentinel bound to a user variable and returned by $let",
    ),
    StageTestCase(
        "sentinel_map_as_variable_body",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": {"$first": {"$map": {"input": [1], "as": "y", "in": "$$PRUNE"}}}}],
        expected=[],
        msg="$redact should honor a sentinel returned from a $map as-variable body",
    ),
    StageTestCase(
        "sentinel_ifnull_coalesce",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": {"$ifNull": [MISSING, "$$PRUNE"]}}],
        expected=[],
        msg="$redact should honor a sentinel produced by $ifNull coalescing",
    ),
    StageTestCase(
        "sentinel_array_elem_at_prune",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": {"$arrayElemAt": [["$$PRUNE"], 0]}}],
        expected=[],
        msg="$redact should honor a sentinel extracted from an array by $arrayElemAt",
    ),
    StageTestCase(
        "sentinel_get_field_prune",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": {"$getField": {"field": "f", "input": {"f": "$$PRUNE"}}}}],
        expected=[],
        msg="$redact should honor a sentinel extracted from a document by $getField",
    ),
    StageTestCase(
        "sentinel_first_prune",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": {"$first": [["$$PRUNE"]]}}],
        expected=[],
        msg="$redact should honor a sentinel extracted from an array by $first",
    ),
    StageTestCase(
        "sentinel_last_prune",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$redact": {"$last": [["$$PRUNE"]]}}],
        expected=[],
        msg="$redact should honor a sentinel extracted from an array by $last",
    ),
]

REDACT_EXPRESSION_FILE_TESTS = REDACT_EXPRESSION_TESTS + REDACT_SENTINEL_RESOLUTION_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REDACT_EXPRESSION_FILE_TESTS))
def test_redact_expression_cases(collection, test_case: StageTestCase):
    """Test expression operator support and sentinel resolution inside $redact."""
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
