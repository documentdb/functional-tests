"""Tests for $lookup correlated subquery — let variables in $project/$addFields and other stages.

Covers let variable direct access in non-$match stages: $addFields, $project,
$group, $redact, $replaceRoot. Includes conditional logic, array/string
manipulation, and type preservation through sub-pipeline stages.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Section 1: Basic Direct Access in $addFields and $project ---

LOOKUP_PROJECT_BASIC_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "project_let_var_in_computed_field",
        docs=[{"_id": 1, "label": "outer_label"}],
        foreign_docs=[{"_id": 10, "name": "item_a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"lbl": "$label"},
                    "pipeline": [{"$project": {"_id": 1, "name": 1, "outerLabel": "$$lbl"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "label": "outer_label",
                "joined": [{"_id": 10, "name": "item_a", "outerLabel": "outer_label"}],
            }
        ],
        msg="$lookup $project should access let variable directly as computed field value",
    ),
    LookupTestCase(
        "project_concat_with_let_var",
        docs=[{"_id": 1, "label": "PREFIX"}],
        foreign_docs=[{"_id": 10, "name": "item"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"lbl": "$label"},
                    "pipeline": [
                        {
                            "$project": {
                                "_id": 1,
                                "combined": {"$concat": ["$$lbl", " - ", "$name"]},
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
                "label": "PREFIX",
                "joined": [{"_id": 10, "combined": "PREFIX - item"}],
            }
        ],
        msg="$lookup $project with $concat should combine let var with foreign field",
    ),
    LookupTestCase(
        "project_arithmetic_with_let_var",
        docs=[{"_id": 1, "unitPrice": 5}],
        foreign_docs=[{"_id": 10, "qty": 3}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"price": "$unitPrice"},
                    "pipeline": [
                        {
                            "$project": {
                                "_id": 0,
                                "total": {"$multiply": ["$qty", "$$price"]},
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
                "unitPrice": 5,
                "joined": [{"total": 15}],
            }
        ],
        msg="$lookup $project with $multiply should compute arithmetic using let var",
    ),
]

# --- Section 2: Conditional Logic with Let Variables ---

LOOKUP_PROJECT_CONDITIONAL_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "addFields_cond_with_let_var",
        docs=[{"_id": 1, "threshold": 60}],
        foreign_docs=[
            {"_id": 10, "score": 80},
            {"_id": 11, "score": 40},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"thr": "$threshold"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "label": {
                                    "$cond": [
                                        {"$gte": ["$score", "$$thr"]},
                                        "pass",
                                        "fail",
                                    ]
                                }
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
                "threshold": 60,
                "joined": [
                    {"_id": 10, "score": 80, "label": "pass"},
                    {"_id": 11, "score": 40, "label": "fail"},
                ],
            }
        ],
        msg="$lookup $addFields with $cond should classify based on let var threshold",
    ),
    LookupTestCase(
        "addFields_switch_with_let_var",
        docs=[{"_id": 1, "highMark": 80}],
        foreign_docs=[
            {"_id": 10, "amount": 90},
            {"_id": 11, "amount": 50},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"high": "$highMark"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "tier": {
                                    "$switch": {
                                        "branches": [
                                            {
                                                "case": {"$gte": ["$amount", "$$high"]},
                                                "then": "premium",
                                            }
                                        ],
                                        "default": "standard",
                                    }
                                }
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
                "highMark": 80,
                "joined": [
                    {"_id": 10, "amount": 90, "tier": "premium"},
                    {"_id": 11, "amount": 50, "tier": "standard"},
                ],
            }
        ],
        msg="$lookup $addFields with $switch should branch using let var threshold",
    ),
    LookupTestCase(
        "addFields_ifNull_let_var_as_default",
        docs=[{"_id": 1, "defaultName": "Anonymous"}],
        foreign_docs=[
            {"_id": 10, "name": "Alice"},
            {"_id": 11},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"dflt": "$defaultName"},
                    "pipeline": [{"$addFields": {"displayName": {"$ifNull": ["$name", "$$dflt"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "defaultName": "Anonymous",
                "joined": [
                    {"_id": 10, "name": "Alice", "displayName": "Alice"},
                    {"_id": 11, "displayName": "Anonymous"},
                ],
            }
        ],
        msg="$lookup $addFields with $ifNull should use let var as fallback when field missing",
    ),
]

# --- Section 3: Array/String Manipulation with Let Variables ---

LOOKUP_PROJECT_ARRAY_STRING_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "addFields_concatArrays_with_let_var",
        docs=[{"_id": 1, "extra": ["x", "y"]}],
        foreign_docs=[{"_id": 10, "tags": ["a", "b"]}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"extras": "$extra"},
                    "pipeline": [
                        {"$addFields": {"allTags": {"$concatArrays": ["$tags", "$$extras"]}}}
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "extra": ["x", "y"],
                "joined": [{"_id": 10, "tags": ["a", "b"], "allTags": ["a", "b", "x", "y"]}],
            }
        ],
        msg="$lookup $addFields with $concatArrays should append let var array to foreign array",
    ),
    LookupTestCase(
        "addFields_string_concat_path_with_let_var",
        docs=[{"_id": 1, "basePath": "/products"}],
        foreign_docs=[{"_id": 10, "slug": "widget"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"base": "$basePath"},
                    "pipeline": [
                        {"$addFields": {"fullPath": {"$concat": ["$$base", "/", "$slug"]}}}
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "basePath": "/products",
                "joined": [{"_id": 10, "slug": "widget", "fullPath": "/products/widget"}],
            }
        ],
        msg="$lookup $addFields with $concat should build path from let var and foreign field",
    ),
    LookupTestCase(
        "addFields_filter_threshold_from_let_var",
        docs=[{"_id": 1, "minScore": 70}],
        foreign_docs=[{"_id": 10, "scores": [50, 75, 90, 60]}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"min": "$minScore"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "highScores": {
                                    "$filter": {
                                        "input": "$scores",
                                        "cond": {"$gte": ["$$this", "$$min"]},
                                    }
                                }
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
                "minScore": 70,
                "joined": [{"_id": 10, "scores": [50, 75, 90, 60], "highScores": [75, 90]}],
            }
        ],
        msg="$lookup $addFields with $filter should use let var as threshold for array filtering",
    ),
    LookupTestCase(
        "addFields_map_with_let_var_multiplier",
        docs=[{"_id": 1, "rate": 1.1}],
        foreign_docs=[{"_id": 10, "prices": [10, 20, 30]}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"r": "$rate"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "adjusted": {
                                    "$map": {
                                        "input": "$prices",
                                        "in": {"$multiply": ["$$this", "$$r"]},
                                    }
                                }
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
                "rate": 1.1,
                "joined": [
                    {
                        "_id": 10,
                        "prices": [10, 20, 30],
                        "adjusted": [11.0, 22.0, 33.0],
                    }
                ],
            }
        ],
        msg="$lookup $addFields with $map should scale array values using let var multiplier",
    ),
]

# --- Section 4: Let Variables in $group Within Sub-Pipeline ---

LOOKUP_PROJECT_GROUP_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "group_let_var_as_id",
        docs=[{"_id": 1, "cat": "electronics"}],
        foreign_docs=[
            {"_id": 10, "item": "phone"},
            {"_id": 11, "item": "laptop"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"category": "$cat"},
                    "pipeline": [{"$group": {"_id": "$$category", "count": {"$sum": 1}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "electronics",
                "joined": [{"_id": "electronics", "count": 2}],
            }
        ],
        msg="$lookup $group with let var as _id should group all foreign docs under that value",
    ),
    LookupTestCase(
        "group_conditional_count_with_let_var",
        docs=[{"_id": 1, "minVal": 50}],
        foreign_docs=[
            {"_id": 10, "val": 80},
            {"_id": 11, "val": 30},
            {"_id": 12, "val": 60},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"min": "$minVal"},
                    "pipeline": [
                        {
                            "$group": {
                                "_id": None,
                                "above": {"$sum": {"$cond": [{"$gte": ["$val", "$$min"]}, 1, 0]}},
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
                "minVal": 50,
                "joined": [{"_id": None, "above": 2}],
            }
        ],
        msg="$lookup $group with $cond using let var should count docs meeting threshold",
    ),
]

# --- Section 5: Let Variables in $redact ---

LOOKUP_PROJECT_REDACT_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "redact_with_let_var",
        docs=[{"_id": 1, "accessLevel": 2}],
        foreign_docs=[
            {"_id": 10, "level": 1, "data": "public"},
            {"_id": 11, "level": 2, "data": "restricted"},
            {"_id": 12, "level": 3, "data": "secret"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"access": "$accessLevel"},
                    "pipeline": [
                        {
                            "$redact": {
                                "$cond": [
                                    {"$lte": ["$level", "$$access"]},
                                    "$$KEEP",
                                    "$$PRUNE",
                                ]
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
                "accessLevel": 2,
                "joined": [
                    {"_id": 10, "level": 1, "data": "public"},
                    {"_id": 11, "level": 2, "data": "restricted"},
                ],
            }
        ],
        msg="$lookup $redact with let var should keep/prune docs based on access level",
    ),
]

# --- Section 6: Let Variables in $replaceRoot ---

LOOKUP_PROJECT_REPLACEROOT_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "replaceRoot_with_let_var",
        docs=[{"_id": 1, "context": "outer_ctx"}],
        foreign_docs=[{"_id": 10, "data": "foreign_data"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"ctx": "$context"},
                    "pipeline": [
                        {
                            "$replaceRoot": {
                                "newRoot": {
                                    "originalData": "$data",
                                    "fromOuter": "$$ctx",
                                }
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
                "context": "outer_ctx",
                "joined": [{"originalData": "foreign_data", "fromOuter": "outer_ctx"}],
            }
        ],
        msg="$lookup $replaceRoot with let var should include it in the new root document",
    ),
]

# --- Section 7: Type Preservation Through $addFields ---

_OID = ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")
_DATE = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

LOOKUP_PROJECT_TYPE_PRESERVATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "type_preservation_int_through_addFields",
        docs=[{"_id": 1, "v": 42}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$v"},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "v": 42, "joined": [{"_id": 10, "val": 42, "t": "int"}]}],
        msg="$lookup let var int type should be preserved through $addFields in sub-pipeline",
    ),
    LookupTestCase(
        "type_preservation_decimal128_through_addFields",
        docs=[{"_id": 1, "v": Decimal128("99.99")}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$v"},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "v": Decimal128("99.99"),
                "joined": [{"_id": 10, "val": Decimal128("99.99"), "t": "decimal"}],
            }
        ],
        msg="$lookup let var Decimal128 type should be preserved through $addFields",
    ),
    LookupTestCase(
        "type_preservation_date_through_addFields",
        docs=[{"_id": 1, "v": _DATE}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$v"},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "v": _DATE, "joined": [{"_id": 10, "val": _DATE, "t": "date"}]}],
        msg="$lookup let var date type should be preserved through $addFields",
    ),
    LookupTestCase(
        "type_preservation_objectid_through_addFields",
        docs=[{"_id": 1, "v": _OID}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$v"},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "v": _OID, "joined": [{"_id": 10, "val": _OID, "t": "objectId"}]}],
        msg="$lookup let var ObjectId type should be preserved through $addFields",
    ),
    LookupTestCase(
        "type_preservation_long_through_addFields",
        docs=[{"_id": 1, "v": Int64(123456789012)}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$v"},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "v": Int64(123456789012),
                "joined": [{"_id": 10, "val": Int64(123456789012), "t": "long"}],
            }
        ],
        msg="$lookup let var Int64 type should be preserved through $addFields",
    ),
]


# --- Combine all tests ---
LOOKUP_CORRELATED_PROJECT_ALL: list[LookupTestCase] = (
    LOOKUP_PROJECT_BASIC_TESTS
    + LOOKUP_PROJECT_CONDITIONAL_TESTS
    + LOOKUP_PROJECT_ARRAY_STRING_TESTS
    + LOOKUP_PROJECT_GROUP_TESTS
    + LOOKUP_PROJECT_REDACT_TESTS
    + LOOKUP_PROJECT_REPLACEROOT_TESTS
    + LOOKUP_PROJECT_TYPE_PRESERVATION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CORRELATED_PROJECT_ALL))
def test_lookup_correlated_project(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery let variables in $project/$addFields and other stages."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
