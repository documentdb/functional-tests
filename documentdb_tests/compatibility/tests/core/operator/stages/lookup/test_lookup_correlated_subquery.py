"""Tests for $lookup correlated subquery — let variable behavior."""

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

# Property [Correlated Subquery]: let variables expose local document
# fields to the sub-pipeline for use in correlated filtering.
LOOKUP_CORRELATED_SUBQUERY_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_exposes_local_fields_via_variable",
        docs=[
            {"_id": 1, "val": "a"},
            {"_id": 2, "val": "b"},
        ],
        foreign_docs=[
            {"_id": 10, "fval": "a"},
            {"_id": 11, "fval": "b"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"local_val": "$val"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$fval", "$$local_val"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": "a",
                "joined": [{"_id": 10, "fval": "a"}],
            },
            {
                "_id": 2,
                "val": "b",
                "joined": [{"_id": 11, "fval": "b"}],
            },
        ],
        msg=(
            "$lookup let variables should expose local document fields"
            " to the sub-pipeline via $$variableName syntax"
        ),
    ),
    LookupTestCase(
        "per_doc_variation_distinct_let_values",
        foreign_docs=[
            {"_id": 10, "type": "A", "val": 1},
            {"_id": 11, "type": "B", "val": 2},
            {"_id": 12, "type": "B", "val": 3},
        ],
        docs=[
            {"_id": 1, "cat": "A"},
            {"_id": 2, "cat": "B"},
            {"_id": 3, "cat": "C"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A", "val": 1}]},
            {
                "_id": 2,
                "cat": "B",
                "joined": [
                    {"_id": 11, "type": "B", "val": 2},
                    {"_id": 12, "type": "B", "val": 3},
                ],
            },
            {"_id": 3, "cat": "C", "joined": []},
        ],
        msg=(
            "$lookup correlated join should produce different results per outer"
            " document based on each document's let variable value"
        ),
    ),
    LookupTestCase(
        "per_doc_duplicate_let_values_same_result",
        foreign_docs=[{"_id": 10, "type": "A"}],
        docs=[
            {"_id": 1, "cat": "A"},
            {"_id": 2, "cat": "A"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$c"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A"}]},
            {"_id": 2, "cat": "A", "joined": [{"_id": 10, "type": "A"}]},
        ],
        msg=(
            "$lookup correlated join with duplicate let values should produce"
            " identical joined results for both outer documents"
        ),
    ),
    LookupTestCase(
        "let_variable_in_match_without_expr_is_literal_string",
        docs=[{"_id": 1, "val": "a"}],
        foreign_docs=[
            {"_id": 10, "fval": "a"},
            {"_id": 11, "fval": "$$local_val"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"local_val": "$val"},
                    "pipeline": [{"$match": {"fval": "$$local_val"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": "a",
                "joined": [{"_id": 11, "fval": "$$local_val"}],
            },
        ],
        msg=(
            "$lookup let variables in $match without $expr should be"
            ' treated as the literal string "$$variable"'
        ),
    ),
    LookupTestCase(
        "let_variable_accessible_in_non_match_stages_without_expr",
        docs=[{"_id": 1, "val": "hello"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"local_val": "$val"},
                    "pipeline": [{"$addFields": {"from_outer": "$$local_val"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": "hello",
                "joined": [{"_id": 10, "from_outer": "hello"}],
            },
        ],
        msg=(
            "$lookup let variables should be accessible directly"
            " in non-$match sub-pipeline stages without $expr"
        ),
    ),
    LookupTestCase(
        "bare_field_resolves_against_foreign_not_outer",
        docs=[{"_id": 1, "shared": "from_local"}],
        foreign_docs=[{"_id": 10, "shared": "from_foreign"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$addFields": {"resolved": "$shared"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "shared": "from_local",
                "joined": [
                    {
                        "_id": 10,
                        "shared": "from_foreign",
                        "resolved": "from_foreign",
                    }
                ],
            },
        ],
        msg=(
            "$lookup bare $field references in the sub-pipeline should"
            " resolve against the foreign collection, not the outer"
        ),
    ),
    LookupTestCase(
        "let_variables_propagate_to_nested_lookup",
        docs=[{"_id": 1, "val": "a"}],
        foreign_docs=[{"_id": 10, "fval": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"outer_val": "$val"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "pipeline": [{"$addFields": {"from_outer": "$$outer_val"}}],
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
                "val": "a",
                "joined": [
                    {
                        "_id": 10,
                        "fval": "a",
                        "nested": [
                            {
                                "_id": 10,
                                "fval": "a",
                                "from_outer": "a",
                            }
                        ],
                    }
                ],
            },
        ],
        msg=(
            "$lookup let variables should propagate to nested"
            " $lookup stages within the sub-pipeline"
        ),
    ),
    LookupTestCase(
        "inner_let_shadows_outer_variable",
        docs=[{"_id": 1, "val": "outer"}],
        foreign_docs=[{"_id": 10, "fval": "inner"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$val"},
                    "pipeline": [
                        {
                            "$lookup": {
                                "from": FOREIGN,
                                "let": {"x": "$fval"},
                                "pipeline": [{"$addFields": {"x_val": "$$x"}}],
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
                "val": "outer",
                "joined": [
                    {
                        "_id": 10,
                        "fval": "inner",
                        "nested": [
                            {
                                "_id": 10,
                                "fval": "inner",
                                "x_val": "inner",
                            }
                        ],
                    }
                ],
            },
        ],
        msg="$lookup inner let variable should shadow an outer variable of the same name",
    ),
    LookupTestCase(
        "variable_names_are_case_sensitive",
        docs=[{"_id": 1, "val": "user_val"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "val": "user_val",
                "joined": [
                    {
                        "_id": 10,
                        "user_root": "user_val",
                        "sys_ROOT": {"_id": 10},
                    }
                ],
            },
        ],
        msg=(
            "$lookup let variable names should be case-sensitive"
            " so $$root and $$ROOT coexist independently"
        ),
    ),
    LookupTestCase(
        "let_variable_values_any_bson_type",
        docs=[
            {
                "_id": 1,
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
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
            "$lookup let variable values should carry every BSON type through"
            " to the sub-pipeline unchanged"
        ),
    ),
    LookupTestCase(
        "let_variable_values_can_be_expressions",
        docs=[{"_id": 1, "a": 5, "b": 3, "s1": "hello", "s2": " world"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "a": 5,
                "b": 3,
                "s1": "hello",
                "s2": " world",
                "joined": [
                    {
                        "_id": 10,
                        "computed_sum": 8,
                        "computed_cat": "hello world",
                    }
                ],
            },
        ],
        msg=(
            "$lookup let variable values should support aggregation"
            " expressions evaluated against the input document"
        ),
    ),
    LookupTestCase(
        "let_variable_values_can_be_constants",
        foreign_docs=[
            {"_id": 10, "n": 7, "s": "hello"},
            {"_id": 11, "n": 7, "s": "other"},
        ],
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
        expected=[{"_id": 1, "joined": [{"_id": 10, "n": 7, "s": "hello"}]}],
        msg=(
            "$lookup let variable values should support literal constants,"
            " including a string treated as a literal rather than a field path"
        ),
    ),
    LookupTestCase(
        "let_mixed_forms_constant_field_expression",
        foreign_docs=[
            {"_id": 10, "c": 5, "f": 7, "e": 3},
            {"_id": 11, "c": 5, "f": 8, "e": 3},
        ],
        docs=[{"_id": 1, "x": 7}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
            {"_id": 1, "x": 7, "joined": [{"_id": 10, "c": 5, "f": 7, "e": 3}]},
        ],
        msg=(
            "$lookup should resolve a let document that mixes constant, field"
            " reference, and expression values in a single binding"
        ),
    ),
    LookupTestCase(
        "let_null_behaves_like_omitting_let",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10, "val": "a"}, {"_id": 11, "val": "b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": None,
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [
                    {"_id": 10, "val": "a"},
                    {"_id": 11, "val": "b"},
                ],
            },
        ],
        msg="$lookup with let: null should behave identically to omitting let",
    ),
    LookupTestCase(
        "let_empty_doc_behaves_like_omitting_let",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10, "val": "a"}, {"_id": 11, "val": "b"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {},
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [
                    {"_id": 10, "val": "a"},
                    {"_id": 11, "val": "b"},
                ],
            },
        ],
        msg="$lookup with let: {} should behave identically to omitting let",
    ),
    LookupTestCase(
        "let_variable_bound_to_missing_field",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "joined": [
                    {
                        "_id": 10,
                        "ifnull_result": "fallback",
                        "type_result": "missing",
                    }
                ],
            },
        ],
        msg=(
            "$lookup let variable bound to a missing field should"
            " resolve to type missing with $ifNull treating it as null"
            " and $addFields omitting the field entirely"
        ),
    ),
    LookupTestCase(
        "system_variables_as_let_values",
        docs=[{"_id": 1, "val": "a"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "val": "a",
                "joined": [
                    {
                        "_id": 10,
                        "root": {"_id": 1, "val": "a"},
                        "current": {"_id": 1, "val": "a"},
                    }
                ],
            },
        ],
        msg="$lookup should accept system variables $$ROOT and $$CURRENT as let values",
    ),
    LookupTestCase(
        "now_system_variable_as_let_value",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
        expected=[{"_id": 1, "joined": [{"_id": 10, "now_type": "date"}]}],
        msg="$lookup should accept system variable $$NOW as a let value producing a date type",
    ),
    LookupTestCase(
        "remove_as_let_value_treats_variable_as_missing",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
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
                "joined": [{"_id": 10, "type_result": "missing"}],
            },
        ],
        msg=(
            "$lookup with $$REMOVE as a let value should cause the"
            " variable to be treated as a removed/missing field"
        ),
    ),
]

# Property [Correlated Subquery Expression Error]: expression evaluation
# errors in let values propagate as errors.
LOOKUP_CORRELATED_SUBQUERY_ERROR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_expression_error_propagates",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"bad": {"$divide": [1, 0]}},
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$lookup should propagate expression evaluation errors in let values",
    ),
]

LOOKUP_CORRELATED_SUBQUERY_ALL_TESTS: list[LookupTestCase] = (
    LOOKUP_CORRELATED_SUBQUERY_TESTS + LOOKUP_CORRELATED_SUBQUERY_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CORRELATED_SUBQUERY_ALL_TESTS))
def test_lookup_correlated_subquery(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
