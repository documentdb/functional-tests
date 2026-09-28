"""Tests for let variable scoping across nested $lookup sub-pipelines with concise outer.

Covers multi-level propagation, shadowing when an inner let reuses a name,
scope isolation between sibling or same-named contexts, and undefined-variable
errors - all with the outer $lookup using concise syntax (localField + foreignField
+ pipeline).
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import LET_UNDEFINED_VARIABLE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Concise Nested Let Propagation]: outer let variables from a concise
# $lookup remain accessible in deeply nested sub-pipelines.
LOOKUP_CONCISE_NESTED_PROPAGATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "outer_let_accessible_in_doubly_nested",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "val": "from_outer"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"x": "$val"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [
                                    {
                                        "$lookup": {
                                            "from": FOREIGN,
                                            "pipeline": [{"$addFields": {"deep": "$$x"}}],
                                            "as": "level3",
                                        }
                                    }
                                ],
                                "as": "level2",
                            }
                        }
                    ],
                    "as": "level1",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "val": "from_outer",
                "level1": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "level2": [
                            {
                                "_id": 10,
                                "ff": "a",
                                "level3": [{"_id": 10, "ff": "a", "deep": "from_outer"}],
                            }
                        ],
                    }
                ],
            }
        ],
        msg="$lookup concise outer let var should be accessible in a triply-nested sub-pipeline",
    ),
    LookupTestCase(
        "outer_and_inner_let_both_accessible",
        foreign_docs=[{"_id": 10, "ff": "a", "b": "inner_b"}],
        docs=[{"_id": 1, "lf": "a", "a": "outer_a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"x": "$a"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"y": "$b"},
                                "pipeline": [
                                    {"$addFields": {"from_outer": "$$x", "from_inner": "$$y"}}
                                ],
                                "as": "nested",
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
                "lf": "a",
                "a": "outer_a",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "b": "inner_b",
                        "nested": [
                            {
                                "_id": 10,
                                "ff": "a",
                                "b": "inner_b",
                                "from_outer": "outer_a",
                                "from_inner": "inner_b",
                            }
                        ],
                    }
                ],
            }
        ],
        msg="$lookup concise nested let should keep both the outer and inner "
        "variables accessible at the innermost level",
    ),
    LookupTestCase(
        "inner_let_defined_from_outer_var",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "a": "outer"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"x": "$a"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"y": {"$concat": ["$$x", "!"]}},
                                "pipeline": [{"$addFields": {"r": "$$y"}}],
                                "as": "inner",
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
                "lf": "a",
                "a": "outer",
                "joined": [
                    {"_id": 10, "ff": "a", "inner": [{"_id": 10, "ff": "a", "r": "outer!"}]}
                ],
            }
        ],
        msg="$lookup concise inner let defining expression should resolve an outer "
        "let variable from the enclosing scope",
    ),
    LookupTestCase(
        "outer_let_in_inner_match_expr",
        foreign_docs=[
            {"_id": 10, "ff": "a", "tag": "target"},
            {"_id": 11, "ff": "a", "tag": "other"},
        ],
        docs=[{"_id": 1, "lf": "a", "ref": "target"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"r": "$ref"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [{"$match": {"$expr": {"$eq": ["$tag", "$$r"]}}}],
                                "as": "inner_match",
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
                "lf": "a",
                "ref": "target",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "tag": "target",
                        "inner_match": [{"_id": 10, "ff": "a", "tag": "target"}],
                    },
                    {
                        "_id": 11,
                        "ff": "a",
                        "tag": "other",
                        "inner_match": [{"_id": 10, "ff": "a", "tag": "target"}],
                    },
                ],
            }
        ],
        msg="$lookup concise outer let var should be usable in a $match $expr "
        "inside a nested sub-pipeline",
    ),
    LookupTestCase(
        "three_levels_each_with_own_let",
        foreign_docs=[{"_id": 10, "ff": "a", "b": "L2", "c": "L3"}],
        docs=[{"_id": 1, "lf": "a", "a": "L1"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"v1": "$a"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"v2": "$b"},
                                "pipeline": [
                                    {
                                        "$lookup": {
                                            "from": FOREIGN,
                                            "let": {"v3": "$c"},
                                            "pipeline": [
                                                {
                                                    "$addFields": {
                                                        "r1": "$$v1",
                                                        "r2": "$$v2",
                                                        "r3": "$$v3",
                                                    }
                                                }
                                            ],
                                            "as": "deep",
                                        }
                                    }
                                ],
                                "as": "mid",
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
                "lf": "a",
                "a": "L1",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "b": "L2",
                        "c": "L3",
                        "mid": [
                            {
                                "_id": 10,
                                "ff": "a",
                                "b": "L2",
                                "c": "L3",
                                "deep": [
                                    {
                                        "_id": 10,
                                        "ff": "a",
                                        "b": "L2",
                                        "c": "L3",
                                        "r1": "L1",
                                        "r2": "L2",
                                        "r3": "L3",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        msg="$lookup concise 3-level nesting where each level defines its own let "
        "should expose all three at the deepest level",
    ),
    LookupTestCase(
        "inner_let_references_field_from_addFields",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "base": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"b": "$base"},
                    "pipeline": [
                        {"$addFields": {"computed": {"$multiply": ["$$b", 2]}}},
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"c": "$computed"},
                                "pipeline": [{"$addFields": {"result": "$$c"}}],
                                "as": "inner",
                            }
                        },
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "base": 10,
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "computed": 20,
                        "inner": [{"_id": 10, "ff": "a", "result": 20}],
                    }
                ],
            }
        ],
        msg="$lookup concise inner let should be able to reference a field created "
        "by a preceding $addFields",
    ),
    LookupTestCase(
        "nested_concise_inside_concise",
        foreign_docs=[
            {"_id": 10, "ff": "a", "nf": "x"},
            {"_id": 11, "ff": "a", "nf": "y"},
            {"_id": 12, "ff": "b", "nf": "x"},
        ],
        docs=[{"_id": 1, "lf": "a", "extra": "E"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"e": "$extra"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "localField": "nf",
                                "foreignField": "nf",
                                "pipeline": [{"$addFields": {"outer_extra": "$$e"}}],
                                "as": "inner",
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
                "lf": "a",
                "extra": "E",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "nf": "x",
                        "inner": [
                            {"_id": 10, "ff": "a", "nf": "x", "outer_extra": "E"},
                            {"_id": 12, "ff": "b", "nf": "x", "outer_extra": "E"},
                        ],
                    },
                    {
                        "_id": 11,
                        "ff": "a",
                        "nf": "y",
                        "inner": [{"_id": 11, "ff": "a", "nf": "y", "outer_extra": "E"}],
                    },
                ],
            }
        ],
        msg="$lookup concise nested inside concise should propagate outer let vars "
        "and apply both equality prefilters",
    ),
]

# Property [Concise Nested Let Shadowing]: an inner let that reuses an outer
# variable name shadows it within the inner scope, and the shadow does not leak
# upward - with the outer $lookup using concise syntax.
LOOKUP_CONCISE_NESTED_SHADOW_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "inner_shadow_defined_from_outer_value",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "a": "outer"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"x": "$a"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": {"$concat": ["$$x", "_inner"]}},
                                "pipeline": [{"$addFields": {"r": "$$x"}}],
                                "as": "inner",
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
                "lf": "a",
                "a": "outer",
                "joined": [
                    {"_id": 10, "ff": "a", "inner": [{"_id": 10, "ff": "a", "r": "outer_inner"}]}
                ],
            }
        ],
        msg="$lookup concise inner let redefining a name from its own outer value "
        "should read the outer value before the shadow takes effect",
    ),
    LookupTestCase(
        "progressive_shadow_three_levels",
        foreign_docs=[{"_id": 10, "ff": "a", "v": "L2"}],
        docs=[{"_id": 1, "lf": "a", "v": "L1"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"x": "$v"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "$v"},
                                "pipeline": [
                                    {
                                        "$lookup": {
                                            "from": FOREIGN,
                                            "let": {"x": "deepest"},
                                            "pipeline": [{"$addFields": {"val": "$$x"}}],
                                            "as": "l3",
                                        }
                                    }
                                ],
                                "as": "l2",
                            }
                        }
                    ],
                    "as": "l1",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "v": "L1",
                "l1": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "v": "L2",
                        "l2": [
                            {
                                "_id": 10,
                                "ff": "a",
                                "v": "L2",
                                "l3": [{"_id": 10, "ff": "a", "v": "L2", "val": "deepest"}],
                            }
                        ],
                    }
                ],
            }
        ],
        msg="$lookup concise triple progressive shadow should let the deepest level "
        "see its own redefined value",
    ),
    LookupTestCase(
        "partial_shadow_inner_redefines_one_of_two",
        foreign_docs=[{"_id": 10, "ff": "a", "c": "inner_c"}],
        docs=[{"_id": 1, "lf": "a", "a": "outer_a", "b": "outer_b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"x": "$a", "y": "$b"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "$c"},
                                "pipeline": [{"$addFields": {"rx": "$$x", "ry": "$$y"}}],
                                "as": "nested",
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
                "lf": "a",
                "a": "outer_a",
                "b": "outer_b",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "c": "inner_c",
                        "nested": [
                            {"_id": 10, "ff": "a", "c": "inner_c", "rx": "inner_c", "ry": "outer_b"}
                        ],
                    }
                ],
            }
        ],
        msg="$lookup concise inner let redefining only x should shadow x while "
        "outer y remains accessible",
    ),
    LookupTestCase(
        "shadow_does_not_leak_up",
        foreign_docs=[{"_id": 10, "ff": "a", "inner_val": "shadowed"}],
        docs=[{"_id": 1, "lf": "a", "val": "outer_val"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"x": "$val"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "$inner_val"},
                                "pipeline": [{"$addFields": {"inner_x": "$$x"}}],
                                "as": "inner",
                            }
                        },
                        {"$addFields": {"after_inner_x": "$$x"}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "val": "outer_val",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "inner_val": "shadowed",
                        "inner": [
                            {"_id": 10, "ff": "a", "inner_val": "shadowed", "inner_x": "shadowed"}
                        ],
                        "after_inner_x": "outer_val",
                    }
                ],
            }
        ],
        msg="$lookup concise inner shadow should not leak upward, so the outer "
        "scope keeps its original value",
    ),
    LookupTestCase(
        "shadow_with_different_type",
        foreign_docs=[{"_id": 10, "ff": "a", "x": "hello"}],
        docs=[{"_id": 1, "lf": "a", "x": 42}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"v": "$x"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"v": "$x"},
                                "pipeline": [{"$addFields": {"val": "$$v", "t": {"$type": "$$v"}}}],
                                "as": "nested",
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
                "lf": "a",
                "x": 42,
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "x": "hello",
                        "nested": [
                            {"_id": 10, "ff": "a", "x": "hello", "val": "hello", "t": "string"}
                        ],
                    }
                ],
            }
        ],
        msg="$lookup concise inner shadow can change a variable's type, with an "
        "outer int shadowed by an inner string",
    ),
]

# Property [Concise Nested Scope Isolation]: same-named let variables in sibling
# nested contexts within a concise $lookup pipeline remain isolated to their own
# scope.
LOOKUP_CONCISE_NESTED_ISOLATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "sibling_nested_lookups_isolate_same_named_var",
        foreign_docs=[
            {"_id": 10, "ff": "a", "tag": "p"},
            {"_id": 11, "ff": "a", "tag": "q"},
        ],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "pipeline": [
                        {"$match": {"_id": 10}},
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "p"},
                                "pipeline": [{"$match": {"$expr": {"$eq": ["$tag", "$$x"]}}}],
                                "as": "branch_a",
                            }
                        },
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "q"},
                                "pipeline": [{"$match": {"$expr": {"$eq": ["$tag", "$$x"]}}}],
                                "as": "branch_b",
                            }
                        },
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "tag": "p",
                        "branch_a": [{"_id": 10, "ff": "a", "tag": "p"}],
                        "branch_b": [{"_id": 11, "ff": "a", "tag": "q"}],
                    }
                ],
            }
        ],
        msg="$lookup concise sibling nested lookups should isolate a same-named "
        "let variable to each branch",
    ),
    LookupTestCase(
        "sibling_var_undefined_in_other_branch",
        foreign_docs=[{"_id": 10, "ff": "a", "tag": "p"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "pipeline": [
                        {"$match": {"_id": 10}},
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "p"},
                                "pipeline": [{"$match": {}}],
                                "as": "branch_a",
                            }
                        },
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [{"$addFields": {"r": "$$x"}}],
                                "as": "branch_b",
                            }
                        },
                    ],
                    "as": "joined",
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$lookup concise should treat a let variable defined only in a sibling "
        "branch as undefined in the other branch",
    ),
]

# Property [Concise Nested Undefined Variable]: referencing a variable never
# defined at any enclosing level produces an undefined variable error - with the
# outer $lookup using concise syntax.
LOOKUP_CONCISE_NESTED_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "missing_var_at_one_level_errors",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"o": "O"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [
                                    {
                                        "$lookup": {
                                            "from": FOREIGN,
                                            "let": {"i": "I"},
                                            "pipeline": [
                                                {
                                                    "$addFields": {
                                                        "combined": {
                                                            "$concat": ["$$o", "$$m", "$$i"]
                                                        }
                                                    }
                                                }
                                            ],
                                            "as": "lvl3",
                                        }
                                    }
                                ],
                                "as": "lvl2",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$lookup concise referencing a never-defined variable at a nesting "
        "level should error",
    ),
]

LOOKUP_CONCISE_NESTED_TESTS: list[LookupTestCase] = (
    LOOKUP_CONCISE_NESTED_PROPAGATION_TESTS
    + LOOKUP_CONCISE_NESTED_SHADOW_TESTS
    + LOOKUP_CONCISE_NESTED_ISOLATION_TESTS
    + LOOKUP_CONCISE_NESTED_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CONCISE_NESTED_TESTS))
def test_concise_nested_lookup(collection, test_case: LookupTestCase):
    """Test let variable scoping across nested $lookup sub-pipelines with concise outer."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
