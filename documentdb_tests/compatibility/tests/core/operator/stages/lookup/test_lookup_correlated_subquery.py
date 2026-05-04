"""Tests for $lookup correlated subquery — let variable behavior."""

from __future__ import annotations

import pytest

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
                "v_int": 42,
                "v_str": "hello",
                "v_bool": True,
                "v_double": 3.14,
                "v_null": None,
                "v_arr": [1, 2],
                "v_doc": {"n": 1},
            }
        ],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {
                        "vi": "$v_int",
                        "vs": "$v_str",
                        "vb": "$v_bool",
                        "vd": "$v_double",
                        "vn": "$v_null",
                        "va": "$v_arr",
                        "vdoc": "$v_doc",
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "ri": "$$vi",
                                "rs": "$$vs",
                                "rb": "$$vb",
                                "rd": "$$vd",
                                "rn": "$$vn",
                                "ra": "$$va",
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
                "v_int": 42,
                "v_str": "hello",
                "v_bool": True,
                "v_double": 3.14,
                "v_null": None,
                "v_arr": [1, 2],
                "v_doc": {"n": 1},
                "joined": [
                    {
                        "_id": 10,
                        "ri": 42,
                        "rs": "hello",
                        "rb": True,
                        "rd": 3.14,
                        "rn": None,
                        "ra": [1, 2],
                        "rdoc": {"n": 1},
                    }
                ],
            },
        ],
        msg=(
            "$lookup let variable values should support any BSON type"
            " including int, string, bool, double, null, array, and"
            " document"
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
