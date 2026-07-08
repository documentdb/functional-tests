"""Tests for $lookup correlated subquery — nested $lookup scoping and propagation.

Covers let variable behavior across nested $lookup stages: multi-level
propagation, shadowing semantics, correlated $match in inner lookups,
concise syntax interaction, and structure verification.
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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Section 1: Multi-Level Let Propagation ---
# Existing coverage: basic propagation (1 level), basic shadow (1 level)
# New coverage: 3-level propagation, outer+inner let coexistence, outer let in inner $match

LOOKUP_NESTED_PROPAGATION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "outer_let_accessible_in_doubly_nested",
        docs=[{"_id": 1, "val": "from_outer"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "val": "from_outer",
                "level1": [
                    {
                        "_id": 10,
                        "level2": [
                            {
                                "_id": 10,
                                "level3": [{"_id": 10, "deep": "from_outer"}],
                            }
                        ],
                    }
                ],
            }
        ],
        msg="$lookup outer let var should be accessible in a triply-nested sub-pipeline (L3)",
    ),
    LookupTestCase(
        "outer_and_inner_let_both_accessible",
        docs=[{"_id": 1, "a": "outer_a"}],
        foreign_docs=[{"_id": 10, "b": "inner_b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$a"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"y": "$b"},
                                "pipeline": [
                                    {
                                        "$addFields": {
                                            "from_outer": "$$x",
                                            "from_inner": "$$y",
                                        }
                                    }
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
                "a": "outer_a",
                "joined": [
                    {
                        "_id": 10,
                        "b": "inner_b",
                        "nested": [
                            {
                                "_id": 10,
                                "b": "inner_b",
                                "from_outer": "outer_a",
                                "from_inner": "inner_b",
                            }
                        ],
                    }
                ],
            }
        ],
        msg=(
            "$lookup nested let should allow both outer $$x and inner"
            " $$y to be accessible in the innermost pipeline"
        ),
    ),
    LookupTestCase(
        "outer_let_in_inner_match_expr",
        docs=[{"_id": 1, "ref": "target"}],
        foreign_docs=[
            {"_id": 10, "tag": "target"},
            {"_id": 11, "tag": "other"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "ref": "target",
                "joined": [
                    {
                        "_id": 10,
                        "tag": "target",
                        "inner_match": [{"_id": 10, "tag": "target"}],
                    },
                    {
                        "_id": 11,
                        "tag": "other",
                        "inner_match": [{"_id": 10, "tag": "target"}],
                    },
                ],
            }
        ],
        msg=(
            "$lookup outer let var should be usable in $match $expr"
            " inside a nested $lookup sub-pipeline"
        ),
    ),
    LookupTestCase(
        "three_levels_each_with_own_let",
        docs=[{"_id": 1, "a": "L1"}],
        foreign_docs=[{"_id": 10, "b": "L2", "c": "L3"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "a": "L1",
                "joined": [
                    {
                        "_id": 10,
                        "b": "L2",
                        "c": "L3",
                        "mid": [
                            {
                                "_id": 10,
                                "b": "L2",
                                "c": "L3",
                                "deep": [
                                    {
                                        "_id": 10,
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
        msg=(
            "$lookup 3-level nesting where each level defines its own let"
            " should make all three variables accessible at the deepest level"
        ),
    ),
]

# --- Section 2: Let Shadowing in Nested Lookups ---
# Existing coverage: basic inner shadow overwrites outer
# New: partial shadow, shadow doesn't leak up, progressive shadow, type change in shadow

LOOKUP_NESTED_SHADOW_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "partial_shadow_inner_redefines_one_of_two",
        docs=[{"_id": 1, "a": "outer_a", "b": "outer_b"}],
        foreign_docs=[{"_id": 10, "c": "inner_c"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$a", "y": "$b"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "$c"},
                                "pipeline": [
                                    {
                                        "$addFields": {
                                            "rx": "$$x",
                                            "ry": "$$y",
                                        }
                                    }
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
                "a": "outer_a",
                "b": "outer_b",
                "joined": [
                    {
                        "_id": 10,
                        "c": "inner_c",
                        "nested": [
                            {
                                "_id": 10,
                                "c": "inner_c",
                                "rx": "inner_c",
                                "ry": "outer_b",
                            }
                        ],
                    }
                ],
            }
        ],
        msg=(
            "$lookup inner let redefining only x should shadow x"
            " while outer y remains accessible"
        ),
    ),
    LookupTestCase(
        "shadow_does_not_leak_up",
        docs=[{"_id": 1, "val": "outer_val"}],
        foreign_docs=[{"_id": 10, "inner_val": "shadowed"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "val": "outer_val",
                "joined": [
                    {
                        "_id": 10,
                        "inner_val": "shadowed",
                        "inner": [{"_id": 10, "inner_val": "shadowed", "inner_x": "shadowed"}],
                        "after_inner_x": "outer_val",
                    }
                ],
            }
        ],
        msg=(
            "$lookup inner shadow should not leak upward — after inner"
            " lookup exits, outer scope sees original $$x value"
        ),
    ),
    LookupTestCase(
        "progressive_shadow_three_levels",
        docs=[{"_id": 1, "v": "L1"}],
        foreign_docs=[{"_id": 10, "v": "L2"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "v": "L1",
                "l1": [
                    {
                        "_id": 10,
                        "v": "L2",
                        "l2": [
                            {
                                "_id": 10,
                                "v": "L2",
                                "l3": [{"_id": 10, "v": "L2", "val": "deepest"}],
                            }
                        ],
                    }
                ],
            }
        ],
        msg=(
            "$lookup triple progressive shadow: each level redefines $$x,"
            " deepest sees its own value"
        ),
    ),
    LookupTestCase(
        "shadow_with_different_type",
        docs=[{"_id": 1, "x": 42}],
        foreign_docs=[{"_id": 10, "x": "hello"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$x"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"v": "$x"},
                                "pipeline": [
                                    {
                                        "$addFields": {
                                            "val": "$$v",
                                            "t": {"$type": "$$v"},
                                        }
                                    }
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
                "x": 42,
                "joined": [
                    {
                        "_id": 10,
                        "x": "hello",
                        "nested": [{"_id": 10, "x": "hello", "val": "hello", "t": "string"}],
                    }
                ],
            }
        ],
        msg=(
            "$lookup inner shadow can change the type of a variable"
            " — outer int shadowed by inner string"
        ),
    ),
]

# --- Section 3: Nested Lookup Structure and Edge Cases ---

LOOKUP_NESTED_STRUCTURE_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "nested_result_is_array_of_docs_with_arrays",
        docs=[{"_id": 1, "ref": "a"}],
        foreign_docs=[
            {"_id": 10, "tag": "a", "sub_ref": "x"},
            {"_id": 11, "tag": "a", "sub_ref": "y"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"r": "$ref"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$tag", "$$r"]}}},
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"sr": "$sub_ref"},
                                "pipeline": [{"$match": {"$expr": {"$eq": ["$tag", "$$sr"]}}}],
                                "as": "deep",
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
                "ref": "a",
                "joined": [
                    {"_id": 10, "tag": "a", "sub_ref": "x", "deep": []},
                    {"_id": 11, "tag": "a", "sub_ref": "y", "deep": []},
                ],
            }
        ],
        msg=(
            "$lookup nested result should be array of docs each containing"
            " their own inner 'deep' array field"
        ),
    ),
    LookupTestCase(
        "inner_as_same_name_as_outer_no_conflict",
        docs=[{"_id": 1, "v": "outer"}],
        foreign_docs=[{"_id": 10, "v": "mid"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$v"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [{"$addFields": {"src": "$$x"}}],
                                "as": "joined",
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
                "v": "outer",
                "joined": [
                    {
                        "_id": 10,
                        "v": "mid",
                        "joined": [{"_id": 10, "v": "mid", "src": "outer"}],
                    }
                ],
            }
        ],
        msg=(
            "$lookup inner 'as' with same name as outer 'as' should"
            " not conflict — they exist in different document contexts"
        ),
    ),
    LookupTestCase(
        "inner_let_references_field_from_addFields",
        docs=[{"_id": 1, "base": 10}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "base": 10,
                "joined": [
                    {
                        "_id": 10,
                        "computed": 20,
                        "inner": [{"_id": 10, "result": 20}],
                    }
                ],
            }
        ],
        msg=(
            "$lookup inner let should be able to reference a field"
            " created by a preceding $addFields in the same sub-pipeline"
        ),
    ),
    LookupTestCase(
        "self_join_at_depth",
        docs=[
            {"_id": 1, "name": "root", "parent": None},
            {"_id": 2, "name": "child", "parent": 1},
        ],
        foreign_docs=[
            {"_id": 1, "name": "root", "parent": None},
            {"_id": 2, "name": "child", "parent": 1},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"pid": "$_id"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$parent", "$$pid"]}}}],
                    "as": "children",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "name": "root",
                "parent": None,
                "children": [{"_id": 2, "name": "child", "parent": 1}],
            },
            {"_id": 2, "name": "child", "parent": 1, "children": []},
        ],
        msg=(
            "$lookup correlated self-join should find children for each"
            " document where foreign parent == outer _id"
        ),
    ),
]


# --- Combine all tests ---
LOOKUP_CORRELATED_NESTED_ALL: list[LookupTestCase] = (
    LOOKUP_NESTED_PROPAGATION_TESTS + LOOKUP_NESTED_SHADOW_TESTS + LOOKUP_NESTED_STRUCTURE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CORRELATED_NESTED_ALL))
def test_lookup_correlated_nested(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery nested lookup scoping and propagation."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
