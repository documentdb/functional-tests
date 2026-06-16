"""Tests for collation effects on expression operators in aggregate."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Operators Affected by Collation]: comparison and set
# expression operators use command-level collation for string comparisons.
COLLATION_EXPR_OPS_AFFECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_eq_affected",
        docs=[{"_id": 1, "a": "apple", "b": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$eq": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": True}],
        msg="$eq expression should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "expr_ne_affected",
        docs=[{"_id": 1, "a": "apple", "b": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$ne": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": False}],
        msg="$ne expression should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "expr_gt_affected",
        docs=[{"_id": 1, "a": "apple", "b": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$gt": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": False}],
        msg="$gt expression should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "expr_gte_affected",
        docs=[{"_id": 1, "a": "apple", "b": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$gte": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": True}],
        msg="$gte expression should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "expr_lt_affected",
        docs=[{"_id": 1, "a": "apple", "b": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$lt": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": False}],
        msg="$lt expression should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "expr_lte_affected",
        docs=[{"_id": 1, "a": "apple", "b": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$lte": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": True}],
        msg="$lte expression should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "expr_cmp_affected",
        docs=[{"_id": 1, "a": "apple", "b": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$cmp": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": 0}],
        msg="$cmp expression should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "expr_in_affected",
        docs=[{"_id": 1, "arr": ["Apple", "Banana", "Cherry"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$in": ["apple", "$arr"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": True}],
        msg="$in expression should use collation for case-insensitive membership test",
    ),
    CommandTestCase(
        "expr_indexofarray_affected",
        docs=[{"_id": 1, "arr": ["Apple", "Banana", "Cherry"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$indexOfArray": ["$arr", "apple"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": 0}],
        msg="$indexOfArray should use collation for case-insensitive search",
    ),
    CommandTestCase(
        "expr_setequals_affected",
        docs=[{"_id": 1, "arr": ["Apple", "Banana"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$setEquals": ["$arr", ["apple", "banana"]]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": True}],
        msg="$setEquals should use collation for case-insensitive set comparison",
    ),
    CommandTestCase(
        "expr_setintersection_affected",
        docs=[{"_id": 1, "a": ["Apple", "Banana"], "b": ["apple", "cherry"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$setIntersection": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": ["Apple"]}],
        msg="$setIntersection should use collation for case-insensitive intersection",
    ),
    CommandTestCase(
        "expr_setdifference_affected",
        docs=[{"_id": 1, "a": ["Apple", "Banana"], "b": ["apple"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$setDifference": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": ["Banana"]}],
        msg="$setDifference should use collation for case-insensitive difference",
    ),
    CommandTestCase(
        "expr_setunion_affected",
        docs=[{"_id": 1, "a": ["Apple", "Banana"], "b": ["apple", "cherry"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$setUnion": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": ["Apple", "Banana", "cherry"]}],
        msg="$setUnion should use collation to deduplicate case variants",
    ),
    CommandTestCase(
        "expr_setissubset_affected",
        docs=[{"_id": 1, "arr": ["Apple", "Banana"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$setIsSubset": [["apple", "banana"], "$arr"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": True}],
        msg="$setIsSubset should use collation for case-insensitive subset check",
    ),
    CommandTestCase(
        "expr_filter_affected",
        docs=[{"_id": 1, "items": ["Apple", "banana", "apple"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$filter": {
                                "input": "$items",
                                "as": "item",
                                "cond": {"$eq": ["$$item", "apple"]},
                            }
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": ["Apple", "apple"]}],
        msg="$filter should use collation in its condition expression",
    ),
    CommandTestCase(
        "expr_reduce_affected",
        docs=[{"_id": 1, "items": ["Apple", "Banana", "Cherry"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$reduce": {
                                "input": "$items",
                                "initialValue": 0,
                                "in": {
                                    "$cond": {
                                        "if": {"$eq": ["$$this", "apple"]},
                                        "then": {"$add": ["$$value", 1]},
                                        "else": "$$value",
                                    }
                                },
                            }
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": 1}],
        msg="$reduce should use collation in its body expression",
    ),
    CommandTestCase(
        "expr_map_affected",
        docs=[{"_id": 1, "items": ["Apple", "Banana", "Cherry"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$map": {
                                "input": "$items",
                                "as": "item",
                                "in": {"$eq": ["$$item", "apple"]},
                            }
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": [True, False, False]}],
        msg="$map should use collation in its body expression",
    ),
    CommandTestCase(
        "expr_cond_affected",
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$cond": {
                                "if": {"$eq": ["$x", "apple"]},
                                "then": "matched",
                                "else": "no match",
                            }
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": "matched"}],
        msg="$cond should use collation in its condition expression",
    ),
    CommandTestCase(
        "expr_switch_affected",
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {"$eq": ["$x", "apple"]},
                                        "then": "matched",
                                    }
                                ],
                                "default": "no match",
                            }
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": "matched"}],
        msg="$switch should use collation in its branch condition expressions",
    ),
]

# Property [Expression Operators Not Affected by Collation]: string
# manipulation and regex operators always use binary comparison regardless of
# command-level collation.
COLLATION_EXPR_OPS_NOT_AFFECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_indexofbytes_not_affected",
        docs=[{"_id": 1, "x": "Hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$indexOfBytes": ["$x", "hello"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": -1}],
        msg="$indexOfBytes should not use collation for string search",
    ),
    CommandTestCase(
        "expr_indexofcp_not_affected",
        docs=[{"_id": 1, "x": "Hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$indexOfCP": ["$x", "hello"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": -1}],
        msg="$indexOfCP should not use collation for string search",
    ),
    CommandTestCase(
        "expr_regexmatch_not_affected",
        docs=[{"_id": 1, "x": "Hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"result": {"$regexMatch": {"input": "$x", "regex": "hello"}}}}
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": False}],
        msg="$regexMatch should not use collation for pattern matching",
    ),
    CommandTestCase(
        "expr_regexfind_not_affected",
        docs=[{"_id": 1, "x": "Hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"result": {"$regexFind": {"input": "$x", "regex": "hello"}}}}
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": None}],
        msg="$regexFind should not use collation for pattern matching",
    ),
    CommandTestCase(
        "expr_regexfindall_not_affected",
        docs=[{"_id": 1, "x": "Hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"result": {"$regexFindAll": {"input": "$x", "regex": "hello"}}}}
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": []}],
        msg="$regexFindAll should not use collation for pattern matching",
    ),
    CommandTestCase(
        "expr_replaceone_not_affected",
        docs=[{"_id": 1, "x": "Hello World"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$replaceOne": {
                                "input": "$x",
                                "find": "hello",
                                "replacement": "hi",
                            }
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": "Hello World"}],
        msg="$replaceOne should not use collation for find matching",
    ),
    CommandTestCase(
        "expr_replaceall_not_affected",
        docs=[{"_id": 1, "x": "Hello Hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$replaceAll": {
                                "input": "$x",
                                "find": "hello",
                                "replacement": "hi",
                            }
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": "Hello Hello"}],
        msg="$replaceAll should not use collation for find matching",
    ),
    CommandTestCase(
        "expr_strcasecmp_not_affected",
        docs=[{"_id": 1, "a": "cafe", "b": "caf\u00e9"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$strcasecmp": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # $strcasecmp only folds case, not diacritics. Collation at strength 1
        # would treat "cafe" and "caf\u00e9" as equal, but $strcasecmp should not.
        expected=[{"_id": 1, "result": -1}],
        msg="$strcasecmp should not be affected by collation",
    ),
    CommandTestCase(
        "expr_split_not_affected",
        docs=[{"_id": 1, "x": "Hello World"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$split": ["$x", "hello"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": ["Hello World"]}],
        msg="$split should not use collation for delimiter matching",
    ),
    CommandTestCase(
        "expr_tolower_not_affected",
        docs=[{"_id": 1, "x": "I"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$toLower": "$x"}}}],
            "cursor": {},
            "collation": {"locale": "tr", "strength": 1},
        },
        # Turkish locale would map I -> \u0131 (dotless i), but $toLower uses
        # simple Unicode folding (I -> i), proving collation is ignored.
        expected=[{"_id": 1, "result": "i"}],
        msg="$toLower should perform simple Unicode case folding regardless of collation locale",
    ),
    CommandTestCase(
        "expr_toupper_not_affected",
        docs=[{"_id": 1, "x": "i"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$toUpper": "$x"}}}],
            "cursor": {},
            "collation": {"locale": "tr", "strength": 1},
        },
        # Turkish locale would map i -> \u0130 (I with dot above), but $toUpper
        # uses simple Unicode folding (i -> I), proving collation is ignored.
        expected=[{"_id": 1, "result": "I"}],
        msg="$toUpper should perform simple Unicode case folding regardless of collation locale",
    ),
    CommandTestCase(
        "expr_concat_not_affected",
        docs=[{"_id": 1, "a": "Hello", "b": "World"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$concat": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": "HelloWorld"}],
        msg="$concat should concatenate without collation influence",
    ),
    CommandTestCase(
        "expr_substrbytes_not_affected",
        docs=[{"_id": 1, "x": "caf\u00e9"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$substrBytes": ["$x", 0, 3]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": "caf"}],
        msg="$substrBytes should use byte offsets regardless of collation",
    ),
    CommandTestCase(
        "expr_substrcp_not_affected",
        docs=[{"_id": 1, "x": "caf\u00e9"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$substrCP": ["$x", 0, 3]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": "caf"}],
        msg="$substrCP should use code point offsets regardless of collation",
    ),
    CommandTestCase(
        "expr_strlenbytes_not_affected",
        docs=[{"_id": 1, "x": "caf\u00e9"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$strLenBytes": "$x"}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": 5}],
        msg="$strLenBytes should count bytes regardless of collation",
    ),
    CommandTestCase(
        "expr_strlencp_not_affected",
        docs=[{"_id": 1, "x": "caf\u00e9"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$strLenCP": "$x"}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "result": 4}],
        msg="$strLenCP should count code points regardless of collation",
    ),
]

# Property [$expr $in Asymmetry]: $expr with $in using a field reference as
# the first argument in $match does not use collation, but a literal first
# argument does, and $project/$addFields use collation regardless of argument
# form.
COLLATION_EXPR_IN_ASYMMETRY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_in_match_field_ref_no_collation",
        docs=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"$expr": {"$in": ["$x", ["Apple", "Banana"]]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[],
        msg="$expr $in with field ref first arg in $match should not use collation",
    ),
    CommandTestCase(
        "expr_in_match_literal_uses_collation",
        docs=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"$expr": {"$in": ["apple", "$arr"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        msg="$expr $in with literal first arg in $match should use collation",
    ),
    CommandTestCase(
        "expr_in_project_field_ref_uses_collation",
        docs=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$in": ["$x", ["Apple", "Banana"]]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "result": True},
            {"_id": 2, "result": False},
        ],
        msg="$expr $in with field ref in $project should use collation",
    ),
    CommandTestCase(
        "expr_in_addfields_field_ref_uses_collation",
        docs=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"]},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"result": {"$in": ["$x", ["Apple", "Banana"]]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "apple", "arr": ["Apple", "Banana"], "result": True},
            {"_id": 2, "x": "grape", "arr": ["Apple", "Banana"], "result": False},
        ],
        msg="$expr $in with field ref in $addFields should use collation",
    ),
]

# Property [$max/$min Expression Collation]: $max and $min expression operators
# use command-level collation for string comparisons, returning the
# linguistically largest or smallest value.
COLLATION_EXPR_MAX_MIN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_max_affected",
        docs=[{"_id": 1, "a": "a", "b": "B"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$max": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Linguistic: a < b, so max is "B".
        expected=[{"_id": 1, "result": "B"}],
        msg="$max expression should use collation for string comparison",
    ),
    CommandTestCase(
        "expr_max_no_collation_binary",
        docs=[{"_id": 1, "a": "a", "b": "B"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$max": ["$a", "$b"]}}}],
            "cursor": {},
        },
        # Binary: 'B'(66) < 'a'(97), so max is "a".
        expected=[{"_id": 1, "result": "a"}],
        msg="$max expression without collation should use binary comparison",
    ),
    CommandTestCase(
        "expr_min_affected",
        docs=[{"_id": 1, "a": "a", "b": "B"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$min": ["$a", "$b"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Linguistic: a < b, so min is "a".
        expected=[{"_id": 1, "result": "a"}],
        msg="$min expression should use collation for string comparison",
    ),
    CommandTestCase(
        "expr_min_no_collation_binary",
        docs=[{"_id": 1, "a": "a", "b": "B"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$min": ["$a", "$b"]}}}],
            "cursor": {},
        },
        # Binary: 'B'(66) < 'a'(97), so min is "B".
        expected=[{"_id": 1, "result": "B"}],
        msg="$min expression without collation should use binary comparison",
    ),
]

# Property [$maxN/$minN Array Expression Collation]: $maxN and $minN array
# expression operators use command-level collation for string comparisons when
# selecting the N largest or smallest elements.
COLLATION_EXPR_MAXN_MINN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_maxn_affected",
        docs=[{"_id": 1, "arr": ["a", "B", "c", "D"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$maxN": {"n": 2, "input": "$arr"}}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Linguistic: a < b < c < d, so maxN(2) = ["D", "c"].
        expected=[{"_id": 1, "result": ["D", "c"]}],
        msg="$maxN array expression should use collation for string comparison",
    ),
    CommandTestCase(
        "expr_maxn_no_collation_binary",
        docs=[{"_id": 1, "arr": ["a", "B", "c", "D"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$maxN": {"n": 2, "input": "$arr"}}}}],
            "cursor": {},
        },
        # Binary: 'B'(66) < 'D'(68) < 'a'(97) < 'c'(99), so maxN(2) = ["c", "a"].
        expected=[{"_id": 1, "result": ["c", "a"]}],
        msg="$maxN array expression without collation should use binary comparison",
    ),
    CommandTestCase(
        "expr_minn_affected",
        docs=[{"_id": 1, "arr": ["a", "B", "c", "D"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$minN": {"n": 2, "input": "$arr"}}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Linguistic: a < b < c < d, so minN(2) = ["a", "B"].
        expected=[{"_id": 1, "result": ["a", "B"]}],
        msg="$minN array expression should use collation for string comparison",
    ),
    CommandTestCase(
        "expr_minn_no_collation_binary",
        docs=[{"_id": 1, "arr": ["a", "B", "c", "D"]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"result": {"$minN": {"n": 2, "input": "$arr"}}}}],
            "cursor": {},
        },
        # Binary: 'B'(66) < 'D'(68) < 'a'(97) < 'c'(99), so minN(2) = ["B", "D"].
        expected=[{"_id": 1, "result": ["B", "D"]}],
        msg="$minN array expression without collation should use binary comparison",
    ),
]

COLLATION_AGGREGATE_EXPRESSIONS_TESTS: list[CommandTestCase] = (
    COLLATION_EXPR_OPS_AFFECTED_TESTS
    + COLLATION_EXPR_OPS_NOT_AFFECTED_TESTS
    + COLLATION_EXPR_IN_ASYMMETRY_TESTS
    + COLLATION_EXPR_MAX_MIN_TESTS
    + COLLATION_EXPR_MAXN_MINN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_EXPRESSIONS_TESTS))
def test_collation_aggregate_expressions(database_client, collection, test):
    """Test collation effects on expression operators in aggregate."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
