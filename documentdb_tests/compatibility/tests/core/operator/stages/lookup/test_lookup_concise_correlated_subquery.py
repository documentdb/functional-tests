"""Tests for $lookup concise syntax: equality prefilter composed with a sub-pipeline.

Covers concise-specific composition behavior (equality + pipeline) and let variable
behavior when used with concise syntax.
"""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Concise Composition]: when localField, foreignField, and pipeline
# are all specified, the equality match is applied first and the pipeline runs
# only on the matched foreign subset.
LOOKUP_CONCISE_COMPOSITION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "equality_match_then_pipeline_filters",
        foreign_docs=[
            {"_id": 10, "ff": "a", "val": 1},
            {"_id": 11, "ff": "a", "val": 2},
            {"_id": 12, "ff": "b", "val": 3},
            {"_id": 13, "ff": "b", "val": 4},
            {"_id": 14, "ff": "c", "val": 5},
        ],
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "b"},
            {"_id": 3, "lf": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "pipeline": [{"$match": {"val": {"$gte": 2}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "a", "joined": [{"_id": 11, "ff": "a", "val": 2}]},
            {
                "_id": 2,
                "lf": "b",
                "joined": [
                    {"_id": 12, "ff": "b", "val": 3},
                    {"_id": 13, "ff": "b", "val": 4},
                ],
            },
            {"_id": 3, "lf": "c", "joined": [{"_id": 14, "ff": "c", "val": 5}]},
        ],
        msg="$lookup concise should apply the equality match first then run the "
        "pipeline on the matched subset",
    ),
    LookupTestCase(
        "empty_pipeline_same_as_simple_equality",
        foreign_docs=[{"_id": 10, "ff": "val"}, {"_id": 11, "ff": "other"}],
        docs=[{"_id": 1, "lf": "val"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "val", "joined": [{"_id": 10, "ff": "val"}]}],
        msg="$lookup concise with an empty pipeline should behave like a simple equality lookup",
    ),
    LookupTestCase(
        "equality_no_match_pipeline_not_executed",
        foreign_docs=[{"_id": 10, "ff": "val1"}, {"_id": 11, "ff": "val2"}],
        docs=[{"_id": 1, "lf": "no_match"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"v": "$lf"},
                    "pipeline": [{"$addFields": {"src": "$$v"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "no_match", "joined": []}],
        msg="$lookup concise with no equality match should return an empty array "
        "without running the pipeline",
    ),
    LookupTestCase(
        "equality_evaluated_before_pipeline_transforms",
        foreign_docs=[{"_id": 10, "ff": "a", "val": 1}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "pipeline": [{"$project": {"val": 1}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": [{"_id": 10, "val": 1}]}],
        msg="$lookup concise should evaluate equality on original foreign documents "
        "before the pipeline removes the foreignField",
    ),
]

# Property [Concise Let Behavior]: let variables in concise syntax expose local
# document fields to the sub-pipeline for use in correlated filtering.
LOOKUP_CONCISE_LET_BEHAVIOR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_combined_with_equality_and_pipeline",
        foreign_docs=[
            {"_id": 10, "ff": "a", "val": 1},
            {"_id": 11, "ff": "a", "val": 2},
            {"_id": 12, "ff": "b", "val": 3},
        ],
        docs=[
            {"_id": 1, "lf": "a", "extra": "x"},
            {"_id": 2, "lf": "b", "extra": "y"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"local_extra": "$extra"},
                    "pipeline": [{"$addFields": {"from_local": "$$local_extra"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "extra": "x",
                "joined": [
                    {"_id": 10, "ff": "a", "val": 1, "from_local": "x"},
                    {"_id": 11, "ff": "a", "val": 2, "from_local": "x"},
                ],
            },
            {
                "_id": 2,
                "lf": "b",
                "extra": "y",
                "joined": [{"_id": 12, "ff": "b", "val": 3, "from_local": "y"}],
            },
        ],
        msg="$lookup concise should expose let variables to the pipeline alongside "
        "the equality match",
    ),
    LookupTestCase(
        "per_doc_variation_distinct_let_values",
        foreign_docs=[
            {"_id": 10, "ff": "A", "type": "A", "val": 1},
            {"_id": 11, "ff": "B", "type": "B", "val": 2},
            {"_id": 12, "ff": "B", "type": "B", "val": 3},
        ],
        docs=[
            {"_id": 1, "lf": "A", "cat": "A"},
            {"_id": 2, "lf": "B", "cat": "B"},
            {"_id": 3, "lf": "C", "cat": "C"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "A",
                "cat": "A",
                "joined": [{"_id": 10, "ff": "A", "type": "A", "val": 1}],
            },
            {
                "_id": 2,
                "lf": "B",
                "cat": "B",
                "joined": [
                    {"_id": 11, "ff": "B", "type": "B", "val": 2},
                    {"_id": 12, "ff": "B", "type": "B", "val": 3},
                ],
            },
            {"_id": 3, "lf": "C", "cat": "C", "joined": []},
        ],
        msg=(
            "$lookup concise correlated join should produce different results per outer"
            " document based on each document's let variable value"
        ),
    ),
    LookupTestCase(
        "per_doc_duplicate_let_values_same_result",
        foreign_docs=[{"_id": 10, "ff": "A", "type": "A"}],
        docs=[
            {"_id": 1, "lf": "A", "cat": "A"},
            {"_id": 2, "lf": "A", "cat": "A"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": "A", "cat": "A", "joined": [{"_id": 10, "ff": "A", "type": "A"}]},
            {"_id": 2, "lf": "A", "cat": "A", "joined": [{"_id": 10, "ff": "A", "type": "A"}]},
        ],
        msg=(
            "$lookup concise correlated join with duplicate let values should produce"
            " identical joined results for both outer documents"
        ),
    ),
    LookupTestCase(
        "let_variable_in_match_without_expr_is_literal_string",
        foreign_docs=[
            {"_id": 10, "ff": "a", "fval": "a"},
            {"_id": 11, "ff": "a", "fval": "$$local_val"},
        ],
        docs=[{"_id": 1, "lf": "a", "val": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"local_val": "$val"},
                    "pipeline": [{"$match": {"fval": "$$local_val"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "val": "a",
                "joined": [{"_id": 11, "ff": "a", "fval": "$$local_val"}],
            },
        ],
        msg=(
            "$lookup concise let variables in $match without $expr should be"
            ' treated as the literal string "$$variable"'
        ),
    ),
    LookupTestCase(
        "bare_field_resolves_against_foreign_not_outer",
        foreign_docs=[{"_id": 10, "ff": "a", "shared": "from_foreign"}],
        docs=[{"_id": 1, "lf": "a", "shared": "from_local"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "pipeline": [{"$addFields": {"resolved": "$shared"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "shared": "from_local",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "shared": "from_foreign",
                        "resolved": "from_foreign",
                    }
                ],
            },
        ],
        msg=(
            "$lookup concise bare $field references in the sub-pipeline should"
            " resolve against the foreign collection, not the outer"
        ),
    ),
    LookupTestCase(
        "variable_names_are_case_sensitive",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "val": "user_val"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"root": "$val"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "user_root": "$$root",
                                "sys_ROOT": "$$ROOT",
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
                "val": "user_val",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "user_root": "user_val",
                        "sys_ROOT": {"_id": 10, "ff": "a"},
                    }
                ],
            },
        ],
        msg=(
            "$lookup concise let variable names should be case-sensitive"
            " so $$root and $$ROOT coexist independently"
        ),
    ),
    LookupTestCase(
        "let_variable_values_any_bson_type",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[
            {
                "_id": 1,
                "lf": "a",
                "v_double": 3.14,
                "v_int32": 42,
                "v_int64": Int64(2**40),
                "v_decimal": Decimal128("123.456"),
                "v_string": "hello",
                "v_bool": True,
                "v_null": None,
                "v_date": datetime.datetime(2024, 6, 15, 12, 0, 0),
                "v_oid": ObjectId("507f1f77bcf86cd799439011"),
                "v_binary": Binary(b"\x00\x01\x02", 0),
                "v_regex": Regex("^abc", "i"),
                "v_code": Code("function() {}"),
                "v_timestamp": Timestamp(1000, 1),
                "v_minkey": MinKey(),
                "v_maxkey": MaxKey(),
                "v_arr": [1, "two", 3],
                "v_doc": {"nested": "doc"},
            }
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {
                        "vdouble": "$v_double",
                        "vint32": "$v_int32",
                        "vint64": "$v_int64",
                        "vdecimal": "$v_decimal",
                        "vstring": "$v_string",
                        "vbool": "$v_bool",
                        "vnull": "$v_null",
                        "vdate": "$v_date",
                        "void": "$v_oid",
                        "vbinary": "$v_binary",
                        "vregex": "$v_regex",
                        "vcode": "$v_code",
                        "vtimestamp": "$v_timestamp",
                        "vminkey": "$v_minkey",
                        "vmaxkey": "$v_maxkey",
                        "varr": "$v_arr",
                        "vdoc": "$v_doc",
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "rdouble": "$$vdouble",
                                "rint32": "$$vint32",
                                "rint64": "$$vint64",
                                "rdecimal": "$$vdecimal",
                                "rstring": "$$vstring",
                                "rbool": "$$vbool",
                                "rnull": "$$vnull",
                                "rdate": "$$vdate",
                                "roid": "$$void",
                                "rbinary": "$$vbinary",
                                "rregex": "$$vregex",
                                "rcode": "$$vcode",
                                "rtimestamp": "$$vtimestamp",
                                "rminkey": "$$vminkey",
                                "rmaxkey": "$$vmaxkey",
                                "rarr": "$$varr",
                                "rdoc": "$$vdoc",
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
                "v_double": 3.14,
                "v_int32": 42,
                "v_int64": Int64(2**40),
                "v_decimal": Decimal128("123.456"),
                "v_string": "hello",
                "v_bool": True,
                "v_null": None,
                "v_date": datetime.datetime(2024, 6, 15, 12, 0, 0, tzinfo=datetime.timezone.utc),
                "v_oid": ObjectId("507f1f77bcf86cd799439011"),
                "v_binary": b"\x00\x01\x02",
                "v_regex": Regex("^abc", 2),
                "v_code": Code("function() {}"),
                "v_timestamp": Timestamp(1000, 1),
                "v_minkey": MinKey(),
                "v_maxkey": MaxKey(),
                "v_arr": [1, "two", 3],
                "v_doc": {"nested": "doc"},
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "rdouble": 3.14,
                        "rint32": 42,
                        "rint64": Int64(2**40),
                        "rdecimal": Decimal128("123.456"),
                        "rstring": "hello",
                        "rbool": True,
                        "rnull": None,
                        "rdate": datetime.datetime(
                            2024, 6, 15, 12, 0, 0, tzinfo=datetime.timezone.utc
                        ),
                        "roid": ObjectId("507f1f77bcf86cd799439011"),
                        "rbinary": b"\x00\x01\x02",
                        "rregex": Regex("^abc", 2),
                        "rcode": Code("function() {}"),
                        "rtimestamp": Timestamp(1000, 1),
                        "rminkey": MinKey(),
                        "rmaxkey": MaxKey(),
                        "rarr": [1, "two", 3],
                        "rdoc": {"nested": "doc"},
                    }
                ],
            },
        ],
        msg=(
            "$lookup concise let variable values should carry every BSON type through"
            " to the sub-pipeline unchanged"
        ),
    ),
    LookupTestCase(
        "let_variable_values_can_be_expressions",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "a": 5, "b": 3, "s1": "hello", "s2": " world"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {
                        "sum_val": {"$add": ["$a", "$b"]},
                        "cat_val": {"$concat": ["$s1", "$s2"]},
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "computed_sum": "$$sum_val",
                                "computed_cat": "$$cat_val",
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
                "a": 5,
                "b": 3,
                "s1": "hello",
                "s2": " world",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "computed_sum": 8,
                        "computed_cat": "hello world",
                    }
                ],
            },
        ],
        msg=(
            "$lookup concise let variable values should support aggregation"
            " expressions evaluated against the input document"
        ),
    ),
    LookupTestCase(
        "let_variable_values_can_be_constants",
        foreign_docs=[
            {"_id": 10, "ff": "a", "n": 7, "s": "hello"},
            {"_id": 11, "ff": "a", "n": 7, "s": "other"},
        ],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"num": 7, "word": "hello"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$n", "$$num"]},
                                        {"$eq": ["$s", "$$word"]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": [{"_id": 10, "ff": "a", "n": 7, "s": "hello"}]}],
        msg=(
            "$lookup concise let variable values should support literal constants,"
            " including a string treated as a literal rather than a field path"
        ),
    ),
    LookupTestCase(
        "let_constant_values_all_bson_types",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {
                        "k_double": 3.14,
                        "k_int32": 42,
                        "k_int64": Int64(2**40),
                        "k_decimal": Decimal128("123.456"),
                        "k_string": "hello",
                        "k_bool": True,
                        "k_null": None,
                        "k_date": datetime.datetime(2024, 6, 15, 12, 0, 0),
                        "k_oid": ObjectId("507f1f77bcf86cd799439011"),
                        "k_binary": Binary(b"\x00\x01\x02", 0),
                        "k_regex": Regex("^abc", "i"),
                        "k_code": Code("function() {}"),
                        "k_timestamp": Timestamp(1000, 1),
                        "k_minkey": MinKey(),
                        "k_maxkey": MaxKey(),
                        "k_arr": [1, "two", 3],
                        "k_doc": {"nested": "doc"},
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "r_double": "$$k_double",
                                "r_int32": "$$k_int32",
                                "r_int64": "$$k_int64",
                                "r_decimal": "$$k_decimal",
                                "r_string": "$$k_string",
                                "r_bool": "$$k_bool",
                                "r_null": "$$k_null",
                                "r_date": "$$k_date",
                                "r_oid": "$$k_oid",
                                "r_binary": "$$k_binary",
                                "r_regex": "$$k_regex",
                                "r_code": "$$k_code",
                                "r_timestamp": "$$k_timestamp",
                                "r_minkey": "$$k_minkey",
                                "r_maxkey": "$$k_maxkey",
                                "r_arr": "$$k_arr",
                                "r_doc": "$$k_doc",
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
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "r_double": 3.14,
                        "r_int32": 42,
                        "r_int64": Int64(2**40),
                        "r_decimal": Decimal128("123.456"),
                        "r_string": "hello",
                        "r_bool": True,
                        "r_null": None,
                        "r_date": datetime.datetime(
                            2024, 6, 15, 12, 0, 0, tzinfo=datetime.timezone.utc
                        ),
                        "r_oid": ObjectId("507f1f77bcf86cd799439011"),
                        "r_binary": b"\x00\x01\x02",
                        "r_regex": Regex("^abc", 2),
                        "r_code": Code("function() {}"),
                        "r_timestamp": Timestamp(1000, 1),
                        "r_minkey": MinKey(),
                        "r_maxkey": MaxKey(),
                        "r_arr": [1, "two", 3],
                        "r_doc": {"nested": "doc"},
                    }
                ],
            }
        ],
        msg=(
            "$lookup concise let variable values should support literal constants of every"
            " BSON type, carried through to the sub-pipeline unchanged"
        ),
    ),
    LookupTestCase(
        "let_mixed_forms_constant_field_expression",
        foreign_docs=[
            {"_id": 10, "ff": "a", "c": 5, "f": 7, "e": 3},
            {"_id": 11, "ff": "a", "c": 5, "f": 8, "e": 3},
        ],
        docs=[{"_id": 1, "lf": "a", "x": 7}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {
                        "konst": 5,
                        "from_field": "$x",
                        "expr": {"$add": [1, 2]},
                    },
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$c", "$$konst"]},
                                        {"$eq": ["$f", "$$from_field"]},
                                        {"$eq": ["$e", "$$expr"]},
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
                "lf": "a",
                "x": 7,
                "joined": [{"_id": 10, "ff": "a", "c": 5, "f": 7, "e": 3}],
            },
        ],
        msg=(
            "$lookup concise should resolve a let document that mixes constant, field"
            " reference, and expression values in a single binding"
        ),
    ),
    LookupTestCase(
        "let_null_behaves_like_omitting_let",
        foreign_docs=[{"_id": 10, "ff": "a", "val": "x"}, {"_id": 11, "ff": "a", "val": "y"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": None,
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [
                    {"_id": 10, "ff": "a", "val": "x"},
                    {"_id": 11, "ff": "a", "val": "y"},
                ],
            },
        ],
        msg="$lookup concise with let: null should behave identically to omitting let",
    ),
    LookupTestCase(
        "let_empty_doc_behaves_like_omitting_let",
        foreign_docs=[{"_id": 10, "ff": "a", "val": "x"}, {"_id": 11, "ff": "a", "val": "y"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {},
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [
                    {"_id": 10, "ff": "a", "val": "x"},
                    {"_id": 11, "ff": "a", "val": "y"},
                ],
            },
        ],
        msg="$lookup concise with let: {} should behave identically to omitting let",
    ),
    LookupTestCase(
        "let_variable_bound_to_missing_field",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"missing_var": "$nonexistent"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "ifnull_result": {"$ifNull": ["$$missing_var", "fallback"]},
                                "type_result": {"$type": "$$missing_var"},
                                "direct_val": "$$missing_var",
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
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "ifnull_result": "fallback",
                        "type_result": "missing",
                    }
                ],
            },
        ],
        msg=(
            "$lookup concise let variable bound to a missing field should"
            " resolve to type missing with $ifNull treating it as null"
            " and $addFields omitting the field entirely"
        ),
    ),
    LookupTestCase(
        "system_variables_as_let_values",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "val": "x"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {
                        "root_doc": "$$ROOT",
                        "current_doc": "$$CURRENT",
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "root": "$$root_doc",
                                "current": "$$current_doc",
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
                "val": "x",
                "joined": [
                    {
                        "_id": 10,
                        "ff": "a",
                        "root": {"_id": 1, "lf": "a", "val": "x"},
                        "current": {"_id": 1, "lf": "a", "val": "x"},
                    }
                ],
            },
        ],
        msg="$lookup concise should accept system variables $$ROOT and $$CURRENT as let values",
    ),
    LookupTestCase(
        "now_system_variable_as_let_value",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"now_val": "$$NOW"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "now_type": {"$type": "$$now_val"},
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lf": "a", "joined": [{"_id": 10, "ff": "a", "now_type": "date"}]}],
        msg=(
            "$lookup concise should accept system variable $$NOW as a let value "
            "producing a date type"
        ),
    ),
    LookupTestCase(
        "remove_as_let_value_treats_variable_as_missing",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"removed": "$$REMOVE"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "removed_val": "$$removed",
                                "type_result": {"$type": "$$removed"},
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
                "joined": [{"_id": 10, "ff": "a", "type_result": "missing"}],
            },
        ],
        msg=(
            "$lookup concise with $$REMOVE as a let value should cause the"
            " variable to be treated as a removed/missing field"
        ),
    ),
]

# Property [Concise Let Expression Error]: expression evaluation errors in let
# values propagate as errors.
LOOKUP_CONCISE_LET_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_expression_error_propagates",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"bad": {"$divide": [1, 0]}},
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$lookup concise should propagate expression evaluation errors in let values",
    ),
    LookupTestCase(
        "let_expr_error_for_some_docs_fails_all",
        foreign_docs=[{"_id": 10, "ff": "a"}],
        docs=[{"_id": 1, "lf": "a", "x": 10}, {"_id": 2, "lf": "a", "x": 0}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"inv": {"$divide": [1, "$x"]}},
                    "pipeline": [{"$addFields": {"val": "$$inv"}}],
                    "as": "joined",
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$lookup concise should fail the entire aggregate when a let expression errors "
        "for any single outer document",
    ),
]

LOOKUP_CONCISE_CORRELATED_SUBQUERY_TESTS: list[LookupTestCase] = (
    LOOKUP_CONCISE_COMPOSITION_TESTS
    + LOOKUP_CONCISE_LET_BEHAVIOR_TESTS
    + LOOKUP_CONCISE_LET_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CONCISE_CORRELATED_SUBQUERY_TESTS))
def test_lookup_concise_correlated_subquery(collection, test_case: LookupTestCase):
    """Test $lookup concise correlated subquery."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
